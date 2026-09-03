"""Async scraper for the sensor.community airrohr API (https://sensor.community)."""

import logging
from statistics import median
from typing import Any, Dict, List, Optional, Tuple, TypedDict

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from config import SENSOR_RADIUS

logger = logging.getLogger(__name__)

BASE_URL = "https://data.sensor.community/airrohr/v1"
HEADERS = {"User-Agent": "smogzilla-bot/1.0"}
TIMEOUT = 10.0

# sensordatavalue type -> pollutant key
POLLUTANT_MAP = {"P1": "pm10", "P2": "pm2.5"}

# How to combine multiple records of the same sensor: "last" | "median" | "mean"
REDUCE_STRATEGY = "last"


# "pm2.5" contains a dot, so the functional TypedDict syntax is required
SensorReading = TypedDict(
    "SensorReading",
    {
        "sensor_id": int,
        "timestamp": str,
        "pm2.5": Optional[float],
        "pm10": Optional[float],
    },
)


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

        if response.status_code >= 400:
            logger.warning("sensor.community returned %s for %s", response.status_code, url)
            return []

        try:
            return response.json()
        except ValueError:
            logger.error("sensor.community returned invalid JSON for %s", url)
            return []


async def fetch_by_area(
    lat: float,
    lng: float,
    radius_km: Optional[int] = None,
) -> List[SensorReading]:
    """Fetch readings from all sensors within radius_km of (lat, lng)."""
    if radius_km is None:
        radius_km = SENSOR_RADIUS
    url = f"{BASE_URL}/filter/area={lat},{lng},{radius_km}"
    return _parse_sensors(await _fetch(url))


async def fetch_by_sensor(sensor_id: int) -> List[SensorReading]:
    """Fetch readings from a single sensor by ID."""
    url = f"{BASE_URL}/sensor/{sensor_id}/"
    return _parse_sensors(await _fetch(url))