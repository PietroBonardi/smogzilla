"""Shared types and helpers for air-quality scrapers."""

import logging
from datetime import datetime, timezone
from typing import Optional, TypedDict

logger = logging.getLogger(__name__)


# "pm2.5" contains a dot, so the functional TypedDict syntax is required
SensorReading = TypedDict(
    "SensorReading",
    {
        "sensor_id": int,
        "timestamp": str,
        "pm2.5": Optional[float],
        "pm10": Optional[float],
        "source": str,
    },
)


# Readings older than this are dropped by ``is_fresh``. Official EPA stations
# on WAQI report hourly, so 3 hours tolerates clock skew and small delays
# while filtering out zombie stations that stopped feeding data long ago.
MAX_AGE_HOURS = 3


def is_fresh(timestamp: str, max_age_hours: int = MAX_AGE_HOURS) -> bool:
    """Return True iff ``timestamp`` is within ``max_age_hours`` of now.

    Accepts:
      - ISO 8601 with timezone (WAQI form: "2026-10-03T13:00:00+02:00")
      - Naive "YYYY-MM-DD HH:MM:SS" / ISO without tz (sensor.community form),
        assumed to be UTC.

    Unparseable or empty timestamps are treated as stale.
    """
    if not timestamp:
        return False

    parsed: Optional[datetime] = None
    try:
        parsed = datetime.fromisoformat(timestamp)
    except ValueError:
        # sensor.community uses "%Y-%m-%d %H:%M:%S" with a space separator
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                parsed = datetime.strptime(timestamp, fmt)
                break
            except ValueError:
                continue

    if parsed is None:
        logger.debug("unparseable timestamp %r, treating as stale", timestamp)
        return False

    # Naive timestamps: assume UTC (sensor.community publishes UTC).
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    age_seconds = (datetime.now(timezone.utc) - parsed).total_seconds()
    return 0 <= age_seconds <= max_age_hours * 3600
