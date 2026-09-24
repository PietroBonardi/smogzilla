import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# WHO 24h guideline thresholds (µg/m³)
PM25_THRESHOLD = float(os.getenv("PM25_THRESHOLD", 15.0))
PM10_THRESHOLD = float(os.getenv("PM10_THRESHOLD", 45.0))
SENSOR_RADIUS = int(os.getenv("SENSOR_RADIUS", "10"))
DELTA=1