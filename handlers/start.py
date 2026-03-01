from telegram import Update
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:  # ← guard
        return

    await update.message.reply_text(
        "🦖 *Welcome to Smogzilla!*\n\n"
        "I report real-time air quality for Italian cities.\n\n"
        "*> Commands:*\n"
        "  - `/air brescia` — get air quality for a city\n"
        "  - `/cities` — list all available cities\n\n"
        "_Data provided by Sensor.Community_",
        parse_mode="Markdown"
    )