import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
# WHO 24h guideline thresholds (µg/m³)
PM25_THRESHOLD = float(os.getenv("PM25_THRESHOLD", 15.0))
PM10_THRESHOLD = float(os.getenv("PM10_THRESHOLD", 45.0))
DELTA=1