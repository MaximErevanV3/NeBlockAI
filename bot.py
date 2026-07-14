import openai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import asyncio
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
    "extra5": {"name": "+5 запросов", "price": 10, "emoji": "📦"},
    "extra10": {"name": "+10 запросов", "price": 18, "emoji": "📦"},
    "unlimited_1h": {"name": "Безлимит 1 час", "price": 30, "emoji": "⚡"},
    "unlimited_24h": {"name": "Безлимит 24 часа", "price": 100, "emoji": "⚡"},
    "unlimited_7d": {"name": "Безлимит 7 дней", "price": 500, "emoji": "🔥"},
}

FAQ_TEXT = """
📚 ЧАСТЫЕ ВОПРОСЫ

❓ Что такое NeBlock AI?
ИИ-бот в Telegram. Отвечает на вопросы, пишет код, объясняет темы.

❓ Почему лимит 5 запросов в день?
Чтобы не перегружать нейросеть. Так ответы остаются быстрыми для всех.

❓ Что такое NeBlock Tokens?
Внутренняя валюта бота. Нужна для покупок в Магазине. Не продаётся за деньги — только заработок.

❓ Как заработать токены?
• Ежедневный бонус: 5-15 токенов
• Рефералы: +25 тебе, +10 другу
• Стартовый бонус: 50 токенов

❓ Когда сбрасывается лимит?
Каждый день в 00:00 по Москве.

❓ Бот помнит контекст?
Да, можно вести диалог и задавать уточняющие вопросы.

❓ Какие языки понимает?
Автоматически определяет язык и отвечает на нём же.
"""

# Логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("NeBlockAI")

# Клиент Yandex Cloud
client = openai.OpenAI(
    api_key=YANDEX_API_KEY,
    base_url="https://ai.api.cloud.yandex.net/v1",
    project="b1guk4h3j9t48lsjl6sq",
    timeout=30.0,
)

# ==================== БАЗА ДАННЫХ ====================

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
        logger.info(f"Новый пользователь: {user_id}")
    
    # Сброс при новом дне
    today = datetime.now().strftime("%Y-%m-%d")
    if users[uid]["reset_date"] != today:
        users[uid]["requests_today"] = 0
        users[uid]["extra_requests"] = 0
        users[uid]["reset_date"] = today
        save_users(users)
    
    return users[uid]

def generate_ref_code():
    return "".join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(8))

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

# ==================== КЛАВИАТУРЫ ====================

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Задать вопрос", callback_data="ask"),
         InlineKeyboardButton("ℹ️ О боте", callback_data="about")],
        [InlineKeyboardButton("👤 Личный кабинет", callback_data="profile"),
         InlineKeyboardButton("🛒 Магазин", callback_data="shop")],
        [InlineKeyboardButton("💰 Заработать", callback_data="earn"),
         InlineKeyboardButton("📚 FAQ", callback_data="faq")],
    ])

def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="menu")]])

