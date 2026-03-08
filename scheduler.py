import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram.ext import Application

from storage import get_all_subscriptions
from scrapers.sensor_community import fetch_by_area
from formatter import format_message
from utils.cities import CITIES

logger = logging.getLogger(__name__)


async def send_daily_reports(app: Application) -> None:
    """Fetch and send daily air quality reports to all subscribers."""
    subscriptions = get_all_subscriptions()

    if not subscriptions:
        logger.info("[scheduler] no subscriptions found")
        return

    logger.info(f"[scheduler] sending reports to {len(subscriptions)} subscribers")

    for chat_id, city_key in subscriptions:
        if city_key not in CITIES:
            logger.warning(f"[scheduler] unknown city '{city_key}' for chat {chat_id}")
            continue

        city = CITIES[city_key]
        try:
            data = await fetch_by_area(city.lat, city.lng)
            if not data:
                await app.bot.send_message(
                    chat_id=chat_id,
                    text=f"!! no sensor data received for {city.name.upper()}"
                )
                continue

            message = format_message(city_key, data)
            await app.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="Markdown"
            )
            logger.info(f"[scheduler] sent report for {city.name} to {chat_id}")

        except Exception as e:
            logger.error(f"[scheduler] failed to send to {chat_id}: {e}")


def build_scheduler(app: Application) -> AsyncIOScheduler:
    """Build and return the scheduler."""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        send_daily_reports,
        trigger=CronTrigger(hour=8, minute=0),  # every day at 08:00
        args=[app],
        id="daily_reports",
        name="Daily air quality reports",
        replace_existing=True,
    )
    return scheduler

from datetime import datetime, timedelta

def test_build_scheduler(app: Application) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    test_time = datetime.now() + timedelta(minutes=1)

    scheduler.add_job(
        send_daily_reports,
        trigger=CronTrigger(hour=test_time.hour, minute=test_time.minute),
        args=[app],
        id="daily_reports",
        name="Daily air quality reports",
        replace_existing=True,
    )
    return scheduler