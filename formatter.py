from utils.cities import CITIES
import pandas as pd


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
    city = CITIES[city_key]
    agg_data = aggregate_readings(data)

    avg_pm25  = round(agg_data["pm25"].mean(), 2)
    avg_pm10  = round(agg_data["pm10"].mean(), 2)
    latest    = agg_data["timestamp"].max()
    n_sensors = len(agg_data)

    return (
        f"🦖 *Smogzilla — {city.name}*\n"
        f"📅 {latest}\n\n"
        f"*Pollutants (avg over {n_sensors} sensors):*\n"
        f"  > PM2.5: `{avg_pm25} µg/m³`\n"
        f"  > PM10:  `{avg_pm10} µg/m³`\n"
    )