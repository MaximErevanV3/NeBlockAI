import openai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import logging
import os
import json
import random
from datetime import datetime, timedelta

# Конфигурация
TELEGRAM_TOKEN = "8700124191:AAE6qSSouLjlDxPWwoFObJORMbDotsby9co"
YANDEX_API_KEY = "AQVNy7Dm-dvQRzejHvH0383oHTZhhW2fda95I558"
PROMPT_ID = "fvt621uiq1fftiu5qomu"
DAILY_LIMIT = 5
DATA_FILE = "users.json"
ADMIN_IDS = [1671403667]
START_BONUS = 50
DAILY_BONUS_MIN = 5
DAILY_BONUS_MAX = 15
REFERRAL_BONUS = 25
INVITED_BONUS = 10

SHOP_ITEMS = {
    "extra5": {"name": "+5 запросов", "price": 10},
    "extra10": {"name": "+10 запросов", "price": 18},
    "unlimited_1h": {"name": "Безлимит 1 час", "price": 30},
    "unlimited_24h": {"name": "Безлимит 24 часа", "price": 100},
    "unlimited_7d": {"name": "Безлимит 7 дней", "price": 500},
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("NeBlockAI")

client = openai.OpenAI(
    api_key=YANDEX_API_KEY,
    base_url="https://ai.api.cloud.yandex.net/v1",
    project="b1guk4h3j9t48lsjl6sq",
    timeout=30.0,
)

# База данных
def load_users():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def get_user(user_id):
    users = load_users()
    uid = str(user_id)
    
    if uid not in users:
        users[uid] = {
            "joined": datetime.now().isoformat(),
            "requests_today": 0,
            "extra_requests": 0,
            "unlimited_until": None,
            "last_request": None,
            "total_requests": 0,
            "reset_date": datetime.now().strftime("%Y-%m-%d"),
            "tokens": START_BONUS,
            "daily_bonus_claimed": None,
            "referral_code": "".join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(8)),
            "referred_by": None,
            "referrals": 0,
            "earned_tokens": 0,
        }
        save_users(users)
    
    today = datetime.now().strftime("%Y-%m-%d")
    if users[uid]["reset_date"] != today:
        users[uid]["requests_today"] = 0
        users[uid]["extra_requests"] = 0
        users[uid]["reset_date"] = today
        save_users(users)
    
    return users[uid]

def add_request(user_id):
    users = load_users()
    uid = str(user_id)
    if uid in users:
        users[uid]["requests_today"] += 1
        users[uid]["total_requests"] += 1
        users[uid]["last_request"] = datetime.now().isoformat()
        save_users(users)

def can_request(user_id):
    user = get_user(user_id)
    if user["unlimited_until"]:
        until = datetime.fromisoformat(user["unlimited_until"])
        if datetime.now() < until:
            return True
    return user["requests_today"] < (DAILY_LIMIT + user["extra_requests"])

def remaining(user_id):
    user = get_user(user_id)
    if user["unlimited_until"]:
        until = datetime.fromisoformat(user["unlimited_until"])
        if datetime.now() < until:
            return "безлимит"
    return max(0, DAILY_LIMIT + user["extra_requests"] - user["requests_today"])

def add_tokens(user_id, amount):
    users = load_users()
    uid = str(user_id)
    if uid in users:
        users[uid]["tokens"] = users[uid].get("tokens", 0) + amount
        users[uid]["earned_tokens"] = users[uid].get("earned_tokens", 0) + amount
        save_users(users)

def remove_tokens(user_id, amount):
    users = load_users()
    uid = str(user_id)
    if uid in users:
        users[uid]["tokens"] = users[uid].get("tokens", 0) - amount
        save_users(users)

def get_tokens(user_id):
    return get_user(user_id).get("tokens", 0)

# Клавиатуры
def main_menu():
    keyboard = [
        [InlineKeyboardButton("Задать вопрос", callback_data="ask"),
         InlineKeyboardButton("О боте", callback_data="about")],
        [InlineKeyboardButton("Личный кабинет", callback_data="profile"),
         InlineKeyboardButton("Магазин", callback_data="shop")],
        [InlineKeyboardButton("Заработать токены", callback_data="earn"),
         InlineKeyboardButton("FAQ", callback_data="faq")],
    ]
    return InlineKeyboardMarkup(keyboard)

def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="menu")]])

