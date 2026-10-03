"""Scraper for the WAQI JSON API (https://api.waqi.info, https://aqicn.org).

WAQI aggregates official government monitoring stations (in Italy: ARPA
regional agencies) and returns per-pollutant IAQI values rather than raw
concentrations. ``WaqiScraper`` converts PM2.5/PM10 IAQI back to µg/m³ via
US-EPA piecewise-linear breakpoints so readings align with the WHO thresholds
used elsewhere in the bot.

The scraper uses the ``feed/geo:{lat};{lng}/`` endpoint, which returns the
station nearest to the given coordinates. (``map/bounds/`` was tried first
but filters out stations unpredictably; ``feed/geo:`` is reliable.)
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from scrapers.base import BaseScraper
from scrapers.types import SensorReading, is_fresh

logger = logging.getLogger(__name__)


# Piecewise-linear IAQI breakpoints (iaqi_value, concentration_ugm3).
# Source: US EPA "Technical Assistance Document for the Reporting of Daily
# Air Quality – the Air Quality Index (AQI)".
_PM25_BREAKPOINTS: Tuple[Tuple[float, float], ...] = (
    (0, 0.0),
    (50, 12.0),
    (100, 35.4),
    (150, 55.4),
    (200, 150.4),
    (300, 250.4),
    (400, 350.4),
    (500, 500.4),
)

_PM10_BREAKPOINTS: Tuple[Tuple[float, float], ...] = (
    (0, 0),
    (50, 54),
    (100, 154),
    (150, 254),
    (200, 354),
    (300, 424),
    (400, 504),
    (500, 604),
)


def _is_transient_error(exc: BaseException) -> bool:
    """Retry only network-level failures and 5xx responses."""
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500
    return isinstance(exc, httpx.TransportError)


class WaqiScraper(BaseScraper):
    """``BaseScraper`` adapter for the WAQI JSON API."""

    source = "waqi"

    BASE_URL = "https://api.waqi.info"
    HEADERS = {"User-Agent": "smogzilla-bot/1.0"}
    TIMEOUT = 10.0

    def __init__(self, token: str) -> None:
        """Fail fast on missing token; callers decide whether to construct."""
        if not token:
            raise ValueError("WAQI_API_TOKEN is required to use WaqiScraper")
        self._token = token

    # ------------------------------------------------------------- public API

    async def fetch_by_area(
        self,
        lat: float,
        lng: float,
        radius_km: Optional[int] = None,
    ) -> List[SensorReading]:
        """Fetch the WAQI station nearest to ``(lat, lng)``.

        The ``radius_km`` argument is accepted for interface parity with
        other scrapers but currently ignored — the ``feed/geo:`` endpoint
        always returns the single closest station.
        """
        feed = await self._feed_by_geo(lat, lng)
        reading = self._parse_feed(feed)
        return [reading] if reading is not None else []

    # ------------------------------------------------------------ HTTP layer

    async def _fetch(self, path: str) -> Dict[str, Any]:
        """GET ``{BASE_URL}{path}`` with the token attached; retries transient errors."""
        url = f"{self.BASE_URL}{path}"
        return await self._fetch_with_retry(url, self._token)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, max=10),
        retry=retry_if_exception(_is_transient_error),
        retry_error_callback=lambda retry_state: WaqiScraper._log_exhausted(retry_state),
    )
    async def _fetch_with_retry(self, url: str, token: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.TIMEOUT, headers=self.HEADERS) as client:
            response = await client.get(url, params={"token": token})

            if response.status_code >= 500:
                # raise so the tenacity decorator can retry the request
                response.raise_for_status()

            if response.status_code >= 400:
                logger.warning("WAQI returned %s for %s", response.status_code, url)
                return {}

            try:
                return response.json()
            except ValueError:
                logger.error("WAQI returned invalid JSON for %s", url)
                return {}

    @staticmethod
    def _log_exhausted(retry_state: Any) -> Dict[str, Any]:
        logger.error("WAQI request failed after retries: %s", retry_state.outcome.exception())
        return {}

    async def _feed_by_geo(self, lat: float, lng: float) -> Dict[str, Any]:
        """Return the WAQI ``data`` payload for the station nearest to (lat, lng)."""
        payload = await self._fetch(f"/feed/geo:{lat};{lng}/")
        if payload.get("status") != "ok":
            logger.warning("WAQI feed/geo non-ok status: %s", payload.get("status"))
            return {}
        data = payload.get("data")
        return data if isinstance(data, dict) else {}

    # ------------------------------------------------------------ pure logic

    @staticmethod
    def _interp(iaqi: float, breakpoints: Tuple[Tuple[float, float], ...]) -> Optional[float]:
        """Piecewise-linear interpolation of IAQI -> concentration."""
        if iaqi < 0 or iaqi > breakpoints[-1][0]:
            return None
        for (x0, y0), (x1, y1) in zip(breakpoints, breakpoints[1:]):
            if x0 <= iaqi <= x1:
                if x1 == x0:
                    return y0
                return y0 + (iaqi - x0) * (y1 - y0) / (x1 - x0)
        return None

    @staticmethod
    def _iaqi_to_pm25_ugm3(iaqi: float) -> Optional[float]:
        return WaqiScraper._interp(iaqi, _PM25_BREAKPOINTS)

    @staticmethod
    def _iaqi_to_pm10_ugm3(iaqi: float) -> Optional[float]:
        return WaqiScraper._interp(iaqi, _PM10_BREAKPOINTS)

    @staticmethod
    def _safe_float(raw: Any) -> Optional[float]:
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_feed(data: Dict[str, Any]) -> Optional[SensorReading]:
        """Turn a WAQI ``feed/...`` ``data`` payload into a SensorReading.

        Returns None when the payload lacks a station id or any usable PM data.
        """
        if not data:
            return None

        station_idx = data.get("idx")
        if station_idx is None:
            return None

        iaqi = data.get("iaqi") or {}

        pm25_iaqi = WaqiScraper._safe_float((iaqi.get("pm25") or {}).get("v"))
        pm10_iaqi = WaqiScraper._safe_float((iaqi.get("pm10") or {}).get("v"))

        pm25 = (
            WaqiScraper._iaqi_to_pm25_ugm3(pm25_iaqi) if pm25_iaqi is not None else None
        )
        pm10 = (
            WaqiScraper._iaqi_to_pm10_ugm3(pm10_iaqi) if pm10_iaqi is not None else None
        )

        if pm25 is None and pm10 is None:
            return None

        timestamp = ((data.get("time") or {}).get("iso")) or ""
        if not is_fresh(timestamp):
            logger.info(
                "WAQI station %s dropped: stale timestamp %r",
                station_idx,
                timestamp,
            )
            return None

        return {
            "sensor_id": int(station_idx),
            "pm2.5": pm25,
            "pm10": pm10,
            "timestamp": timestamp,
            "source": WaqiScraper.source,
        }
