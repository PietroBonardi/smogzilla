"""Unit tests for scrapers/waqi.py pure helpers (no network I/O)."""

from datetime import datetime, timedelta, timezone

import httpx
import pytest

from scrapers.waqi import (
    _PM10_BREAKPOINTS,
    _PM25_BREAKPOINTS,
    WaqiScraper,
    _is_transient_error,
)
from tests.conftest import json_response

pytestmark = pytest.mark.unit


def _fresh_iso(hours_ago: float = 0.5) -> str:
    """Return an ISO-8601 timestamp hours_ago in the past (tz-aware)."""
    dt = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    return dt.isoformat()


# ------------------------------------------------------------------- __init__


def test_init_raises_on_missing_token():
    with pytest.raises(ValueError, match="WAQI_API_TOKEN"):
        WaqiScraper(token="")


def test_init_raises_on_none_token():
    with pytest.raises(ValueError, match="WAQI_API_TOKEN"):
        WaqiScraper(token=None)  # type: ignore[arg-type]


def test_init_stores_token_and_inherits_abc():
    s = WaqiScraper(token="abc123")
    assert s.source == "waqi"
    assert s._token == "abc123"


# ---------------------------------------------------------------- _safe_float


@pytest.mark.parametrize(
    "raw, expected",
    [("12.5", 12.5), (7, 7.0), ("0", 0.0), ("-3.2", -3.2), (0, 0.0)],
)
def test_safe_float_valid(raw, expected):
    assert WaqiScraper._safe_float(raw) == expected


@pytest.mark.parametrize("raw", ["not-a-number", None, "", "NaN?"])
def test_safe_float_invalid(raw):
    assert WaqiScraper._safe_float(raw) is None


# ------------------------------------------------------------------- _interp


def test_interp_below_range_returns_none():
    assert WaqiScraper._interp(-1, _PM25_BREAKPOINTS) is None


def test_interp_above_range_returns_none():
    assert WaqiScraper._interp(501, _PM25_BREAKPOINTS) is None


def test_interp_at_breakpoint_returns_exact_concentration():
    assert WaqiScraper._interp(50, _PM25_BREAKPOINTS) == 12.0
    assert WaqiScraper._interp(100, _PM25_BREAKPOINTS) == 35.4


def test_interp_mid_segment_is_linear():
    # Midpoint of (50, 12.0) - (100, 35.4) is (75, 23.7)
    assert WaqiScraper._interp(75, _PM25_BREAKPOINTS) == pytest.approx(23.7)


def test_interp_at_zero():
    assert WaqiScraper._interp(0, _PM25_BREAKPOINTS) == 0.0


def test_interp_at_top_of_scale():
    assert WaqiScraper._interp(500, _PM25_BREAKPOINTS) == 500.4
    assert WaqiScraper._interp(500, _PM10_BREAKPOINTS) == 604


# ------------------------------------------------- IAQI -> µg/m³ conversions


@pytest.mark.parametrize(
    "iaqi, expected_ugm3",
    [
        (0, 0.0),
        (50, 12.0),
        (100, 35.4),
        (150, 55.4),
        (200, 150.4),
        (300, 250.4),
        (400, 350.4),
        (500, 500.4),
    ],
)
def test_pm25_breakpoints_match_epa_standard(iaqi, expected_ugm3):
    assert WaqiScraper._iaqi_to_pm25_ugm3(iaqi) == pytest.approx(expected_ugm3)


@pytest.mark.parametrize(
    "iaqi, expected_ugm3",
    [
        (0, 0),
        (50, 54),
        (100, 154),
        (150, 254),
        (200, 354),
        (300, 424),
        (400, 504),
        (500, 604),
    ],
)
def test_pm10_breakpoints_match_epa_standard(iaqi, expected_ugm3):
    assert WaqiScraper._iaqi_to_pm10_ugm3(iaqi) == pytest.approx(expected_ugm3)


def test_iaqi_conversion_out_of_range():
    assert WaqiScraper._iaqi_to_pm25_ugm3(-1) is None
    assert WaqiScraper._iaqi_to_pm25_ugm3(501) is None


# --------------------------------------------------------------- _parse_feed