def shop_keyboard():
    keyboard = []
    for item_id, item in SHOP_ITEMS.items():
        keyboard.append([InlineKeyboardButton(
            f"{item['emoji']} {item['name']} — {item['price']} токенов",
            callback_data=f"buy_{item_id}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="menu")])
    return InlineKeyboardMarkup(keyboard)

def earn_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 Ежедневный бонус", callback_data="daily_bonus")],
        [InlineKeyboardButton("👥 Реферальная ссылка", callback_data="ref_link")],
        [InlineKeyboardButton("🔙 Назад", callback_data="menu")],
    ])

# ==================== АНИМАЦИЯ ====================

async def show_typing_with_animation(update, context, user_id):
    """Показывает анимацию генерации"""
    load_msg = await update.message.reply_text("⚡ Генерирую ответ...")
    
    # Запускаем анимацию в фоне
    async def animate():
        dots = ["", ".", "..", "..."]
        i = 0
        for _ in range(20):  # Максимум 20 циклов
            try:
                await load_msg.edit_text(f"⚡ Генерирую ответ{dots[i % 4]}")
                await asyncio.sleep(0.5)
                i += 1
            except:
                break
    
    animation_task = asyncio.create_task(animate())
    await update.message.chat.send_action("typing")
    
    return load_msg, animation_task

# ==================== КОМАНДЫ ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    # Обработка реферала
    if context.args and len(context.args) > 0 and context.args[0].startswith("ref_"):
        ref_code = context.args[0].replace("ref_", "")
        users = load_users()
        uid = str(user_id)
        
        for u_id, u_data in users.items():
            if u_data.get("referral_code") == ref_code and u_id != uid:
                if not users[uid].get("referred_by"):
                    users[uid]["referred_by"] = u_id
                    add_tokens(int(u_id), REFERRAL_BONUS)
                    add_tokens(user_id, INVITED_BONUS)
                    users[u_id]["referrals"] = users[u_id].get("referrals", 0) + 1
                    save_users(users)
                    
                    try:
                        await context.bot.send_message(
                            int(u_id),
                            f"🎉 Новый пользователь по твоей ссылке!\n💰 +{REFERRAL_BONUS} NeBlock Tokens"
                        )
                    except:
                        pass
                break
    
    text = (
        "🧠 **NeBlock AI V1**\n"
        "━━━━━━━━━━━━━━━━\n"
        "⚡ Быстрые и точные ответы\n"
        "💻 Помощь с программированием\n"
        "📚 Объяснение сложных тем\n"
        "🌐 Поддержка всех языков\n\n"
        f"📊 Лимит: {DAILY_LIMIT} запросов/день\n"
        f"💰 Баланс: {user['tokens']} NeBlock Tokens\n\n"
        "👇 Выбери действие или просто напиши вопрос:"
    )
    
    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu(), parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(text, reply_markup=main_menu(), parse_mode="Markdown")

async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    joined = datetime.fromisoformat(user["joined"]).strftime("%d.%m.%Y в %H:%M")
    last = "Никогда"
    if user["last_request"]:
        last = datetime.fromisoformat(user["last_request"]).strftime("%H:%M %d.%m.%Y")
    
    unlimited = "Не активен"
    if user["unlimited_until"]:
        until = datetime.fromisoformat(user["unlimited_until"])
        if datetime.now() < until:
            remaining_time = until - datetime.now()
            hours = remaining_time.seconds // 3600
            minutes = (remaining_time.seconds % 3600) // 60
            unlimited = f"Активен (осталось {hours}ч {minutes}м)"
    
    total_limit = DAILY_LIMIT + user["extra_requests"]
    
    text = (
        "👤 **Личный кабинет**\n"
        "━━━━━━━━━━━━━━━━\n"
        f"🆔 ID: `{user_id}`\n"
        f"📅 Регистрация: {joined}\n"
        f"💰 Баланс: {user['tokens']} токенов\n"
        f"💎 Заработано: {user.get('earned_tokens', 0)}\n"
        f"📊 Запросов сегодня: {user['requests_today']}/{total_limit}\n"
        f"📈 Всего запросов: {user['total_requests']}\n"
        f"⚡ Безлимит: {unlimited}\n"
        f"👥 Рефералов: {user.get('referrals', 0)}\n"
        f"🕐 Активность: {last}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def shop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    tokens = get_tokens(user_id)
    await update.message.reply_text(
        f"🛒 **Магазин NeBlock**\n━━━━━━━━━━━━━━━━\n💰 Баланс: {tokens} токенов\n\nВыбери товар:",
        reply_markup=shop_keyboard(),
        parse_mode="Markdown"
    )

async def faq_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(FAQ_TEXT)

async def give_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Использование: /give ID КОЛИЧЕСТВО")
        return
    
    try:
        target_id = int(args[0])
        amount = int(args[1])
        add_tokens(target_id, amount)
        
        await update.message.reply_text(f"✅ Начислено {amount} токенов пользователю {target_id}")
        try:
            await context.bot.send_message(target_id, f"💰 Администратор начислил тебе {amount} NeBlock Tokens!")
        except:
            pass
    except:
        await update.message.reply_text("Ошибка. Используй: /give ID КОЛИЧЕСТВО")

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        return
    
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Использование: /broadcast ТЕКСТ")
        return
    
    users = load_users()
    sent = 0
    failed = 0
    
    await update.message.reply_text(f"📢 Начинаю рассылку...")
    
    for uid in users:
        try:
            await context.bot.send_message(int(uid), f"📢 **NeBlock AI**\n\n{text}", parse_mode="Markdown")
            sent += 1
            await asyncio.sleep(0.05)  # Защита от спама
        except:
            failed += 1
    
    await update.message.reply_text(f"✅ Рассылка завершена!\n📤 Отправлено: {sent}\n❌ Ошибок: {failed}")

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        return
    
    users = load_users()
    total_users = len(users)
    total_requests = sum(u.get("total_requests", 0) for u in users.values())
    total_tokens = sum(u.get("tokens", 0) for u in users.values())
    active_today = sum(1 for u in users.values() if u.get("requests_today", 0) > 0)
    
    text = (
        "📊 **Статистика NeBlock AI**\n"
        "━━━━━━━━━━━━━━━━\n"
        f"👥 Пользователей: {total_users}\n"
        f"📝 Всего запросов: {total_requests}\n"
        f"💰 Токенов в обороте: {total_tokens}\n"
        f"📈 Активных сегодня: {active_today}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ==================== КНОПКИ ====================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    # Назад в меню
    if data == "menu":
        user = get_user(user_id)
        text = (
            "🧠 **NeBlock AI V1**\n"
            "━━━━━━━━━━━━━━━━\n"
            f"📊 Лимит: {DAILY_LIMIT} запросов/день\n"
            f"💰 Баланс: {user['tokens']} токенов\n\n"
            "👇 Выбери действие:"
        )
        await query.edit_message_text(text, reply_markup=main_menu(), parse_mode="Markdown")
        return
    
    # Профиль
    if data == "profile":
        user = get_user(user_id)
        joined = datetime.fromisoformat(user["joined"]).strftime("%d.%m.%Y")
        last = "Никогда" if not user["last_request"] else datetime.fromisoformat(user["last_request"]).strftime("%H:%M %d.%m.%Y")
        unlimited = "Не активен"
        if user["unlimited_until"] and datetime.now() < datetime.fromisoformat(user["unlimited_until"]):
            until = datetime.fromisoformat(user["unlimited_until"])
            remaining_time = until - datetime.now()
            hours = remaining_time.seconds // 3600
            minutes = (remaining_time.seconds % 3600) // 60
            unlimited = f"Активен ({hours}ч {minutes}м)"
        
        text = (
            "👤 **Личный кабинет**\n"
            "━━━━━━━━━━━━━━━━\n"
            f"🆔 ID: `{user_id}`\n"
            f"📅 Регистрация: {joined}\n"
            f"💰 Баланс: {user['tokens']} токенов\n"
            f"💎 Заработано: {user.get('earned_tokens', 0)}\n"
            f"📊 Запросов сегодня: {user['requests_today']}/{DAILY_LIMIT + user['extra_requests']}\n"
            f"📈 Всего запросов: {user['total_requests']}\n"
            f"⚡ Безлимит: {unlimited}\n"
            f"👥 Рефералов: {user.get('referrals', 0)}\n"
            f"🕐 Активность: {last}"
        )
        await query.edit_message_text(text, reply_markup=back_button(), parse_mode="Markdown")
        return
    
    # Магазин
    if data == "shop":
        await query.edit_message_text(
            f"🛒 **Магазин NeBlock**\n━━━━━━━━━━━━━━━━\n💰 Баланс: {get_tokens(user_id)} токенов\n\nВыбери товар:",
            reply_markup=shop_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    # Заработок
    if data == "earn":
        await query.edit_message_text(
            f"💰 **Заработок токенов**\n━━━━━━━━━━━━━━━━\n💎 Баланс: {get_tokens(user_id)}\n\n"
            f"🎁 Ежедневный бонус: {DAILY_BONUS_MIN}-{DAILY_BONUS_MAX} токенов\n"
            f"👥 Рефералы: +{REFERRAL_BONUS} тебе, +{INVITED_BONUS} другу\n"
            f"🎯 Стартовый бонус: {START_BONUS} токенов",
            reply_markup=earn_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    # FAQ
    if data == "faq":
        await query.edit_message_text(FAQ_TEXT, reply_markup=back_button())
        return
    
    # Ежедневный бонус
    if data == "daily_bonus":
        user = get_user(user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        
        if user.get("daily_bonus_claimed") == today:
            await query.answer("Ты уже получил бонус сегодня! Возвращайся завтра.", show_alert=True)
            return
        
        bonus = random.randint(DAILY_BONUS_MIN, DAILY_BONUS_MAX)
        users = load_users()
        users[str(user_id)]["daily_bonus_claimed"] = today
        save_users(users)
        add_tokens(user_id, bonus)
        
        await query.answer(f"🎉 +{bonus} NeBlock Tokens!", show_alert=True)
        await query.edit_message_text(
            f"🎁 **Ежедневный бонус**\n━━━━━━━━━━━━━━━━\n"
            f"✅ Получено: +{bonus} токенов\n"
            f"💰 Баланс: {get_tokens(user_id)} токенов\n\n"
            f"🔄 Приходи завтра за новым бонусом!",
            reply_markup=back_button(),
            parse_mode="Markdown"
        )
        return
    
    # Реферальная ссылка
    if data == "ref_link":
        user = get_user(user_id)
        bot_username = (await context.bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start=ref_{user['referral_code']}"
        
        await query.edit_message_text(
            f"👥 **Реферальная программа**\n━━━━━━━━━━━━━━━━\n"
            f"🔗 Твоя ссылка:\n`{ref_link}`\n\n"
            f"💰 Ты получаешь: +{REFERRAL_BONUS} токенов\n"
            f"🎁 Друг получает: +{INVITED_BONUS} токенов\n"
            f"👥 Приглашено: {user.get('referrals', 0)}",
            reply_markup=back_button(),
            parse_mode="Markdown"
        )
        return
    
    # Покупки
    if data.startswith("buy_"):
        item_id = data.replace("buy_", "")
        item = SHOP_ITEMS.get(item_id)
        
        if not item:
            return
        
        tokens = get_tokens(user_id)
        
        if tokens < item["price"]:
            await query.answer(f"Недостаточно токенов! Нужно {item['price']}, у тебя {tokens}", show_alert=True)
            return
        
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
        
        await query.answer(f"✅ {item['name']} активирован!", show_alert=True)
        await query.edit_message_text(
            f"✅ **Покупка успешна!**\n━━━━━━━━━━━━━━━━\n"
            f"🛒 Товар: {item['name']}\n"
            f"💰 Потрачено: {item['price']} токенов\n"
            f"💎 Остаток: {get_tokens(user_id)} токенов",
            reply_markup=back_button(),
            parse_mode="Markdown"
        )
        return
    
    # Остальные кнопки
    pages = {
        "ask": f"📝 **Задай вопрос**\n━━━━━━━━━━━━━━━━\nПросто напиши в чат что угодно.\nЯ отвечу быстро и по делу.\n\n📊 Осталось запросов: {remaining(user_id)}",
        "about": "ℹ️ **NeBlock AI V1**\n━━━━━━━━━━━━━━━━\n🧠 Модель: NeBlock AI V1\n⚡ Быстрые ответы\n💬 Понимание контекста\n🌐 Все языки\n💰 Внутренняя экономика",
    }
    
    if data in pages:
        await query.edit_message_text(pages[data], reply_markup=back_button(), parse_mode="Markdown")

# ==================== СООБЩЕНИЯ ====================

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id
    
    if not text:
        return
    
    if len(text) > 2000:
        await update.message.reply_text("⚠️ Сообщение слишком длинное. Максимум 2000 символов.")
        return
    
    # Проверка лимита
    if not can_request(user_id):
        user = get_user(user_id)
        await update.message.reply_text(
            f"🚫 **Лимит исчерпан!**\n━━━━━━━━━━━━━━━━\n"
            f"📊 Использовано: {user['requests_today']}/{DAILY_LIMIT + user['extra_requests']}\n"
            f"💰 Баланс: {user['tokens']} токенов\n\n"
            f"🛒 Купи доп запросы: /shop\n"
            f"🔄 Сброс в 00:00 МСК",
            parse_mode="Markdown"
        )
        return
    
    user_name = update.effective_user.first_name or update.effective_user.username or "Пользователь"
    logger.info(f"Запрос от {user_name} ({user_id}): {text[:60]}")
    
    # Анимация
    load_msg = await update.message.reply_text("⚡ Генерирую ответ...")
    
    async def animate():
        dots = ["", ".", "..", "..."]
        i = 0
        for _ in range(30):
            try:
                await load_msg.edit_text(f"⚡ Генерирую ответ{dots[i % 4]}")
                await asyncio.sleep(0.5)
                i += 1
            except:
                break
    
    anim_task = asyncio.create_task(animate())
    await update.message.chat.send_action("typing")
    
    try:
        response = client.responses.create(
            prompt={"id": PROMPT_ID},
            input=text,
        )
        answer = response.output_text
        
        # Учитываем запрос
        add_request(user_id)
        
        # Останавливаем анимацию
        anim_task.cancel()
        try:
            await load_msg.delete()
        except:
            pass
        
        if answer:
            rem = remaining(user_id)
            footer = f"\n\n━━━━━━━━━━━━━━━━\n📊 Осталось: {rem}"
            
            # Отправка с разбивкой
            for i in range(0, len(answer), 4000):
                chunk = answer[i:i+4000]
                if i == 0:
                    await update.message.reply_text(chunk + footer)
                else:
                    await update.message.reply_text(chunk)
        else:
            await update.message.reply_text("🤷 Не удалось сгенерировать ответ. Попробуй переформулировать вопрос.")
            
    except Exception as e:
        anim_task.cancel()
        try:
            await load_msg.delete()
        except:
            pass
        
        error = str(e)
        logger.error(f"Ошибка API: {error[:150]}")
        
        if "timeout" in error.lower():
            await update.message.reply_text("⏰ Нейросеть не успела ответить. Попробуй ещё раз.")
        elif "rate" in error.lower():
            await update.message.reply_text("🚫 Слишком много запросов. Подожди немного.")
        else:
            await update.message.reply_text("❌ Произошла ошибка. Попробуй позже.")

# ==================== ЗАПУСК ====================

def main():
    logger.info("=" * 40)
    logger.info("🧠 NeBlock AI V1")
    logger.info("=" * 40)
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("profile", profile_cmd))
    app.add_handler(CommandHandler("shop", shop_cmd))
    app.add_handler(CommandHandler("faq", faq_cmd))
    app.add_handler(CommandHandler("give", give_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    
    # Кнопки и сообщения
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    
    logger.info("✅ Бот запущен!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
