from telegram import Update
from telegram.ext import ContextTypes
from scrapers.sensor_community import fetch_by_area
from formatter import format_message
from utils.cities import CITIES

async def air(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    if not context.args:
        await update.message.reply_text(
            "```\n!! missing argument\n$ /air <city_name>\n```",
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

    data = await fetch_by_area(city.lat, city.lng)
    if not data:
        await update.message.reply_text(
            f"```\n!! no sensor data received for {city.name.upper()}\n```",
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text(format_message(city_key, data), parse_mode="Markdown")