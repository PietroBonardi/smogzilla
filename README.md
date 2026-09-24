# smogzilla

Telegram bot for real-time air quality (smog) monitoring in Italian cities. Aggregates PM2.5/PM10 data from [sensor.community](https://sensor.community) and reports on demand.

## Commands

| Command | Description |
|---|---|
| `/start` | Help and usage info |
| `/air <city>` | On-demand air quality report for a city |
| `/cities` | List supported cities |

## How it works

- `scrapers/sensor_community.py` fetches readings from the sensor.community airrohr API (with retries)
- `formatter.py` aggregates readings per sensor and computes city-wide stats (mean/min/max) against WHO thresholds; p95 drives hotspot alerts

## Getting started

1. Clone the repo
2. Install dependencies: `pip install -r requirements.txt`
3. Configure `.env` (see `.env.example` below)
4. Run the bot: `python bot.py`

Required environment variables:

```
TELEGRAM_BOT_TOKEN=<your bot token>
PM25_THRESHOLD=15   # WHO PM2.5 limit (µg/m³)
PM10_THRESHOLD=45   # WHO PM10 limit (µg/m³)
SENSOR_RADIUS=10    # sensor search radius in km
```

## Testing

```
pytest
```

Data source: [sensor.community](https://sensor.community) — thanks to all citizen sensor hosts.