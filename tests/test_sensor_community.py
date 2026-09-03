import asyncio

import httpx
import pytest

import scrapers.sensor_community as sc
from scrapers.sensor_community import (
    POLLUTANT_MAP,
    _is_transient_error,
    _parse_sensors,
    _reduce,
    _safe_float,
    fetch_by_area,
    fetch_by_sensor,
)


def run(coro):
    return asyncio.run(coro)


def response(status_code=200, payload=None):
    return httpx.Response(
        status_code,
        json=payload if payload is not None else [],
        request=httpx.Request("GET", "http://test"),
    )


def make_record(sensor_id, timestamp, values):
    return {
        "sensor": {"id": sensor_id},
        "timestamp": timestamp,
        "sensordatavalues": [
            {"value_type": vtype, "value": value} for vtype, value in values
        ],
    }


# ---------------------------------------------------------------- _safe_float


def test_safe_float_valid():
    assert _safe_float("12.5") == 12.5
    assert _safe_float(7) == 7.0


def test_safe_float_invalid():
    assert _safe_float("not-a-number") is None
    assert _safe_float(None) is None
    assert _safe_float("") is None


# ---------------------------------------------------------------- POLLUTANT_MAP


def test_pollutant_map():
    assert POLLUTANT_MAP == {"P1": "pm10", "P2": "pm2.5"}


# ---------------------------------------------------------------- _reduce


def test_reduce_last_picks_newest_timestamp():
    samples = [("2026-09-04 22:40:00", 99.0), ("2026-09-04 22:50:00", 12.0)]
    assert _reduce(samples) == 12.0


def test_reduce_median():
    samples = [("t1", 10.0), ("t2", 12.0), ("t3", 99.0)]
    original = sc.REDUCE_STRATEGY
    sc.REDUCE_STRATEGY = "median"
    try:
        assert _reduce(samples) == 12.0
    finally:
        sc.REDUCE_STRATEGY = original


def test_reduce_mean():
    samples = [("t1", 10.0), ("t2", 20.0)]
    original = sc.REDUCE_STRATEGY
    sc.REDUCE_STRATEGY = "mean"
    try:
        assert _reduce(samples) == 15.0
    finally:
        sc.REDUCE_STRATEGY = original


def test_reduce_empty():
    assert _reduce([]) is None


def test_reduce_unknown_strategy_falls_back_to_last():
    samples = [("t1", 1.0), ("t2", 2.0)]
    original = sc.REDUCE_STRATEGY
    sc.REDUCE_STRATEGY = "bogus"
    try:
        assert _reduce(samples) == 2.0
    finally:
        sc.REDUCE_STRATEGY = original


# ---------------------------------------------------------------- _parse_sensors


def test_parse_sensors_last_strategy_with_fallback():
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
    readings = _parse_sensors(records)
    assert len(readings) == 2
    by_id = {r["sensor_id"]: r for r in readings}
    assert by_id[1]["pm10"] == 11.0
    assert by_id[1]["timestamp"] == "t2"
    assert by_id[2]["pm10"] == 20.0


def test_parse_sensors_skips_records_without_sensor_id():
    records = [
        {"timestamp": "t", "sensordatavalues": [{"value_type": "P1", "value": "1.0"}]},
        make_record(1, "t", [("P1", "2.0")]),
    ]
    readings = _parse_sensors(records)
    assert [r["sensor_id"] for r in readings] == [1]


def test_parse_sensors_drops_sensors_without_valid_pm_values():
    records = [
        make_record(1, "t", [("P1", "oops"), ("P2", None)]),
        make_record(2, "t", [("P1", "3.0")]),
    ]
    readings = _parse_sensors(records)
    assert [r["sensor_id"] for r in readings] == [2]


def test_parse_sensors_ignores_non_pm_value_types():
    records = [make_record(1, "t", [("temperature", "21.0"), ("humidity", "50")])]
    assert _parse_sensors(records) == []


def test_parse_sensors_empty_input():
    assert _parse_sensors([]) == []


# ---------------------------------------------------------------- retry logic


