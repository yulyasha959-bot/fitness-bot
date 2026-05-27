import os, json, tempfile
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes,
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io

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

nutrition_sheet = spreadsheet.worksheet("nutrition")
steps_sheet = spreadsheet.worksheet("steps")

def get_or_create_sheet(name, headers):
    try:
        ws = spreadsheet.worksheet(name)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=name, rows=1000, cols=10)
        ws.append_row(headers)
    return ws

weight_sheet = get_or_create_sheet("weight", ["date", "weight_kg"])
measure_sheet = get_or_create_sheet("measures", ["date", "type", "value_cm"])

main_keyboard = ReplyKeyboardMarkup(
    [
        ["🍽 Харчування", "🚶 Кроки"],
        ["⚖️ Вага", "📏 Заміри"],
        ["📊 Сьогодні", "📈 Аналітика"],
    ],
    resize_keyboard=True,
)

food_keyboard = ReplyKeyboardMarkup(
    [
        ["🥩 Білок", "🌾 Вуглеводи"],
        ["🥗 Овочі", "🧈 Жири"],
        ["🍎 Фрукти"],
        ["⬅️ Назад"],
    ],
    resize_keyboard=True,
)

measure_keyboard = ReplyKeyboardMarkup(
    [
        ["💪 Рука", "🦵 Нога"],
        ["🫁 Груди", "🧍 Талія"],
        ["🍑 Стегна"],
        ["⬅️ Назад"],
    ],
    resize_keyboard=True,
)

analytics_keyboard = ReplyKeyboardMarkup(
    [
        ["📈 Графік ваги", "📊 Тижнева аналітика"],
        ["🔥 Стрік", "⬅️ Назад"],
    ],
    resize_keyboard=True,
)

daily_goals = {
    "🥩 Білок": 5,
    "🌾 Вуглеводи": 4,
    "🥗 Овочі": 2,
    "🧈 Жири": 2,
    "🍎 Фрукти": 2,
}

MEASURE_TYPES = {"💪 Рука", "🦵 Нога", "🫁 Груди", "🧍 Талія", "🍑 Стегна"}

def today_str():
    return str(datetime.now().date())

def build_today_nutrition():
    records = nutrition_sheet.get_all_values()
    today = today_str()
    today_records = [r[1] for r in records if len(r) > 1 and r[0] == today]
    text = "📊 Харчування сьогодні:\n\n"
    for block, goal in daily_goals.items():
        count = today_records.count(block)
        bar = "🟩" * count + "⬜" * max(0, goal - count)
        text += f"{block} {bar} {count}/{goal}\n"
    return text

def calc_streak():
    all_dates = set()
    for row in nutrition_sheet.get_all_values():
        if row and row[0]:
            all_dates.add(row[0])
    for row in steps_sheet.get_all_values():
        if row and row[0]:
            all_dates.add(row[0])
    streak = 0
    check = datetime.now().date()
    while str(check) in all_dates:
        streak += 1
        check -= timedelta(days=1)
    return streak

