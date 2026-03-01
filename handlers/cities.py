from telegram import Update
from telegram.ext import ContextTypes
from utils.cities import CITIES


async def cities(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    city_list = "\n".join(
        f"  • {c.name} ({c.region})" 
        for c in sorted(CITIES.values(), key=lambda c: c.region)
    )
    await update.message.reply_text(
        f"🦖 *Available cities:*\n\n{city_list}\n\n"
        f"Usage: `/air <cityname>` e.g. `/air brescia`",
        parse_mode="Markdown"
    )
# ```

# The cities list is sorted by region so it reads naturally:
# ```
# - Bergamo (Lombardia)
# - Brescia (Lombardia)
# - Como (Lombardia)
# ...
# - Bologna (Emilia-Romagna)
# - Modena (Emilia-Romagna)
# ...