# smogzilla

Telegram bot for real-time air quality (smog) monitoring in Italian cities. Aggregates PM2.5/PM10 data from [sensor.community](https://sensor.community) (citizen sensors) and [WAQI](https://waqi.info) (official EPA stations) and reports on demand.

## Commands

| Command | Description |
|---|---|
| `/start` | Help and usage info |
| `/air <city>` | On-demand air quality report for a city |
| `/cities` | List supported cities |

## How it works

- `scrapers/sensor_community.py` — `SensorCommunityScraper` fetches readings from the sensor.community airrohr API
- `scrapers/waqi.py` — `WaqiScraper` fetches the nearest official station from api.waqi.info (converts IAQI to µg/m³)
- Both subclass `scrapers/base.py:BaseScraper` and emit readings tagged with their source; the handler calls both in parallel and merges results
- Readings older than 3 hours are dropped (`scrapers/types.py:MAX_AGE_HOURS`)
- `formatter.py` aggregates readings per sensor and computes city-wide stats (mean/min/max) against WHO thresholds

## Getting started

1. Clone the repo
2. Create a venv: `python3 -m venv .venv && source .venv/bin/activate`
3. Install: `pip install -e .` then `pip install -r requirements.txt`
4. Configure `.env` (see `.env.example` below)
5. Run the bot: `python bot.py`

Required environment variables:

```
TELEGRAM_BOT_TOKEN=<your bot token>
WAQI_API_TOKEN=<from https://aqicn.org/data-platform/token/>   # optional, enables WAQI source
PM25_THRESHOLD=15   # WHO PM2.5 limit (µg/m³)
PM10_THRESHOLD=45   # WHO PM10 limit (µg/m³)
SENSOR_RADIUS=10    # sensor search radius in km
```

## Testing

Install dev dependencies (`pip install -r requirements-dev.txt`) then run:

```
pytest
```

The suite is layered and selectable by marker:

| Layer | Command | Scope |
|---|---|---|
| Unit | `pytest -m unit` | Pure helpers (`_parse_sensors`, `_stats`, status bands) |
| Integration | `pytest -m integration` | Handlers + scraper + formatter over a mocked HTTP transport |
| E2E | `pytest -m e2e` | Commands dispatched through the wired `Application` |

All network I/O is mocked in tests; no real calls to Telegram or the data APIs are made.

Data sources: [sensor.community](https://sensor.community) (thanks to all citizen sensor hosts) and [WAQI / aqicn.org](https://waqi.info) (official EPA stations).
