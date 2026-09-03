"""Formats air quality reports for Telegram messages."""

from typing import Callable, Dict, List, Optional

import pandas as pd

from config import DELTA, PM10_THRESHOLD, PM25_THRESHOLD
from utils.cities import CITIES


def _pm25_status(value: float) -> str:
    if value <= 15: return "⣀⣀⣀ [OK]"
    if value <= 25: return "⣤⣀⣀ [WARN]"
    if value <= 50: return "⣤⣶⣀ [HIGH]"
    return "⣤⣶⣿ [CRITICAL]"


def _pm10_status(value: float) -> str:
    if value <= 20: return "⣀⣀⣀ [OK]"
    if value <= 45: return "⣤⣀⣀ [WARN]"
    if value <= 90: return "⣤⣶⣀ [HIGH]"
    return "⣤⣶⣿ [CRITICAL]"


def aggregate_readings(data: dict) -> pd.DataFrame:
    df = pd.DataFrame(data)
    return (
        df.groupby("sensor_id")
        .agg(
            pm25=("pm2.5", "mean"),
            pm10=("pm10", "mean"),
            timestamp=("timestamp", "last"),
        )
        .round(2)
        .reset_index()
    )


def _stats(values: pd.Series) -> Dict[str, Optional[float]]:
    """City-wide summary statistics, robust to NaN readings."""
    clean = values.dropna()
    if clean.empty:
        return {"mean": None, "median": None, "p95": None, "max": None}
    return {
        "mean": float(clean.mean()),
        "median": float(clean.median()),
        "p95": float(clean.quantile(0.95)),
        "max": float(clean.max()),
    }


def _value_line(label: str, stats: Dict[str, Optional[float]], status_fn: Callable[[float], str]) -> str:
    mean = stats["mean"]
    value = f"{mean:.1f}" if mean is not None else "--"
    bar = status_fn(mean) if mean is not None else "⣀⣀⣀ [--]"
    return f"{label}    {value} µg/m³    {bar}"


def _stats_line(stats: Dict[str, Optional[float]]) -> str:
    if stats["median"] is None:
        return "         no data"
    return (
        f"         med {stats['median']:.1f}"
        f"  p95 {stats['p95']:.1f}"
        f"  max {stats['max']:.1f}"
    )


def _pollutant_alerts(label: str, stats: Dict[str, Optional[float]], threshold: float) -> List[str]:
    mean = stats["mean"]
    if mean is None:
        return []
    if mean > threshold + DELTA:
        ratio = round(mean / threshold, 1)
        return [f"   {label} is {ratio:.1f}x the safe limit"]
    p95 = stats["p95"]
    if p95 is not None and p95 > threshold + DELTA:
        ratio = round(p95 / threshold, 1)
        return [f"   {label.strip()} hotspot: p95 is {ratio:.1f}x the safe limit"]
    return []


def format_message(city_key: str, data: dict) -> str:
    city = CITIES[city_key]
    agg_data = aggregate_readings(data)

    latest = agg_data["timestamp"].max()
    n_sensors = len(agg_data)

    body_lines: List[str] = []
    alerts: List[str] = []
    for label, column, threshold, status_fn in (
        ("PM2.5", "pm25", PM25_THRESHOLD, _pm25_status),
        ("PM10 ", "pm10", PM10_THRESHOLD, _pm10_status),
    ):
        stats = _stats(agg_data[column])
        body_lines.append(_value_line(label, stats, status_fn))
        body_lines.append(_stats_line(stats))
        alerts.extend(_pollutant_alerts(label, stats, threshold))

    alert_count = len(alerts)
    alert_text = (
        f"!! {alert_count} ALERT{'S' if alert_count > 1 else ''}\n" + "\n".join(alerts)
        if alerts
        else "ALL CLEAR"
    )

    body = "\n".join(body_lines)
    return (
        f"*SMOGZILLA // {city.name.upper()}*\n"
        "```\n"
        f"{latest}\n"
        f"sensors  {n_sensors} active\n\n"
        f"{body}\n\n"
        f"{alert_text}\n"
        "```"
    )