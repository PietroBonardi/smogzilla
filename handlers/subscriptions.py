from telegram import Update
from telegram.ext import ContextTypes
from utils.cities import CITIES
from storage import get_subscriptions_by_chat


async def subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    chat_id = update.message.chat_id
    subs    = get_subscriptions_by_chat(chat_id)

    if not subs:
        await update.message.reply_text(
            "!! no active subscriptions\n"
            "$ /subscribe <city_name> to add one"
        )
        return

    city_list = "\n".join(
        f"  {CITIES[key].name.ljust(20)} {CITIES[key].region}"
        for key in subs
        if key in CITIES
    )

    await update.message.reply_text(
        f"> active subscriptions\n\n"
        f"{city_list}\n\n\n"
        f"$ /unsubscribe <city_name> to remove"
    )