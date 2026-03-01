import httpx
from datetime import datetime
BASE_URL = "https://data.sensor.community/airrohr/v1"
HEADERS = {"User-Agent": "smogzilla-bot/1.0"}


def _parse_readings(data: list[dict]) -> dict | None:
    """Extract and average PM10/PM2.5 from all readings."""
    if not data:
        return None
    
    results = {
        "sensor_id": [],
        "timestamp": [],
        "pm2.5": [],
        "pm10": [],
    }

    for read in data:
        sensor_id = read["sensor"]["id"]
        values = {v["value_type"]: float(v["value"]) for v in read["sensordatavalues"]}
        pm10 = values.get("P1")
        pm25 = values.get("P2")
        results["sensor_id"].append(sensor_id)
        results["timestamp"].append(read["timestamp"])
        results["pm2.5"].append(pm10)
        results["pm10"].append(pm25)

    return results


async def fetch_by_area(lat: float, lng: float, radius_km: int = 10) -> dict | None:
    """Fetch air quality data from all sensors in a given area."""
    url = f"{BASE_URL}/filter/area={lat},{lng},{radius_km}"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, headers=HEADERS)
        r.raise_for_status()
        data = r.json()

    return _parse_readings(data)


async def fetch_by_sensor(sensor_id: int) -> dict | None:
    """Fetch air quality data from a specific sensor by ID."""
    url = f"{BASE_URL}/sensor/{sensor_id}/"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, headers=HEADERS)
        r.raise_for_status()
        data = r.json()
    return _parse_readings(data)