async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    await context.bot.send_message(
        chat_id=chat_id,
        text="⏰ Нагадування! Не забудь внести харчування та кроки сьогодні 💪",
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    current_jobs = context.job_queue.get_jobs_by_name(f"reminder_{chat_id}")
    if not current_jobs:
        context.job_queue.run_daily(
            send_reminder,
            time=datetime.strptime("20:00", "%H:%M").time(),
            chat_id=chat_id,
            name=f"reminder_{chat_id}",
        )
    inline_kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "🏋️ Відкрити Fitness Tracker",
            web_app=WebAppInfo(url=MINI_APP_URL)
        )
    ]])
    await update.message.reply_text(
        "Привіт ✨ Твій fitness tracker готовий!\n\n"
        "Натисни кнопку нижче щоб відкрити додаток 👇",
        reply_markup=inline_kb,
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    state = context.user_data.get("state")

    if text == "🍽 Харчування":
        context.user_data["state"] = None
        await update.message.reply_text("Обери блок:", reply_markup=food_keyboard)
    elif text == "🚶 Кроки":
        context.user_data["state"] = "waiting_steps"
        await update.message.reply_text("Введи кількість кроків:")
    elif text == "⚖️ Вага":
        context.user_data["state"] = "waiting_weight"
        await update.message.reply_text("Введи свою вагу (кг), наприклад: 65.5")
    elif text == "📏 Заміри":
        context.user_data["state"] = None
        await update.message.reply_text("Обери тип заміру:", reply_markup=measure_keyboard)
    elif text == "📊 Сьогодні":
        context.user_data["state"] = None
        nutrition_text = build_today_nutrition()
        steps_records = steps_sheet.get_all_values()
        today_steps = [r[1] for r in steps_records if len(r) > 1 and r[0] == today_str()]
        steps_text = f"\n🚶 Кроки: {today_steps[-1] if today_steps else '—'}"
        w_records = weight_sheet.get_all_values()
        today_w = [r[1] for r in w_records if len(r) > 1 and r[0] == today_str()]
        weight_text = f"\n⚖️ Вага: {today_w[-1] + ' кг' if today_w else '—'}"
        await update.message.reply_text(nutrition_text + steps_text + weight_text, reply_markup=main_keyboard)
    elif text == "📈 Аналітика":
        context.user_data["state"] = None
        await update.message.reply_text("Оберіть звіт:", reply_markup=analytics_keyboard)
    elif text == "📈 Графік ваги":
        await send_weight_chart(update, context)
    elif text == "📊 Тижнева аналітика":
        await send_weekly_report(update, context)
    elif text == "🔥 Стрік":
        streak = calc_streak()
        emoji = "🔥" * min(streak, 7)
        await update.message.reply_text(
            f"🔥 Твій стрік: {streak} {'день' if streak == 1 else 'днів'} поспіль!\n{emoji}"
        )
    elif text in daily_goals:
        nutrition_sheet.append_row([today_str(), text])
        progress_text = build_today_nutrition()
        await update.message.reply_text(f"✅ {text} додано\n\n{progress_text}")
    elif text in MEASURE_TYPES:
        context.user_data["state"] = "waiting_measure"
        context.user_data["measure_type"] = text
        await update.message.reply_text(f"Введи значення для «{text}» у сантиметрах, наприклад: 38")
    elif text == "⬅️ Назад":
        context.user_data["state"] = None
        await update.message.reply_text("Головне меню", reply_markup=main_keyboard)
    elif state == "waiting_steps":
        if text.isdigit():
            steps_sheet.append_row([today_str(), text])
            context.user_data["state"] = None
            await update.message.reply_text(f"🚶 Збережено: {text} кроків", reply_markup=main_keyboard)
        else:
            await update.message.reply_text("Введи ціле число кроків, наприклад: 8500")
    elif state == "waiting_weight":
        try:
            val = float(text.replace(",", "."))
            weight_sheet.append_row([today_str(), str(val)])
            context.user_data["state"] = None
            await update.message.reply_text(f"⚖️ Вага {val} кг збережена!", reply_markup=main_keyboard)
        except ValueError:
            await update.message.reply_text("Введи число, наприклад: 65.5")
    elif state == "waiting_measure":
        try:
            val = float(text.replace(",", "."))
            m_type = context.user_data.get("measure_type", "невідомо")
            measure_sheet.append_row([today_str(), m_type, str(val)])
            context.user_data["state"] = None
            await update.message.reply_text(f"📏 {m_type}: {val} см збережено!", reply_markup=main_keyboard)
        except ValueError:
            await update.message.reply_text("Введи число сантиметрів, наприклад: 38")
    else:
        await update.message.reply_text(f"Записано: {text}", reply_markup=main_keyboard)

async def send_weight_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    records = weight_sheet.get_all_values()
    rows = [(r[0], float(r[1])) for r in records if len(r) > 1 and r[0] != "date"]
    if len(rows) < 2:
        await update.message.reply_text("📈 Поки недостатньо даних (потрібно мінімум 2 записи ваги).")
        return
    dates = [r[0] for r in rows]
    weights = [r[1] for r in rows]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(dates, weights, marker="o", color="#4CAF50", linewidth=2, markersize=6)
    ax.fill_between(range(len(dates)), weights, min(weights) - 1, alpha=0.15, color="#4CAF50")
    ax.set_xticks(range(len(dates)))
    ax.set_xticklabels(dates, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("кг")
    ax.set_title("📈 Динаміка ваги")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150)
    buf.seek(0)
    plt.close(fig)
    await update.message.reply_photo(photo=buf, caption="📈 Графік твоєї ваги")

async def send_weekly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now().date()
    week_dates = {str(today - timedelta(days=i)) for i in range(7)}
    n_records = nutrition_sheet.get_all_values()
    weekly_nutrition = {k: 0 for k in daily_goals}
    for row in n_records:
        if len(row) > 1 and row[0] in week_dates and row[1] in weekly_nutrition:
            weekly_nutrition[row[1]] += 1
    s_records = steps_sheet.get_all_values()
    weekly_steps = [int(r[1]) for r in s_records if len(r) > 1 and r[0] in week_dates and r[1].isdigit()]
    avg_steps = int(sum(weekly_steps) / len(weekly_steps)) if weekly_steps else 0
    total_steps = sum(weekly_steps)
    streak = calc_streak()
    report = "📊 Тижнева аналітика (останні 7 днів)\n\n"
    report += "🍽 Харчування:\n"
    for block, count in weekly_nutrition.items():
        goal_week = daily_goals[block] * 7
        report += f"  {block}: {count}/{goal_week}\n"
    report += f"\n🚶 Кроки:\n"
    report += f"  Загалом: {total_steps:,}\n"
    report += f"  Середньо/день: {avg_steps:,}\n"
    report += f"\n🔥 Поточний стрік: {streak} днів"
    await update.message.reply_text(report, reply_markup=analytics_keyboard)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot is running...")
app.run_polling()
