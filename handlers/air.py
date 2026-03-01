from telegram import Update
from telegram.ext import ContextTypes
from scrapers.sensor_community import fetch_by_area
from formatter import format_message
from utils.cities import CITIES


async def air(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:  # ← guard
        return

    if not context.args:
        await update.message.reply_text("Usage: `/air brescia`", parse_mode="Markdown")
        return

    city_key = context.args[0].lower()
    if city_key not in CITIES:
        await update.message.reply_text(f"❌ City `{city_key}` not found. Try `/cities`", parse_mode="Markdown")
        return

    city = CITIES[city_key]
    await update.message.reply_text(f"⏳ Fetching data for *{city.name}*...", parse_mode="Markdown")

    data = await fetch_by_area(city.lat, city.lng)
    if not data:
        await update.message.reply_text(f"😔 No data available for *{city.name}*.", parse_mode="Markdown")
        return

    await update.message.reply_text(format_message(city_key, data), parse_mode="Markdown")