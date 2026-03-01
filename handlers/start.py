from telegram import Update
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:  # ← guard
        return

    await update.message.reply_text(
        "*SMOGZILLA*\n"
        "```\n"
        "Real-time air quality for Italian cities.\n\n"
        "$ /cities: list available cities\n"
        "$ /air <city_name>: get air quality report\n\n"
        "data: sensor.community\n"
        "```",
        parse_mode="Markdown"
    )