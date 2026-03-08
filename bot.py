import logging
from telegram.ext import Application, CommandHandler
from config import TELEGRAM_BOT_TOKEN
from storage import init_db
from scheduler import build_scheduler
from handlers.start import start
from handlers.air import air
from handlers.cities import cities
from handlers.subscribe import subscribe
from handlers.unsubscribe import unsubscribe
from handlers.subscriptions import subscriptions

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


async def error_handler(update: object, context) -> None:
    logging.error(f"[error] {context.error}")


async def post_init(app: Application) -> None:
    scheduler = build_scheduler(app)
    scheduler.start()
    logging.info("[scheduler] started")


def main():
    init_db()

    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start",         start))
    app.add_handler(CommandHandler("air",           air))
    app.add_handler(CommandHandler("cities",        cities))
    app.add_handler(CommandHandler("subscribe",     subscribe))
    app.add_handler(CommandHandler("unsubscribe",   unsubscribe))
    app.add_handler(CommandHandler("subscriptions", subscriptions))
    app.add_error_handler(error_handler)
    logging.info("==========================")
    logging.info("Smogzilla bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()