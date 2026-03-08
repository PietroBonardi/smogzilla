from telegram import Update
from telegram.ext import ContextTypes
from utils.cities import CITIES
from storage import remove_subscription


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    if not context.args:
        await update.message.reply_text(
            "!! missing argument\n$ /unsubscribe <city>"
        )
        return

    city_key = context.args[0].lower()
    if city_key not in CITIES:
        await update.message.reply_text(
            f"!! city '{city_key}' not found\n$ /cities for full list"
        )
        return

    chat_id = update.message.chat_id
    city    = CITIES[city_key]
    removed = remove_subscription(chat_id, city_key)

    if not removed:
        await update.message.reply_text(
            f"!! not subscribed to {city.name.upper()}"
        )
        return

    await update.message.reply_text(
        f"> unsubscribed from {city.name.upper()}"
    )