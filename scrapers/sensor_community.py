"""Scraper for the sensor.community airrohr API (https://sensor.community).

The module-level helpers (`_fetch`, `_parse_sensors`, `_reduce`, `_safe_float`,
`_is_transient_error`, `_log_exhausted`) and constants (`POLLUTANT_MAP`,
`REDUCE_STRATEGY`, `BASE_URL`, `HEADERS`, `TIMEOUT`) implement the actual
pipeline. ``SensorCommunityScraper`` is a thin ``BaseScraper`` adapter around
them, and the module-level ``fetch_by_area`` is preserved as a backwards-compat
shim delegating to a default scraper instance.
"""

import logging
from statistics import median
from typing import Any, Dict, List, Optional, Tuple

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from config import SENSOR_RADIUS
from scrapers.base import BaseScraper
from scrapers.types import SensorReading, is_fresh

logger = logging.getLogger(__name__)

BASE_URL = "https://data.sensor.community/airrohr/v1"
HEADERS = {"User-Agent": "smogzilla-bot/1.0"}
TIMEOUT = 10.0

# sensordatavalue type -> pollutant key
POLLUTANT_MAP = {"P1": "pm10", "P2": "pm2.5"}

# How to combine multiple records of the same sensor: "last" | "median" | "mean"
REDUCE_STRATEGY = "last"


def _safe_float(raw: Any) -> Optional[float]:
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _reduce(samples: List[Tuple[str, float]]) -> Optional[float]:
    """Combine multiple measurements of one pollutant from a single sensor."""
    if not samples:
        return None
    if REDUCE_STRATEGY == "median":
        return median(value for _, value in samples)
    if REDUCE_STRATEGY == "mean":
        return sum(value for _, value in samples) / len(samples)

    # "last": newest sample wins, falling back to older samples for
    # pollutants the newest record does not report
    ordered = sorted(samples, key=lambda sample: sample[0], reverse=True)
    return ordered[0][1]


def _parse_sensors(records: List[Dict[str, Any]]) -> List[SensorReading]:
    """Flatten nested sensordatavalues into one reduced row per sensor."""
    samples: Dict[int, Dict[str, List[Tuple[str, float]]]] = {}
    timestamps: Dict[int, str] = {}

    for record in records:
        sensor_id = record.get("sensor", {}).get("id")
        if sensor_id is None:
            continue

        timestamp = record.get("timestamp", "")
        if sensor_id not in timestamps or timestamp > timestamps[sensor_id]:
            timestamps[sensor_id] = timestamp

        sensor_samples = samples.setdefault(
            sensor_id, {"pm2.5": [], "pm10": []}
        )
        for value in record.get("sensordatavalues", []):
            key = POLLUTANT_MAP.get(value.get("value_type"))
            parsed = _safe_float(value.get("value"))
            if key and parsed is not None:
                sensor_samples[key].append((timestamp, parsed))

    readings: List[SensorReading] = []
    for sensor_id, sensor_samples in samples.items():
        pm25 = _reduce(sensor_samples["pm2.5"])
        pm10 = _reduce(sensor_samples["pm10"])
        if pm25 is None and pm10 is None:
            continue

        readings.append(
            {
                "sensor_id": sensor_id,
                "pm2.5": pm25,
                "pm10": pm10,
                "timestamp": timestamps[sensor_id],
                "source": "sensor.community",
            }
        )

    return readings


def _is_transient_error(exc: BaseException) -> bool:
    """Retry only network-level failures and 5xx responses."""
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500
    return isinstance(exc, httpx.TransportError)


def _log_exhausted(retry_state: Any) -> List[Any]:
    logger.error("sensor.community request failed after retries: %s", retry_state.outcome.exception())
    return []


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, max=10),
    retry=retry_if_exception(_is_transient_error),
    retry_error_callback=_log_exhausted,
)
async def _fetch(url: str) -> List[Dict[str, Any]]:
    """Fetch JSON records from the API, retrying transient failures."""
    async with httpx.AsyncClient(timeout=TIMEOUT, headers=HEADERS) as client:
        response = await client.get(url)

        if response.status_code >= 500:
            # raise so the tenacity decorator can retry the request
            response.raise_for_status()

        if response.status_code >= 400:
            logger.warning("sensor.community returned %s for %s", response.status_code, url)
            return []

        try:
            return response.json()
        except ValueError:
            logger.error("sensor.community returned invalid JSON for %s", url)
            return []


class SensorCommunityScraper(BaseScraper):
    """``BaseScraper`` adapter for the sensor.community airrohr API.

    Stateless: it delegates to the module-level ``_fetch`` and ``_parse_sensors``
    so existing tests that patch those names keep working unchanged.
    """

    source = "sensor.community"

    async def fetch_by_area(
        self,
        lat: float,
        lng: float,
        radius_km: Optional[int] = None,
    ) -> List[SensorReading]:
        """Fetch fresh readings from all sensors within ``radius_km`` of (lat, lng).

        Readings whose timestamps are older than ``MAX_AGE_HOURS`` are dropped.
        """
        if radius_km is None:
            radius_km = SENSOR_RADIUS
        url = f"{BASE_URL}/filter/area={lat},{lng},{radius_km}"
        readings = _parse_sensors(await _fetch(url))
        fresh = [r for r in readings if is_fresh(r["timestamp"])]
        if len(fresh) < len(readings):
            logger.info(
                "sensor.community dropped %d stale reading(s) out of %d",
                len(readings) - len(fresh),
                len(readings),
            )
        return fresh


# Backwards-compat shim: previous module-level API used by handlers and tests.
_default_scraper = SensorCommunityScraper()
fetch_by_area = _default_scraper.fetch_by_area