def test_is_transient_error_for_5xx():
    exc = httpx.HTTPStatusError(
        "server error",
        request=httpx.Request("GET", "http://test"),
        response=response(503),
    )
    assert _is_transient_error(exc) is True


def test_is_not_transient_error_for_4xx():
    exc = httpx.HTTPStatusError(
        "client error",
        request=httpx.Request("GET", "http://test"),
        response=response(404),
    )
    assert _is_transient_error(exc) is False


def test_is_transient_error_for_network_errors():
    assert _is_transient_error(httpx.ConnectError("boom")) is True
    assert _is_transient_error(httpx.ReadTimeout("boom")) is True


def test_is_not_transient_error_for_other_exceptions():
    assert _is_transient_error(ValueError("boom")) is False


# ---------------------------------------------------------------- fetch functions


def _patch_transport(monkeypatch, handler):
    transport = httpx.MockTransport(handler)
    original_client = httpx.AsyncClient

    def factory(**kwargs):
        return original_client(**{**kwargs, "transport": transport})

    monkeypatch.setattr(sc.httpx, "AsyncClient", factory)


def test_fetch_by_area_parses_payload(monkeypatch):
    def handler(request):
        assert request.url.path == "/airrohr/v1/filter/area=45.4654,9.1859,10"
        assert request.headers["User-Agent"] == "smogzilla-bot/1.0"
        return response(200, [make_record(7, "t1", [("P1", "9.0"), ("P2", "4.0")])])

    _patch_transport(monkeypatch, handler)
    readings = run(fetch_by_area(45.4654, 9.1859))
    assert readings == [
        {"sensor_id": 7, "pm2.5": 4.0, "pm10": 9.0, "timestamp": "t1"}
    ]


def test_fetch_by_area_custom_radius(monkeypatch):
    def handler(request):
        assert request.url.path == "/airrohr/v1/filter/area=1.0,2.0,25"
        return response(200, [])

    _patch_transport(monkeypatch, handler)
    assert run(fetch_by_area(1.0, 2.0, radius_km=25)) == []


def test_fetch_by_sensor(monkeypatch):
    def handler(request):
        assert request.url.path == "/airrohr/v1/sensor/42/"
        return response(200, [make_record(42, "t1", [("P2", "6.5")])])

    _patch_transport(monkeypatch, handler)
    readings = run(fetch_by_sensor(42))
    assert readings == [
        {"sensor_id": 42, "pm2.5": 6.5, "pm10": None, "timestamp": "t1"}
    ]


def test_fetch_returns_empty_on_4xx(monkeypatch):
    _patch_transport(monkeypatch, lambda request: response(404, {}))
    assert run(fetch_by_sensor(42)) == []


def test_fetch_retries_on_5xx_then_succeeds(monkeypatch):
    calls = {"count": 0}

    def handler(request):
        calls["count"] += 1
        if calls["count"] < 3:
            return response(500, {})
        return response(200, [make_record(1, "t1", [("P1", "5.0")])])

    _patch_transport(monkeypatch, handler)
    readings = run(fetch_by_sensor(1))
    assert calls["count"] == 3
    assert readings[0]["pm10"] == 5.0


def test_fetch_gives_up_after_exhausted_retries(monkeypatch):
    calls = {"count": 0}

    def handler(request):
        calls["count"] += 1
        return response(503, {})

    _patch_transport(monkeypatch, handler)
    assert run(fetch_by_sensor(1)) == []
    assert calls["count"] == 3


def test_fetch_returns_empty_on_invalid_json(monkeypatch):
    original_client = httpx.AsyncClient
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, content=b"<html>oops</html>")
    )

    def factory(**kwargs):
        return original_client(**{**kwargs, "transport": transport})

    monkeypatch.setattr(sc.httpx, "AsyncClient", factory)
    assert run(fetch_by_sensor(1)) == []


def test_fetch_does_not_retry_4xx(monkeypatch):
    calls = {"count": 0}

    def handler(request):
        calls["count"] += 1
        return response(404, {})

    _patch_transport(monkeypatch, handler)
    assert run(fetch_by_sensor(1)) == []
    assert calls["count"] == 1