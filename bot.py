import telebot
import gspread
import json
import os
from google.oauth2.service_account import Credentials

# --- НАЛАШТУВАННЯ ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")
GOOGLE_CREDS = json.loads(os.environ.get("GOOGLE_CREDS"))

# --- ПІДКЛЮЧЕННЯ ---
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(GOOGLE_CREDS, scopes=scopes)
gc = gspread.authorize(creds)
sh = gc.open_by_key(SPREADSHEET_ID)
ws = sh.sheet1

bot = telebot.TeleBot(BOT_TOKEN)

def find_row(sku, size):
    data = ws.get_all_values()
    for i, row in enumerate(data):
        if len(row) >= 4 and row[2].strip().lower() == sku.strip().lower() and row[3].strip() == size.strip():
            return i + 1, row
    return None, None

@bot.message_handler(commands=['start'])
def start(msg):
    bot.send_message(msg.chat.id,
        "👟 Matviy Store Bot\n\n"
        "/check артикул розмір — перевірити наявність\n"
        "/remove артикул розмір кількість — списати товар\n"
        "/add артикул розмір кількість — додати товар\n"
        "/list — показати всі товари в наявності"
    )

@bot.message_handler(commands=['check'])
def check(msg):
    parts = msg.text.split()
    if len(parts) < 3:
        bot.send_message(msg.chat.id, "❌ Формат: /check артикул розмір\nПриклад: /check AM90-001 42")
        return
    sku, size = parts[1], parts[2]
    row_num, row = find_row(sku, size)
    if row:
        name = row[1]
        qty = row[5] if len(row) > 5 else "?"
        available = row[7] if len(row) > 7 else "?"
        bot.send_message(msg.chat.id, f"✅ {name}\nАртикул: {sku} | Розмір: {size}\nКількість: {qty} | В наявності: {available}")
    else:
        bot.send_message(msg.chat.id, f"❌ Товар {sku} розмір {size} не знайдено")

@bot.message_handler(commands=['remove'])
def remove(msg):
    parts = msg.text.split()
    if len(parts) < 4:
        bot.send_message(msg.chat.id, "❌ Формат: /remove артикул розмір кількість\nПриклад: /remove AM90-001 42 1")
        return
    sku, size = parts[1], parts[2]
    try:
        qty = int(parts[3])
    except:
        bot.send_message(msg.chat.id, "❌ Кількість має бути числом")
        return
    row_num, row = find_row(sku, size)
    if row_num:
        current = int(row[5]) if row[5].isdigit() else 0
        if qty > current:
            bot.send_message(msg.chat.id, f"❌ Недостатньо товару. В наявності: {current}")
            return
        new_qty = current - qty
        ws.update_cell(row_num, 6, new_qty)
        bot.send_message(msg.chat.id, f"✅ Списано {qty} шт.\n{row[1]} | {sku} | розмір {size}\nЗалишок: {new_qty}")
    else:
        bot.send_message(msg.chat.id, f"❌ Товар {sku} розмір {size} не знайдено")

@bot.message_handler(commands=['add'])
def add(msg):
    parts = msg.text.split()
    if len(parts) < 4:
        bot.send_message(msg.chat.id, "❌ Формат: /add артикул розмір кількість\nПриклад: /add AM90-001 42 3")
        return
    sku, size = parts[1], parts[2]
    try:
        qty = int(parts[3])
    except:
        bot.send_message(msg.chat.id, "❌ Кількість має бути числом")
        return
    row_num, row = find_row(sku, size)
    if row_num:
        current = int(row[5]) if row[5].isdigit() else 0
        new_qty = current + qty
        ws.update_cell(row_num, 6, new_qty)
        bot.send_message(msg.chat.id, f"✅ Додано {qty} шт.\n{row[1]} | {sku} | розмір {size}\nНовий залишок: {new_qty}")
    else:
        bot.send_message(msg.chat.id, f"❌ Товар {sku} розмір {size} не знайдено")

@bot.message_handler(commands=['list'])
def list_items(msg):
    data = ws.get_all_values()
    if len(data) <= 1:
        bot.send_message(msg.chat.id, "📦 Таблиця порожня")
        return
    text = "📦 Наявність:\n\n"
    for row in data[1:]:
        if len(row) >= 8 and row[7].isdigit() and int(row[7]) > 0:
            text += f"• {row[1]} | {row[2]} | р.{row[3]} — {row[7]} шт.\n"
    bot.send_message(msg.chat.id, text if len(text) > 20 else "📦 Немає товарів в наявності")

print("🤖 Бот запущено...")
bot.polling(none_stop=True)
