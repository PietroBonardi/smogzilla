"""Unit tests for formatter.py pure helpers and format_message."""

import pandas as pd
import pytest

from formatter import (
    _minmax_line,
    _pm10_status,
    _pm25_status,
    _pollutant_alerts,
    _stats,
    _value_line,
    aggregate_readings,
    format_message,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------- status bands


@pytest.mark.parametrize(
    "value, expected",
    [
        (0.0, "⣀⣀⣀ [OK]"),
        (15, "⣀⣀⣀ [OK]"),
        (15.1, "⣤⣀⣀ [WARN]"),
        (25, "⣤⣀⣀ [WARN]"),
        (25.1, "⣤⣶⣀ [HIGH]"),
        (50, "⣤⣶⣀ [HIGH]"),
        (50.1, "⣤⣶⣿ [CRITICAL]"),
    ],
)
def test_pm25_status_bands(value, expected):
    assert _pm25_status(value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (0.0, "⣀⣀⣀ [OK]"),
        (20, "⣀⣀⣀ [OK]"),
        (20.1, "⣤⣀⣀ [WARN]"),
        (45, "⣤⣀⣀ [WARN]"),
        (45.1, "⣤⣶⣀ [HIGH]"),
        (90, "⣤⣶⣀ [HIGH]"),
        (90.1, "⣤⣶⣿ [CRITICAL]"),
    ],
)
def test_pm10_status_bands(value, expected):
    assert _pm10_status(value) == expected


# ---------------------------------------------------------------- aggregate_readings


def test_aggregate_readings_means_duplicate_sensor_rows():
    data = [
        {"sensor_id": 1, "pm2.5": 10.0, "pm10": 20.0, "timestamp": "t1"},
        {"sensor_id": 1, "pm2.5": 20.0, "pm10": 40.0, "timestamp": "t2"},
    ]
    df = aggregate_readings(data)
    assert len(df) == 1
    row = df.iloc[0]
    assert row["pm25"] == 15.0
    assert row["pm10"] == 30.0
    assert row["timestamp"] == "t2"


# ---------------------------------------------------------------- _stats


def test_stats_empty_series_returns_all_none():
    stats = _stats(pd.Series([], dtype=float))
    assert stats == {"mean": None, "min": None, "p95": None, "max": None}


def test_stats_all_nan_returns_all_none():
    stats = _stats(pd.Series([None, None], dtype=float))
    assert stats == {"mean": None, "min": None, "p95": None, "max": None}


def test_stats_computes_mean_min_max_p95():
    stats = _stats(pd.Series([8.0, 10.0, 12.0, 20.0]))
    assert stats["mean"] == 12.5
    assert stats["min"] == 8.0
    assert stats["max"] == 20.0
    assert stats["p95"] == pytest.approx(18.8)


def test_stats_drops_nan_before_computing():
    stats = _stats(pd.Series([10.0, None, 20.0]))
    assert stats["mean"] == 15.0
    assert stats["min"] == 10.0
    assert stats["max"] == 20.0


# ---------------------------------------------------------------- _value_line


def test_value_line_renders_mean_and_status():
    stats = {"mean": 20.0, "min": 8.0, "p95": 24.0, "max": 25.0}
    line = _value_line("PM2.5", stats, _pm25_status)
    assert "20.0" in line
    assert "µg/m³" in line
    assert "[WARN]" in line


def test_value_line_no_data_uses_placeholder():
    stats = {"mean": None, "min": None, "p95": None, "max": None}
    line = _value_line("PM2.5", stats, _pm25_status)
    assert "--" in line
    assert "[--]" in line


# ---------------------------------------------------------------- _minmax_line


def test_minmax_line_renders_both_pollutants():
    stats_by_label = {
        "PM2.5": {"mean": 12.2, "min": 8.4, "p95": 18.0, "max": 21.0},
        "PM10": {"mean": 27.9, "min": 19.2, "p95": 35.0, "max": 40.3},
    }
    assert _minmax_line("min", stats_by_label) == "min  PM2.5 8.4    PM10 19.2"
    assert _minmax_line("max", stats_by_label) == "max  PM2.5 21.0    PM10 40.3"


def test_minmax_line_placeholder_for_missing_values():
    stats_by_label = {
        "PM2.5": {"mean": None, "min": None, "p95": None, "max": None},
        "PM10": {"mean": None, "min": None, "p95": None, "max": None},
    }
    assert _minmax_line("min", stats_by_label) == "min  PM2.5 --    PM10 --"


# ---------------------------------------------------------------- _pollutant_alerts


def test_alert_when_mean_exceeds_threshold():
    stats = {"mean": 30.0, "min": 25.0, "p95": 35.0, "max": 40.0}
    alerts = _pollutant_alerts("PM2.5", stats, threshold=15.0)
    assert alerts == ["   PM2.5 is 2.0x the safe limit"]


def test_alert_when_p95_exceeds_threshold_but_mean_ok():
    stats = {"mean": 12.0, "min": 5.0, "p95": 20.0, "max": 24.0}
    alerts = _pollutant_alerts("PM2.5", stats, threshold=15.0)
    assert alerts == ["   PM2.5 hotspot: p95 is 1.3x the safe limit"]


def test_no_alert_when_mean_none():
    stats = {"mean": None, "min": None, "p95": None, "max": None}
    assert _pollutant_alerts("PM2.5", stats, threshold=15.0) == []


def test_no_alert_when_below_everything():
    stats = {"mean": 5.0, "min": 3.0, "p95": 6.0, "max": 7.0}
    assert _pollutant_alerts("PM2.5", stats, threshold=15.0) == []


# ---------------------------------------------------------------- format_message


def test_format_message_contains_header_stats_and_clear():
    data = [
        {"sensor_id": 1, "pm2.5": 5.0, "pm10": 10.0, "timestamp": "t1"},
        {"sensor_id": 2, "pm2.5": 8.0, "pm10": 13.0, "timestamp": "t1"},
        {"sensor_id": 3, "pm2.5": 6.0, "pm10": 11.0, "timestamp": "t1"},
        {"sensor_id": 4, "pm2.5": 7.0, "pm10": 12.0, "timestamp": "t1"},
    ]
    message = format_message("milano", data)
    assert "*SMOGZILLA // MILANO*" in message
    assert "sensors  4 active" in message
    assert "min  PM2.5 5.0    PM10 10.0" in message
    assert "max  PM2.5 8.0    PM10 13.0" in message
    assert "ALL CLEAR" in message


def test_format_message_reports_hotspot_alert_from_p95(fake_air_data):
    message = format_message("milano", fake_air_data)
    assert "!! 1 ALERT" in message
    assert "PM2.5 hotspot" in message


def test_format_message_reports_alerts_when_mean_high():
    data = [
        {"sensor_id": 1, "pm2.5": 40.0, "pm10": 100.0, "timestamp": "t1"},
        {"sensor_id": 2, "pm2.5": 40.0, "pm10": 100.0, "timestamp": "t1"},
    ]
    message = format_message("milano", data)
    assert "!! 2 ALERTS" in message
    assert "2.7x the safe limit" in message
    assert "2.2x the safe limit" in message


def test_format_message_all_nan_does_not_crash_and_shows_placeholders():
    data = [{"sensor_id": 1, "pm2.5": None, "pm10": None, "timestamp": "t1"}]
    message = format_message("milano", data)
    assert "ALL CLEAR" in message
    assert "min  PM2.5 --    PM10 --" in message
    assert message.count("--") >= 4