def shop_keyboard():
    keyboard = [
        [InlineKeyboardButton("+5 запросов - 10 токенов", callback_data="buy_extra5")],
        [InlineKeyboardButton("+10 запросов - 18 токенов", callback_data="buy_extra10")],
        [InlineKeyboardButton("Безлимит 1ч - 30 токенов", callback_data="buy_unlimited_1h")],
        [InlineKeyboardButton("Безлимит 24ч - 100 токенов", callback_data="buy_unlimited_24h")],
        [InlineKeyboardButton("Безлимит 7д - 500 токенов", callback_data="buy_unlimited_7d")],
        [InlineKeyboardButton("Назад", callback_data="menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

def earn_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Ежедневный бонус", callback_data="daily_bonus")],
        [InlineKeyboardButton("Реферальная ссылка", callback_data="ref_link")],
        [InlineKeyboardButton("Назад", callback_data="menu")],
    ])

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    text = f"NeBlock AI V1\n━━━━━━━━\nЛимит: {DAILY_LIMIT} запросов/день\nБаланс: {user['tokens']} токенов\n\nВыбери действие или напиши вопрос:"
    await update.message.reply_text(text, reply_markup=main_menu())

# Обработчик ВСЕХ callback_query (кнопок)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    logger.info(f"Нажата кнопка: {data} пользователем {user_id}")
    
    if data == "menu":
        user = get_user(user_id)
        text = f"NeBlock AI V1\n━━━━━━━━\nЛимит: {DAILY_LIMIT} запросов/день\nБаланс: {user['tokens']} токенов\n\nВыбери действие или напиши вопрос:"
        await query.edit_message_text(text, reply_markup=main_menu())
    
    elif data == "ask":
        await query.edit_message_text(f"Напиши свой вопрос в чат.\n\nОсталось запросов: {remaining(user_id)}", reply_markup=back_button())
    
    elif data == "about":
        await query.edit_message_text("NeBlock AI V1\n━━━━━━━━\nМодель: NeBlock AI V1\nБыстрые ответы\nПонимание контекста\nВсе языки", reply_markup=back_button())
    
    elif data == "profile":
        user = get_user(user_id)
        joined = datetime.fromisoformat(user["joined"]).strftime("%d.%m.%Y")
        last = "Никогда" if not user["last_request"] else datetime.fromisoformat(user["last_request"]).strftime("%H:%M %d.%m.%Y")
        unlimited = "Не активен"
        if user["unlimited_until"] and datetime.now() < datetime.fromisoformat(user["unlimited_until"]):
            unlimited = "Активен"
        
        text = (
            f"Личный кабинет\n━━━━━━━━\n"
            f"ID: {user_id}\n"
            f"Регистрация: {joined}\n"
            f"Баланс: {user['tokens']} токенов\n"
            f"Запросов сегодня: {user['requests_today']}/{DAILY_LIMIT + user['extra_requests']}\n"
            f"Всего запросов: {user['total_requests']}\n"
            f"Безлимит: {unlimited}\n"
            f"Рефералов: {user.get('referrals', 0)}\n"
            f"Активность: {last}"
        )
        await query.edit_message_text(text, reply_markup=back_button())
    
    elif data == "shop":
        await query.edit_message_text(
            f"Магазин\n━━━━━━━━\nБаланс: {get_tokens(user_id)} токенов\n\nВыбери товар:",
            reply_markup=shop_keyboard()
        )
    
    elif data == "earn":
        await query.edit_message_text(
            f"Заработок токенов\n━━━━━━━━\nБаланс: {get_tokens(user_id)}\n\nЕжедневный бонус: {DAILY_BONUS_MIN}-{DAILY_BONUS_MAX} токенов\nРефералы: +{REFERRAL_BONUS} тебе, +{INVITED_BONUS} другу",
            reply_markup=earn_keyboard()
        )
    
    elif data == "faq":
        text = "FAQ\n━━━━━━━━\n\nЧто такое NeBlock AI?\nИИ-бот в Telegram.\n\nПочему лимит 5 запросов?\nЧтобы не перегружать нейросеть.\n\nЧто такое NeBlock Tokens?\nВнутренняя валюта.\n\nКак заработать?\nЕжедневный бонус, рефералы.\n\nКогда сброс?\nВ 00:00 МСК.\n\nКонтекст?\nДа, бот помнит диалог."
        await query.edit_message_text(text, reply_markup=back_button())
    
    elif data == "daily_bonus":
        user = get_user(user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        
        if user.get("daily_bonus_claimed") == today:
            await query.answer("Уже получил сегодня! Приходи завтра.", show_alert=True)
        else:
            bonus = random.randint(DAILY_BONUS_MIN, DAILY_BONUS_MAX)
            users = load_users()
            users[str(user_id)]["daily_bonus_claimed"] = today
            save_users(users)
            add_tokens(user_id, bonus)
            
            await query.answer(f"+{bonus} токенов!", show_alert=True)
            await query.edit_message_text(
                f"Ежедневный бонус\n━━━━━━━━\nПолучено: +{bonus} токенов\nБаланс: {get_tokens(user_id)}\n\nПриходи завтра!",
                reply_markup=back_button()
            )
    
    elif data == "ref_link":
        user = get_user(user_id)
        bot_username = (await context.bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start=ref_{user['referral_code']}"
        
        await query.edit_message_text(
            f"Реферальная программа\n━━━━━━━━\n\nСсылка:\n{ref_link}\n\nТы получишь: +{REFERRAL_BONUS} токенов\nДруг получит: +{INVITED_BONUS} токенов\nПриглашено: {user.get('referrals', 0)}",
            reply_markup=back_button()
        )
    
    elif data.startswith("buy_"):
        item_id = data.replace("buy_", "")
        item = SHOP_ITEMS.get(item_id)
        
        if not item:
            return
        
        tokens = get_tokens(user_id)
        
        if tokens < item["price"]:
            await query.answer(f"Недостаточно! Нужно {item['price']}, у тебя {tokens}", show_alert=True)
        else:
            remove_tokens(user_id, item["price"])
            users = load_users()
            uid = str(user_id)
            
            if item_id == "extra5":
                users[uid]["extra_requests"] += 5
            elif item_id == "extra10":
                users[uid]["extra_requests"] += 10
            elif item_id == "unlimited_1h":
                users[uid]["unlimited_until"] = (datetime.now() + timedelta(hours=1)).isoformat()
            elif item_id == "unlimited_24h":
                users[uid]["unlimited_until"] = (datetime.now() + timedelta(hours=24)).isoformat()
            elif item_id == "unlimited_7d":
                users[uid]["unlimited_until"] = (datetime.now() + timedelta(days=7)).isoformat()
            
            save_users(users)
            
            await query.answer(f"Куплено: {item['name']}!", show_alert=True)
            await query.edit_message_text(
                f"Покупка успешна!\n━━━━━━━━\nТовар: {item['name']}\nПотрачено: {item['price']} токенов\nОстаток: {get_tokens(user_id)}",
                reply_markup=back_button()
            )

# Обработчик текстовых сообщений
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    logger.info(f"Сообщение от {user_id}: {text[:50]}")
    
    if not can_request(user_id):
        user = get_user(user_id)
        await update.message.reply_text(
            f"Лимит исчерпан!\n━━━━━━━━\nИспользовано: {user['requests_today']}/{DAILY_LIMIT + user['extra_requests']}\nБаланс: {user['tokens']} токенов\n\nКупи запросы: /shop\nСброс в 00:00"
        )
        return
    
    msg = await update.message.reply_text("Генерирую ответ...")
    
    try:
        response = client.responses.create(
            prompt={"id": PROMPT_ID},
            input=text,
        )
        answer = response.output_text
        
        add_request(user_id)
        
        await msg.delete()
        
        if answer:
            rem = remaining(user_id)
            footer = f"\n\n━━━━━━━━\nОсталось: {rem}"
            
            for i in range(0, len(answer), 4000):
                chunk = answer[i:i+4000]
                if i == 0:
                    await update.message.reply_text(chunk + footer)
                else:
                    await update.message.reply_text(chunk)
        else:
            await update.message.reply_text("Не удалось сгенерировать ответ")
            
    except Exception as e:
        try:
            await msg.delete()
        except:
            pass
        
        logger.error(f"Ошибка: {str(e)[:100]}")
        await update.message.reply_text("Ошибка. Попробуй позже.")

# Запуск
def main():
    logger.info("=" * 30)
    logger.info("NeBlock AI V1")
    logger.info("=" * 30)
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Только три обработчика
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    logger.info("Бот запущен!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