def _waqi_payload(idx=101, pm25_v=42, pm10_v=65, iso=None):
    return {
        "idx": idx,
        "iaqi": {
            "pm25": {"v": pm25_v},
            "pm10": {"v": pm10_v},
        },
        "time": {"iso": iso if iso is not None else _fresh_iso()},
    }


def test_parse_feed_full_payload():
    payload = _waqi_payload(idx=9118, pm25_v=50, pm10_v=50, iso=_fresh_iso(1))
    reading = WaqiScraper._parse_feed(payload)

    assert reading is not None
    assert reading["sensor_id"] == 9118
    assert reading["pm2.5"] == pytest.approx(12.0)
    assert reading["pm10"] == pytest.approx(54.0)
    assert reading["source"] == "waqi"
    assert reading["timestamp"] == payload["time"]["iso"]


def test_parse_feed_empty_payload_returns_none():
    assert WaqiScraper._parse_feed({}) is None


def test_parse_feed_missing_idx_returns_none():
    payload = _waqi_payload()
    del payload["idx"]
    assert WaqiScraper._parse_feed(payload) is None


def test_parse_feed_no_pm_data_returns_none():
    payload = {
        "idx": 1,
        "iaqi": {"o3": {"v": 25}},
        "time": {"iso": _fresh_iso()},
    }
    assert WaqiScraper._parse_feed(payload) is None


def test_parse_feed_pm_only_pm25():
    payload = {
        "idx": 1,
        "iaqi": {"pm25": {"v": 50}},
        "time": {"iso": _fresh_iso()},
    }
    reading = WaqiScraper._parse_feed(payload)
    assert reading is not None
    assert reading["pm2.5"] == pytest.approx(12.0)
    assert reading["pm10"] is None


def test_parse_feed_pm_only_pm10():
    payload = {
        "idx": 1,
        "iaqi": {"pm10": {"v": 50}},
        "time": {"iso": _fresh_iso()},
    }
    reading = WaqiScraper._parse_feed(payload)
    assert reading is not None
    assert reading["pm2.5"] is None
    assert reading["pm10"] == pytest.approx(54.0)


def test_parse_feed_invalid_iaqi_values_are_dropped():
    payload = {
        "idx": 1,
        "iaqi": {"pm25": {"v": "not-a-number"}, "pm10": None},
        "time": {"iso": _fresh_iso()},
    }
    # pm25 unparsable, pm10 not a dict -> both None -> None overall
    assert WaqiScraper._parse_feed(payload) is None


def test_parse_feed_stale_timestamp_returns_none():
    stale_iso = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()
    payload = _waqi_payload(iso=stale_iso)
    assert WaqiScraper._parse_feed(payload) is None


def test_parse_feed_missing_timestamp_returns_none():
    payload = _waqi_payload()
    del payload["time"]
    assert WaqiScraper._parse_feed(payload) is None


def test_parse_feed_empty_time_iso_returns_none():
    payload = _waqi_payload()
    payload["time"] = {"iso": ""}
    assert WaqiScraper._parse_feed(payload) is None


def test_parse_feed_three_hours_old_is_fresh():
    iso = (datetime.now(timezone.utc) - timedelta(hours=2, minutes=59)).isoformat()
    payload = _waqi_payload(iso=iso)
    assert WaqiScraper._parse_feed(payload) is not None


# -------------------------------------------------------- _is_transient_error


def test_is_transient_error_for_5xx():
    exc = httpx.HTTPStatusError(
        "server error",
        request=httpx.Request("GET", "http://test"),
        response=json_response(503),
    )
    assert _is_transient_error(exc) is True


def test_is_not_transient_error_for_4xx():
    exc = httpx.HTTPStatusError(
        "client error",
        request=httpx.Request("GET", "http://test"),
        response=json_response(404),
    )
    assert _is_transient_error(exc) is False


@pytest.mark.parametrize(
    "exc",
    [httpx.ConnectError("boom"), httpx.ReadTimeout("boom")],
)
def test_is_transient_error_for_network_errors(exc):
    assert _is_transient_error(exc) is True


def test_is_not_transient_error_for_other_exceptions():
    assert _is_transient_error(ValueError("boom")) is False
