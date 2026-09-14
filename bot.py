import os, json, tempfile
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes,
)
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, time
import gspread

TOKEN = "8921021336:AAF2agrxCts1tXaRl8p1FWojyjEaXWZrBQ0"
MINI_APP_URL = "https://yulyasha959-bot.github.io/fitness-bot/"

# IF settings: window 12:00-20:00
IF_START = time(12, 0)
IF_END   = time(20, 0)

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

# ── Reminder jobs ──────────────────────────────────────────────────────────────
async def remind_open_window(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text="🟢 Вікно їжі відкрите! (12:00–20:00)\n\nЧас їсти 🍽 Починай з білка і овочів — так довше залишишся ситою!",
        reply_markup=get_inline_kb(),
    )

async def remind_close_window(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text="🔴 Вікно їжі закривається за 30 хвилин! (20:00)\n\nЯкщо хочеш щось з'їсти — зроби це зараз 😊",
    )

async def remind_water(context: ContextTypes.DEFAULT_TYPE):
    msgs = [
        "💧 Час випити склянку води!",
        "💧 Не забувай про воду — це важливо для схуднення!",
        "💧 Склянка води зараз — і ти молодець! 🌟",
        "💧 Вода допомагає контролювати апетит. Пий!",
    ]
    import random
    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text=random.choice(msgs),
    )

async def remind_meal_1(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text="🍽 Час першого прийому їжі (12:00)\n\nПорада: почни з білка (яйця, сир, курка) + овочі — так ти довше будеш ситою і не переїси потім!",
        reply_markup=get_inline_kb(),
    )

async def remind_meal_2(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text="🍽 Час другого прийому їжі (15:00)\n\nЦе середина твого вікна — ідеальний час для основної їжі дня! 💪",
        reply_markup=get_inline_kb(),
    )

async def remind_meal_3(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text="🍽 Час третього прийому їжі (18:00)\n\nОстанній прийом їжі — обери щось легке: білок + овочі. Уникай вуглеводів ввечері 🌙",
        reply_markup=get_inline_kb(),
    )

async def remind_evening(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text="🌙 Вікно їжі закрито! Голодування розпочато.\n\nМожна пити воду, чай, каву без цукру ☕\nДо відкриття вікна: 12:00 завтра 💪",
    )

def setup_reminders(context, chat_id):
    # Remove old jobs
    for job in context.job_queue.get_jobs_by_name(f"r_{chat_id}"):
        job.schedule_removal()

    jobs = [
        (time(12, 0),  remind_open_window,  "відкриття вікна"),
        (time(12, 0),  remind_meal_1,        "прийом 1"),
        (time(14, 30), remind_water,          "вода 1"),
        (time(15, 0),  remind_meal_2,         "прийом 2"),
        (time(17, 0),  remind_water,          "вода 2"),
        (time(18, 0),  remind_meal_3,         "прийом 3"),
        (time(19, 30), remind_close_window,   "закриття вікна"),
        (time(20, 0),  remind_evening,        "вікно закрито"),
        (time(21, 30), remind_water,          "вода 3"),
    ]

    for t, callback, name in jobs:
        context.job_queue.run_daily(
            callback,
            time=t,
            chat_id=chat_id,
            name=f"r_{chat_id}",
        )

# ── Handlers ───────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    setup_reminders(context, chat_id)
    await update.message.reply_text(
        "Привіт ✨ Натисни кнопку щоб відкрити додаток 👇\n\n"
        "⏰ Нагадування налаштовано:\n"
        "• 12:00 — відкриття вікна їжі\n"
        "• 12:00, 15:00, 18:00 — прийоми їжі\n"
        "• 14:30, 17:00, 21:30 — вода 💧\n"
        "• 19:30 — попередження про закриття\n"
        "• 20:00 — вікно закрито",
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
