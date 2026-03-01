from telegram.ext import Application, CommandHandler
from config import TELEGRAM_BOT_TOKEN
from handlers.start import start
from handlers.air import air
from handlers.cities import cities

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",  start))
    app.add_handler(CommandHandler("air",    air))
    app.add_handler(CommandHandler("cities", cities))
    print("🦖 Smogzilla bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()