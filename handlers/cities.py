from telegram import Update
from telegram.ext import ContextTypes
from utils.cities import CITIES


async def cities(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    city_list = "\n".join(
        f"  - {c.name} ({c.region})" 
        for c in sorted(CITIES.values(), key=lambda c: c.name)
    )
    await update.message.reply_text(
        f"*SMOGZILLA // CITIES*\n"
        f"```\n"
        f"{city_list}\n\n"
        f"$ /air <city_name>\n"
        f"```",
        parse_mode="Markdown"
    )