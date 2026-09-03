# smogzilla

Smogzilla monitors pollution so you don’t have to. Our real-time air quality tracking system aggregates data from public APIs to show you:
- Current pollution levels in your area
- Current air quality data for selected cities
- Health alerts for sensitive groups
- Comparative analysis across cities

## Features

### Telegram Bot Integration
- Real-time air quality data via Telegram bot commands (`/air`, `/cities`)
- User-subscription system for pollution alerts (`/subscribe`, `/unsubscribe`)
- Automated data refresh using background scheduler
- Persistent user data storage for subscriptions

### Core Functionality
- Aggregates air quality data from multiple public sources
- Provides location-based pollution analysis
- Maintains user-specific alert preferences
- Supports city-level comparative analysis

## Getting Started
1. Clone the repo
2. Install dependencies
3. Configure API keys in `config.py`
4. Run the bot using `python bot.py`

For detailed documentation, see [docs/README.md](docs/README.md)