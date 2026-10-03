"""Integration tests: WaqiScraper fetch pipeline over a mocked HTTP transport.

These exercise _fetch + _feed_by_geo + fetch_by_area together, mocking only
the network boundary (httpx transport).
"""

from datetime import datetime, timedelta, timezone

import pytest

import scrapers.waqi as w
from scrapers.waqi import WaqiScraper
from tests.conftest import json_response, patch_httpx_transport

pytestmark = pytest.mark.integration


def _fresh_iso(hours_ago: float = 0.5) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()


@pytest.fixture
def scraper(no_retry_wait):  # noqa: ARG001 - reuse the no-wait fixture
    s = WaqiScraper(token="TEST-TOKEN")
    # make tenacity retries instant on this instance
    from tenacity import wait_none

    s._fetch_with_retry.retry.wait = wait_none()
    return s


async def test_fetch_by_area_parses_payload(monkeypatch, scraper):
    def handler(request):
        assert request.url.path == "/feed/geo:45.4654;9.1859/"
        assert request.url.params["token"] == "TEST-TOKEN"
        assert request.headers["User-Agent"] == "smogzilla-bot/1.0"
        return json_response(200, {
            "status": "ok",
            "data": {
                "idx": 9357,
                "iaqi": {"pm25": {"v": 50}, "pm10": {"v": 100}},
                "time": {"iso": _fresh_iso()},
            },
        })

    patch_httpx_transport(monkeypatch, w, handler)
    result = await scraper.fetch_by_area(45.4654, 9.1859)

    assert len(result) == 1
    r = result[0]
    assert r["sensor_id"] == 9357
    assert r["pm2.5"] == 12.0     # IAQI 50 -> 12.0 µg/m³
    assert r["pm10"] == 154.0     # IAQI 100 -> 154 µg/m³
    assert r["source"] == "waqi"


async def test_fetch_by_area_returns_empty_when_waqi_not_ok(monkeypatch, scraper):
    def handler(request):
        return json_response(200, {"status": "error", "data": "invalid station"})

    patch_httpx_transport(monkeypatch, w, handler)
    assert await scraper.fetch_by_area(1.0, 2.0) == []


async def test_fetch_by_area_returns_empty_on_stale_station(monkeypatch, scraper):
    stale = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()

    def handler(request):
        return json_response(200, {
            "status": "ok",
            "data": {
                "idx": 999,
                "iaqi": {"pm25": {"v": 50}},
                "time": {"iso": stale},
            },
        })

    patch_httpx_transport(monkeypatch, w, handler)
    assert await scraper.fetch_by_area(1.0, 2.0) == []


async def test_fetch_returns_empty_on_4xx_without_retrying(monkeypatch, scraper):
    calls = {"count": 0}

    def handler(request):
        calls["count"] += 1
        return json_response(404, {})

    patch_httpx_transport(monkeypatch, w, handler)
    assert await scraper.fetch_by_area(1.0, 2.0) == []
    assert calls["count"] == 1


async def test_fetch_retries_5xx_then_succeeds(monkeypatch, scraper):
    calls = {"count": 0}

    def handler(request):
        calls["count"] += 1
        if calls["count"] < 3:
            return json_response(500, {})
        return json_response(200, {
            "status": "ok",
            "data": {
                "idx": 1,
                "iaqi": {"pm10": {"v": 50}},
                "time": {"iso": _fresh_iso()},
            },
        })

    patch_httpx_transport(monkeypatch, w, handler)
    readings = await scraper.fetch_by_area(1.0, 2.0)
    assert calls["count"] == 3
    assert readings[0]["pm10"] == 54.0  # IAQI 50 -> 54 µg/m³


async def test_fetch_gives_up_after_exhausted_retries(monkeypatch, scraper):
    calls = {"count": 0}

    def handler(request):
        calls["count"] += 1
        return json_response(503, {})

    patch_httpx_transport(monkeypatch, w, handler)
    assert await scraper.fetch_by_area(1.0, 2.0) == []
    assert calls["count"] == 3


async def test_fetch_returns_empty_on_invalid_json(monkeypatch, scraper):
    import httpx

    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, content=b"<html>oops</html>")
    )
    original_client = httpx.AsyncClient

    def factory(**kwargs):
        return original_client(**{**kwargs, "transport": transport})

    monkeypatch.setattr(w.httpx, "AsyncClient", factory)
    assert await scraper.fetch_by_area(1.0, 2.0) == []


async def test_fetch_by_area_ignores_radius_km(monkeypatch, scraper):
    """radius_km is accepted for BaseScraper parity but unused by feed/geo:."""
    iso = _fresh_iso()

    def handler(request):
        return json_response(200, {
            "status": "ok",
            "data": {
                "idx": 1,
                "iaqi": {"pm25": {"v": 10}},
                "time": {"iso": iso},
            },
        })

    patch_httpx_transport(monkeypatch, w, handler)
    result_default = await scraper.fetch_by_area(45.46, 9.18)
    result_with_radius = await scraper.fetch_by_area(45.46, 9.18, radius_km=50)

    # both should hit the same endpoint and return the same single-reading list
    assert len(result_default) == 1
    assert len(result_with_radius) == 1
    assert result_default == result_with_radius
