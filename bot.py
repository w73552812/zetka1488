"""
Spark Dating Bot
Telegram Mini App Bot

Usage:
  BOT_TOKEN=xxx WEBAPP_URL=https://your-app.railway.app/app python bot.py
"""

import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.environ["BOT_TOKEN"]
WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://your-app.railway.app/app")

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name or "друг"

    keyboard = [[
        InlineKeyboardButton(
            "💘 Открыть Spark",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    ]]
    markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Привет, {name}! 👋\n\n"
        "✨ *Spark* — приложение для знакомств прямо в Telegram.\n\n"
        "🔥 Свайпай, ставь лайки и находи свою половинку!\n\n"
        "Нажми кнопку ниже, чтобы начать:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Как пользоваться Spark:*\n\n"
        "• *Лента* — смотри анкеты рядом\n"
        "• *Свайп* — листай карточки (вправо = ❤️, влево = ✗)\n"
        "• *Профиль* — редактируй свою анкету\n\n"
        "❤️ Если вы оба поставили лайк — это Матч!\n\n"
        "/start — открыть приложение",
        parse_mode="Markdown"
    )

async def fallback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("💘 Открыть Spark", web_app=WebAppInfo(url=WEBAPP_URL))]]
    await update.message.reply_text(
        "Нажми кнопку, чтобы открыть приложение 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback))
    print("🤖 Spark Bot запущен...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
