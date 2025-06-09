# bot.py
import os
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

app = Application.builder().token(TELEGRAM_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hello from worker bot!")

app.add_handler(CommandHandler("start", start))

if __name__ == "__main__":
    app.run_polling()
