"""Integration tests: scraper fetch pipeline over a mocked HTTP transport.

These exercise _fetch + _parse_sensors + fetch_by_area together, mocking only
the network boundary (httpx transport).
"""

import pytest

import scrapers.sensor_community as sc
from scrapers.sensor_community import fetch_by_area
from tests.conftest import json_response, make_record, patch_httpx_transport

pytestmark = pytest.mark.integration


async def test_fetch_by_area_parses_payload(monkeypatch, no_retry_wait):
    def handler(request):
        assert request.url.path == "/airrohr/v1/filter/area=45.4654,9.1859,10"
        assert request.headers["User-Agent"] == "smogzilla-bot/1.0"
        return json_response(200, [make_record(7, "t1", [("P1", "9.0"), ("P2", "4.0")])])

    patch_httpx_transport(monkeypatch, sc, handler)
    result = await fetch_by_area(45.4654, 9.1859)
    assert result == [
        {"sensor_id": 7, "pm2.5": 4.0, "pm10": 9.0, "timestamp": "t1"}
    ]


async def test_fetch_by_area_custom_radius(monkeypatch, no_retry_wait):
    def handler(request):
        assert request.url.path == "/airrohr/v1/filter/area=1.0,2.0,25"
        return json_response(200, [])

    patch_httpx_transport(monkeypatch, sc, handler)
    assert await fetch_by_area(1.0, 2.0, radius_km=25) == []


async def test_fetch_returns_empty_on_4xx_without_retrying(monkeypatch, no_retry_wait):
    calls = {"count": 0}

    def handler(request):
        calls["count"] += 1
        return json_response(404, {})

    patch_httpx_transport(monkeypatch, sc, handler)
    assert await fetch_by_area(1.0, 2.0) == []
    assert calls["count"] == 1


async def test_fetch_retries_5xx_then_succeeds(monkeypatch, no_retry_wait):
    calls = {"count": 0}

    def handler(request):
        calls["count"] += 1
        if calls["count"] < 3:
            return json_response(500, {})
        return json_response(200, [make_record(1, "t1", [("P1", "5.0")])])

    patch_httpx_transport(monkeypatch, sc, handler)
    readings = await fetch_by_area(1.0, 2.0)
    assert calls["count"] == 3
    assert readings[0]["pm10"] == 5.0


async def test_fetch_gives_up_after_exhausted_retries(monkeypatch, no_retry_wait):
    calls = {"count": 0}

    def handler(request):
        calls["count"] += 1
        return json_response(503, {})

    patch_httpx_transport(monkeypatch, sc, handler)
    assert await fetch_by_area(1.0, 2.0) == []
    assert calls["count"] == 3


async def test_fetch_returns_empty_on_invalid_json(monkeypatch, no_retry_wait):
    import httpx

    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, content=b"<html>oops</html>")
    )
    original_client = httpx.AsyncClient

    def factory(**kwargs):
        return original_client(**{**kwargs, "transport": transport})

    monkeypatch.setattr(sc.httpx, "AsyncClient", factory)
    assert await fetch_by_area(1.0, 2.0) == []
