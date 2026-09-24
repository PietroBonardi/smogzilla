import logging
from telegram.ext import Application, CommandHandler
from config import TELEGRAM_BOT_TOKEN
from handlers.start import start
from handlers.air import air
from handlers.cities import cities

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


async def error_handler(update: object, context) -> None:
    logging.error(f"[error] {context.error}")


def main():
    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start",         start))
    app.add_handler(CommandHandler("air",           air))
    app.add_handler(CommandHandler("cities",        cities))
    app.add_error_handler(error_handler)
    logging.info("==========================")
    logging.info("Smogzilla bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()