import asyncio
import logging
from typing import List

from telegram import Update
from telegram.ext import ContextTypes

from config import WAQI_API_TOKEN
from formatter import format_message
from scrapers.base import BaseScraper
from scrapers.sensor_community import SensorCommunityScraper
from scrapers.types import SensorReading
from scrapers.waqi import WaqiScraper
from utils.city_data import CITIES

logger = logging.getLogger(__name__)


def _build_scrapers() -> List[BaseScraper]:
    """Instantiate available scrapers. Skip WAQI when its token is missing."""
    scrapers: List[BaseScraper] = [SensorCommunityScraper()]
    if WAQI_API_TOKEN:
        scrapers.append(WaqiScraper(token=WAQI_API_TOKEN))
    return scrapers


async def _fetch_all(lat: float, lng: float) -> List[SensorReading]:
    """Fan out to every scraper in parallel and merge their readings."""
    results = await asyncio.gather(*(s.fetch_by_area(lat, lng) for s in _build_scrapers()))
    return [reading for source_results in results for reading in source_results]


async def air(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    if not context.args:
        await update.message.reply_text(
            "```\n!! missing argument\n$ /air <city>\n```",
            parse_mode="Markdown"
        )
        return

    city_key = context.args[0].lower()
    if city_key not in CITIES:
        await update.message.reply_text(
            f"```\n!! city '{city_key}' not found\n$ /cities for full list\n```",
            parse_mode="Markdown"
        )
        return

    city = CITIES[city_key]
    await update.message.reply_text(
        f"```\n>> scanning {city.name.upper()}...\n```",
        parse_mode="Markdown"
    )

    data = await _fetch_all(city.lat, city.lng)
    if not data:
        await update.message.reply_text(
            f"```\n!! no sensor data received for {city.name.upper()}\n```",
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text(format_message(city_key, data), parse_mode="Markdown")
