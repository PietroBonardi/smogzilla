from telegram import Update
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:  # ← guard
        return

    await update.message.reply_text(
        "🦖🔥 *Welcome to Smogzilla!*\n\n"
        "Real-time air quality reporting for Italian cities.\n\n"
        "*$ Commands:*\n"
        "  - `/cities` — list all available cities\n"
        "  - `/air <city_name>` — get air quality for a city\n\n"
        "_Data provided by Sensor.Community_",
        parse_mode="Markdown"
    )