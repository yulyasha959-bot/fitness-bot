import os, json, tempfile
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes,
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

TOKEN = "8921021336:AAF2agrxCts1tXaRl8p1FWojyjEaXWZrBQ0"
MINI_APP_URL = "https://yulyasha959-bot.github.io/fitness-bot/"

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

google_creds_json = os.environ.get("GOOGLE_CREDENTIALS")
if google_creds_json:
    creds_dict = json.loads(google_creds_json)
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(creds_dict, tmp)
    tmp.close()
    creds = ServiceAccountCredentials.from_json_keyfile_name(tmp.name, scope)
else:
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)

client = gspread.authorize(creds)
spreadsheet = client.open("Fitness Tracker")

def get_inline_kb():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "🏋️ Відкрити Fitness Tracker",
            web_app=WebAppInfo(url=MINI_APP_URL)
        )
    ]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привіт ✨ Натисни кнопку щоб відкрити додаток 👇",
        reply_markup=get_inline_kb(),
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Використовуй кнопку нижче щоб відкрити додаток 👇",
        reply_markup=get_inline_kb(),
    )

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot is running...")
app.run_polling()
