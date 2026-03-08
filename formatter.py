from utils.cities import CITIES
from config import PM25_THRESHOLD, PM10_THRESHOLD
import pandas as pd


def _pm25_status(value: float) -> str:
    if value <= 15: return "⣀⣀⣀ [OK]"
    if value <= 25: return "⣤⣀⣀ [WARN]"
    if value <= 50: return "⣤⣶⣀ [HIGH]"
    return "⣤⣶⣿ [CRITICAL]"
 

def _pm10_status(value: float) -> str:
    if value <= 20: return "⣀⣀⣀ [OK]"
    if value <= 45: return "⣤⣀⣀ [WARN]"
    if value <= 90: return "⣤⣶⣀ [HIGH]"
    return "⣤⣶⣿ [CRITICAL]  "


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


def format_message(city_key: str, data: dict) -> str:
    city      = CITIES[city_key]
    agg_data  = aggregate_readings(data)

    avg_pm25  = round(agg_data["pm25"].mean(), 2)
    avg_pm10  = round(agg_data["pm10"].mean(), 2)
    latest    = agg_data["timestamp"].max()
    n_sensors = len(agg_data)

    # alerts
    alerts = []
    if avg_pm25 > PM25_THRESHOLD:
        ratio = round(avg_pm25 / PM25_THRESHOLD, 1)
        alerts.append(f"   PM2.5 is {ratio}x the safe limit")
    if avg_pm10 > PM10_THRESHOLD:
        ratio = round(avg_pm10 / PM10_THRESHOLD, 1)
        alerts.append(f"   PM10  is {ratio}x the safe limit")

    alert_count = len(alerts)
    alert_text  = (
        f"!! {alert_count} ALERT{'S' if alert_count > 1 else ''}\n" + "\n".join(alerts)
        if alerts else
        "ALL CLEAR"
    )

    return (
        f"*SMOGZILLA // {city.name.upper()}*\n"
        f"```\n"
        f"{latest}\n"
        f"sensors  {n_sensors} active\n\n"
        f"PM2.5    {avg_pm25:.1f} µg/m³    {_pm25_status(avg_pm25)}\n"
        f"PM10     {avg_pm10:.1f} µg/m³    {_pm10_status(avg_pm10)}\n\n"
        f"{alert_text}\n"
        f"```"
    )
