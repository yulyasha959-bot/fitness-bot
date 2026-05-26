
# Telegram Fitness Tracker Bot

## Features
- Daily nutrition block tracking
- Step counter
- Weekly body measurements
- Weekly analytics summary

## Stack
- Python
- python-telegram-bot
- Google Sheets
- APScheduler

## Setup

### 1. Create Telegram Bot
Open BotFather:
https://telegram.me/BotFather

Commands:
- /newbot
- choose name
- copy token

### 2. Install dependencies

```bash
pip install python-telegram-bot gspread oauth2client pandas matplotlib apscheduler
```

### 3. Create Google Sheet

Create sheets:
- nutrition
- steps
- measurements
- weight

### 4. Add credentials.json
Place your Google API credentials file into the project folder.

### 5. Add bot token
Open bot.py and replace:
YOUR_BOT_TOKEN

### 6. Run
```bash
python bot.py
```

## Planned commands

/start
/food
/steps
/weight
/measurements
/report

## Nutrition blocks

Protein:
- chicken
- fish
- eggs
- beef

Carbs:
- potatoes
- rice
- pasta
- bread

Vegetables:
- salad
- cucumbers
- tomatoes

Fats:
- olive oil
- nuts
- cheese

Fruits:
- berries
- apples
- bananas
