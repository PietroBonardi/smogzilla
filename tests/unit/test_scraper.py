"""Unit tests for scrapers/sensor_community.py pure helpers."""

import httpx
import pytest

import scrapers.sensor_community as sc
from scrapers.sensor_community import (
    POLLUTANT_MAP,
    _is_transient_error,
    _parse_sensors,
    _reduce,
    _safe_float,
)
from tests.conftest import json_response, make_record

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------- _safe_float


@pytest.mark.parametrize(
    "raw, expected",
    [("12.5", 12.5), (7, 7.0), ("0", 0.0), ("-3.2", -3.2)],
)
def test_safe_float_valid(raw, expected):
    assert _safe_float(raw) == expected


@pytest.mark.parametrize("raw", ["not-a-number", None, "", "NaN?"])
def test_safe_float_invalid(raw):
    assert _safe_float(raw) is None


# ---------------------------------------------------------------- constants


def test_pollutant_map():
    assert POLLUTANT_MAP == {"P1": "pm10", "P2": "pm2.5"}


# ---------------------------------------------------------------- _reduce


def test_reduce_empty_returns_none():
    assert _reduce([]) is None


def test_reduce_last_picks_newest_timestamp_not_insertion_order():
    samples = [("2026-09-04 22:40:00", 99.0), ("2026-09-04 22:50:00", 12.0)]
    assert _reduce(samples) == 12.0


def test_reduce_median(monkeypatch):
    monkeypatch.setattr(sc, "REDUCE_STRATEGY", "median")
    assert _reduce([("t1", 10.0), ("t2", 12.0), ("t3", 99.0)]) == 12.0


def test_reduce_mean(monkeypatch):
    monkeypatch.setattr(sc, "REDUCE_STRATEGY", "mean")
    assert _reduce([("t1", 10.0), ("t2", 20.0)]) == 15.0


def test_reduce_unknown_strategy_falls_back_to_last(monkeypatch):
    monkeypatch.setattr(sc, "REDUCE_STRATEGY", "bogus")
    assert _reduce([("t1", 1.0), ("t2", 2.0)]) == 2.0


# ---------------------------------------------------------------- _parse_sensors


def test_parse_sensors_last_strategy_with_pollutant_fallback():
    records = [
        make_record(1, "2026-09-04 22:45:00", [("P1", "10.0"), ("P2", "7.0")]),
        make_record(1, "2026-09-04 22:50:00", [("P1", "12.0")]),
        make_record(1, "2026-09-04 22:40:00", [("P1", "99.0"), ("P2", "5.0")]),
    ]
    assert _parse_sensors(records) == [
        {
            "sensor_id": 1,
            "pm2.5": 7.0,
            "pm10": 12.0,
            "timestamp": "2026-09-04 22:50:00",
        }
    ]


def test_parse_sensors_groups_multiple_records_per_sensor():
    records = [
        make_record(1, "t1", [("P1", "10.0")]),
        make_record(2, "t1", [("P1", "20.0")]),
        make_record(1, "t2", [("P1", "11.0")]),
    ]
    by_id = {r["sensor_id"]: r for r in _parse_sensors(records)}
    assert set(by_id) == {1, 2}
    assert by_id[1]["pm10"] == 11.0
    assert by_id[1]["timestamp"] == "t2"
    assert by_id[2]["pm10"] == 20.0


def test_parse_sensors_skips_records_without_sensor_id():
    records = [
        {"timestamp": "t", "sensordatavalues": [{"value_type": "P1", "value": "1.0"}]},
        make_record(1, "t", [("P1", "2.0")]),
    ]
    assert [r["sensor_id"] for r in _parse_sensors(records)] == [1]


def test_parse_sensors_drops_sensors_without_valid_pm_values():
    records = [
        make_record(1, "t", [("P1", "oops"), ("P2", None)]),
        make_record(2, "t", [("P1", "3.0")]),
    ]
    assert [r["sensor_id"] for r in _parse_sensors(records)] == [2]


def test_parse_sensors_ignores_non_pm_value_types():
    records = [make_record(1, "t", [("temperature", "21.0"), ("humidity", "50")])]
    assert _parse_sensors(records) == []


def test_parse_sensors_empty_input():
    assert _parse_sensors([]) == []


# ---------------------------------------------------------------- _is_transient_error


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
