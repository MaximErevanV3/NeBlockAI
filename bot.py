import openai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import logging
import os
import json
import random
import asyncio
from datetime import datetime, timedelta

# ═══════════════════════════════════════════
# 🧠 NeBlock AI V1 - Конфигурация
# ═══════════════════════════════════════════

TELEGRAM_TOKEN = "8700124191:AAE6qSSouLjlDxPWwoFObJORMbDotsby9co"
YANDEX_API_KEY = "AQVNy7Dm-dvQRzejHvH0383oHTZhhW2fda95I558"
PROMPT_ID = "fvt621uiq1fftiu5qomu"
DAILY_LIMIT = 5
DATA_FILE = "users.json"
PROMO_FILE = "promos.json"
ADMIN_IDS = [1671403667]
START_BONUS = 50
DAILY_BONUS_MIN = 5
DAILY_BONUS_MAX = 15
REFERRAL_BONUS = 25
INVITED_BONUS = 10

SHOP_ITEMS = {
    "extra5": {"name": "+5 запросов", "price": 10, "icon": "📦", "desc": "Добавляет 5 запросов к дневному лимиту на сегодня"},
    "extra10": {"name": "+10 запросов", "price": 18, "icon": "📦", "desc": "Добавляет 10 запросов к дневному лимиту на сегодня"},
    "unlimited_1h": {"name": "Безлимит 1 час", "price": 30, "icon": "⚡", "desc": "Неограниченные запросы в течение 1 часа"},
    "unlimited_24h": {"name": "Безлимит 24 часа", "price": 100, "icon": "⚡", "desc": "Неограниченные запросы в течение 24 часов"},
    "unlimited_7d": {"name": "Безлимит 7 дней", "price": 500, "icon": "🔥", "desc": "Неограниченные запросы в течение 7 дней"},
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("NeBlockAI")

client = openai.OpenAI(
    api_key=YANDEX_API_KEY,
    base_url="https://ai.api.cloud.yandex.net/v1",
    project="b1guk4h3j9t48lsjl6sq",
    timeout=30.0,
)

# ═══════════════════════════════════════════
# 📂 База данных
# ═══════════════════════════════════════════

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_users(): return load_json(DATA_FILE)
def save_users(users): save_json(DATA_FILE, users)
def load_promos(): return load_json(PROMO_FILE)
def save_promos(promos): save_json(PROMO_FILE, promos)

def get_user(user_id):
    users = load_users()
    uid = str(user_id)
    
    defaults = {
        "joined": datetime.now().isoformat(),
        "requests_today": 0,
        "extra_requests": 0,
        "unlimited_until": None,
        "last_request": None,
        "total_requests": 0,
        "reset_date": datetime.now().strftime("%Y-%m-%d"),
        "tokens": START_BONUS,
        "daily_bonus_claimed": None,
        "daily_bonus_streak": 0,
        "last_bonus_date": None,
        "referral_code": "".join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(8)),
        "referred_by": None,
        "referrals": 0,
        "earned_tokens": 0,
        "spent_tokens": 0,
        "used_promos": [],
    }
    
    if uid not in users:
        users[uid] = defaults.copy()
        save_users(users)
    else:
        for key, value in defaults.items():
            if key not in users[uid]:
                users[uid][key] = value
        save_users(users)
    
    today = datetime.now().strftime("%Y-%m-%d")
    if users[uid].get("reset_date") != today:
        users[uid]["requests_today"] = 0
        users[uid]["extra_requests"] = 0
        users[uid]["reset_date"] = today
        save_users(users)
    
    return users[uid]

def add_request(user_id):
    users = load_users()
    uid = str(user_id)
    if uid in users:
        users[uid]["requests_today"] = users[uid].get("requests_today", 0) + 1
        users[uid]["total_requests"] = users[uid].get("total_requests", 0) + 1
        users[uid]["last_request"] = datetime.now().isoformat()
        save_users(users)

def can_request(user_id):
    user = get_user(user_id)
    if user.get("unlimited_until"):
        try:
            if datetime.now() < datetime.fromisoformat(user["unlimited_until"]):
                return True
        except: pass
    return user.get("requests_today", 0) < (DAILY_LIMIT + user.get("extra_requests", 0))

def remaining(user_id):
    user = get_user(user_id)
    if user.get("unlimited_until"):
        try:
            if datetime.now() < datetime.fromisoformat(user["unlimited_until"]):
                return "безлимит"
        except: pass
    return max(0, DAILY_LIMIT + user.get("extra_requests", 0) - user.get("requests_today", 0))

def add_extra_requests(user_id, amount):
    users = load_users()
    if str(user_id) in users:
        users[str(user_id)]["extra_requests"] = users[str(user_id)].get("extra_requests", 0) + amount
        save_users(users)

def add_tokens(user_id, amount):
    users = load_users()
    uid = str(user_id)
    if uid not in users: get_user(user_id); users = load_users()
    users[uid]["tokens"] = users[uid].get("tokens", 0) + amount
    users[uid]["earned_tokens"] = users[uid].get("earned_tokens", 0) + amount
    save_users(users)

def remove_tokens(user_id, amount):
    users = load_users()
    if str(user_id) in users:
        users[str(user_id)]["tokens"] = users[str(user_id)].get("tokens", 0) - amount
        users[str(user_id)]["spent_tokens"] = users[str(user_id)].get("spent_tokens", 0) + amount
        save_users(users)

def get_tokens(user_id):
    return get_user(user_id).get("tokens", 0)

def create_promo(code, amount, max_uses=0):
    promos = load_promos()
    promos[code.upper()] = {"amount": amount, "max_uses": max_uses, "used_by": [], "created": datetime.now().isoformat()}
    save_promos(promos)

def use_promo(user_id, code):
    promos = load_promos()
    code = code.upper()
    if code not in promos: return False, "Промокод не найден"
    promo = promos[code]
    if promo["max_uses"] > 0 and len(promo["used_by"]) >= promo["max_uses"]: return False, "Лимит использований исчерпан"
    if str(user_id) in promo["used_by"]: return False, "Вы уже использовали этот промокод"
    add_tokens(user_id, promo["amount"])
    promo["used_by"].append(str(user_id))
    save_promos(promos)
    return True, promo["amount"]

# ═══════════════════════════════════════════
# 🎛 Клавиатуры
# ═══════════════════════════════════════════

def main_reply_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📝 Задать вопрос"), KeyboardButton("👤 Профиль")],
        [KeyboardButton("🛒 Магазин"), KeyboardButton("💰 Заработать")],
        [KeyboardButton("🎟 Промокод"), KeyboardButton("📚 FAQ")],
    ], resize_keyboard=True)

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("ℹ️ О боте", callback_data="about"),
         InlineKeyboardButton("📊 Статистика", callback_data="stats")],
    ])

def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="menu")]])

def shop_keyboard():
    keyboard = []
    for item_id, item in SHOP_ITEMS.items():
        keyboard.append([InlineKeyboardButton(f"{item['icon']} {item['name']} — {item['price']} токенов", callback_data=f"buy_{item_id}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="menu")])
    return InlineKeyboardMarkup(keyboard)

def confirm_keyboard(item_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_{item_id}")],
        [InlineKeyboardButton("❌ Отмена", callback_data="shop")],
    ])

def earn_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 Ежедневный бонус", callback_data="daily_bonus")],
        [InlineKeyboardButton("👥 Реферальная ссылка", callback_data="ref_link")],
        [InlineKeyboardButton("🔙 Назад", callback_data="menu")],
    ])

def limit_reached_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Купить запросы", callback_data="shop")],
        [InlineKeyboardButton("💰 Заработать токены", callback_data="earn")],
        [InlineKeyboardButton("🎟 Ввести промокод", callback_data="promo")],
    ])

# ═══════════════════════════════════════════
# 🚀 Команды
# ═══════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if context.args and context.args[0].startswith("ref_"):
        ref_code = context.args[0].replace("ref_", "")
        users = load_users()
        uid = str(user_id)
        for u_id, u_data in users.items():
            if u_data.get("referral_code") == ref_code and u_id != uid and not users[uid].get("referred_by"):
                users[uid]["referred_by"] = u_id
                add_tokens(int(u_id), REFERRAL_BONUS)
                add_tokens(user_id, INVITED_BONUS)
                users[u_id]["referrals"] = users[u_id].get("referrals", 0) + 1
                save_users(users)
                try: await context.bot.send_message(int(u_id), f"🎉 Новый реферал!\n💰 +{REFERRAL_BONUS} NeBlock Tokens")
                except: pass
                break
    
    extra = user.get("extra_requests", 0)
    total = DAILY_LIMIT + extra
    
    await update.message.reply_text(
        f"🧠 NeBlock AI V1\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ Быстрые и точные ответы\n"
        f"💻 Помощь с программированием\n"
        f"📚 Объяснение сложных тем\n"
        f"🌐 Поддержка всех языков\n\n"
        f"📊 Лимит: {total} запросов/день\n"
        f"💰 Баланс: {user.get('tokens', 0)} NeBlock Tokens\n\n"
        f"👇 Просто напиши вопрос или используй кнопки:",
        reply_markup=main_reply_keyboard()
    )

# Админ команды
async def admin_give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args or len(context.args) < 2: return
    try:
        add_tokens(int(context.args[0]), int(context.args[1]))
        await update.message.reply_text(f"✅ Начислено {context.args[1]} токенов пользователю {context.args[0]}")
    except: pass

async def admin_create_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args or len(context.args) < 2: return
    create_promo(context.args[0].upper(), int(context.args[1]), int(context.args[2]) if len(context.args) > 2 else 0)
    await update.message.reply_text(f"✅ Промокод {context.args[0].upper()} создан! Награда: {context.args[1]} токенов")

async def admin_promos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    promos = load_promos()
    if not promos: await update.message.reply_text("Нет промокодов."); return
    text = "🎟 Активные промокоды:\n\n"
    for code, data in promos.items():
        text += f"Код: {code}\nНаграда: {data['amount']} токенов\nИспользовано: {len(data['used_by'])}/{data['max_uses'] if data['max_uses'] > 0 else '∞'}\n\n"
    await update.message.reply_text(text)

async def admin_delete_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args: return
    promos = load_promos()
    code = context.args[0].upper()
    if code in promos: del promos[code]; save_promos(promos); await update.message.reply_text(f"✅ Промокод {code} удалён")

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    users = load_users()
    total = len(users)
    active = sum(1 for u in users.values() if u.get("requests_today", 0) > 0)
    await update.message.reply_text(
        f"📊 Статистика бота\n━━━━━━━━━━━━━━━━\n"
        f"👥 Всего пользователей: {total}\n"
        f"📈 Активных сегодня: {active}\n"
        f"📝 Всего запросов: {sum(u.get('total_requests', 0) for u in users.values())}\n"
        f"💰 Токенов в обороте: {sum(u.get('tokens', 0) for u in users.values())}"
    )

# ═══════════════════════════════════════════
# 🔘 Обычные кнопки
# ═══════════════════════════════════════════

async def reply_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    if text == "📝 Задать вопрос":
        await update.message.reply_text(
            f"📝 Задай свой вопрос\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"Просто напиши в чат что угодно.\n"
            f"Я отвечу быстро и по делу.\n\n"
            f"📊 Осталось запросов: {remaining(user_id)}"
        )
        return True
    
    if text == "👤 Профиль":
        await update.message.reply_text(get_full_profile(user_id), reply_markup=main_menu())
        return True
    
    if text == "🛒 Магазин":
        await update.message.reply_text(
            f"🛒 Магазин NeBlock\n━━━━━━━━━━━━━━━━\n"
            f"💰 Твой баланс: {get_tokens(user_id)} NeBlock Tokens\n\n"
            f"Выбери товар для покупки:",
            reply_markup=shop_keyboard()
        )
        return True
    
    if text == "💰 Заработать":
        await update.message.reply_text(
            f"💰 Заработок NeBlock Tokens\n━━━━━━━━━━━━━━━━\n"
            f"💎 Твой баланс: {get_tokens(user_id)} токенов\n\n"
            f"Способы заработка:\n"
            f"🎁 Ежедневный бонус: {DAILY_BONUS_MIN}-{DAILY_BONUS_MAX} токенов\n"
            f"👥 Рефералы: +{REFERRAL_BONUS} тебе, +{INVITED_BONUS} другу\n"
            f"🎯 Стартовый бонус: {START_BONUS} токенов\n"
            f"🎟 Промокоды от админа",
            reply_markup=earn_keyboard()
        )
        return True
    
    if text == "🎟 Промокод":
        context.user_data["waiting_promo"] = True
        await update.message.reply_text(
            f"🎟 Активация промокода\n━━━━━━━━━━━━━━━━\n"
            f"Отправь промокод в чат одним сообщением.\n\n"
            f"Пример: HELLO2024"
        )
        return True
    
    if text == "📚 FAQ":
        await update.message.reply_text(
            f"📚 Часто задаваемые вопросы\n━━━━━━━━━━━━━━━━\n\n"
            f"❓ Что такое NeBlock AI?\n"
            f"ИИ-бот в Telegram. Отвечает на вопросы, пишет код, объясняет темы.\n\n"
            f"❓ Почему лимит 5 запросов?\n"
            f"Чтобы не перегружать нейросеть и сохранять быстрые ответы для всех.\n\n"
            f"❓ Что такое NeBlock Tokens?\n"
            f"Внутренняя валюта бота для покупок в Магазине. Не продаётся за деньги.\n\n"
            f"❓ Доп запросы сгорают?\n"
            f"Да, каждый день в 00:00 МСК.\n\n"
            f"❓ Как заработать токены?\n"
            f"Ежедневный бонус, рефералы, промокоды.\n\n"
            f"❓ Бот помнит контекст?\n"
            f"Да, можно вести диалог."
        )
        return True
    
    return False

def get_full_profile(user_id):
    user = get_user(user_id)
    
    joined = datetime.fromisoformat(user.get("joined", datetime.now().isoformat())).strftime("%d.%m.%Y в %H:%M")
    last = "Никогда"
    if user.get("last_request"):
        last = datetime.fromisoformat(user["last_request"]).strftime("%d.%m.%Y в %H:%M")
    
    unlimited = "Не активен"
    if user.get("unlimited_until"):
        try:
            until = datetime.fromisoformat(user["unlimited_until"])
            if datetime.now() < until:
                diff = until - datetime.now()
                h = diff.seconds // 3600
                m = (diff.seconds % 3600) // 60
                unlimited = f"Активен (осталось {h}ч {m}м)"
        except: pass
    
    extra = user.get("extra_requests", 0)
    total = DAILY_LIMIT + extra
    used = user.get("requests_today", 0)
    
    streak = user.get("daily_bonus_streak", 0)
    
    return (
        f"👤 Личный кабинет\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🆔 ID: {user_id}\n"
        f"📅 Регистрация: {joined}\n\n"
        f"💰 Баланс: {user.get('tokens', 0)} NeBlock Tokens\n"
        f"💎 Заработано всего: {user.get('earned_tokens', 0)}\n"
        f"💸 Потрачено всего: {user.get('spent_tokens', 0)}\n\n"
        f"📊 Лимит запросов:\n"
        f"   • Базовый: {DAILY_LIMIT}\n"
        f"   • Дополнительные: +{extra}\n"
        f"   • Всего сегодня: {total}\n"
        f"   • Использовано: {used}/{total}\n\n"
        f"📈 Всего запросов за всё время: {user.get('total_requests', 0)}\n\n"
        f"⚡ Безлимитный режим: {unlimited}\n\n"
        f"🔥 Серия ежедневных бонусов: {streak} дней\n\n"
        f"👥 Реферальная программа:\n"
        f"   • Приглашено друзей: {user.get('referrals', 0)}\n"
        f"   • Реферальный код: {user.get('referral_code', '')}\n\n"
        f"🕐 Последняя активность: {last}"
    )

# ═══════════════════════════════════════════
# 🔘 Inline кнопки
# ═══════════════════════════════════════════

async def inline_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if data == "menu":
        await query.edit_message_text(
            f"🧠 NeBlock AI V1\n━━━━━━━━━━━━━━━━\n"
            f"💰 Баланс: {get_tokens(user_id)} токенов",
            reply_markup=main_menu()
        )
    elif data == "about":
        await query.edit_message_text(
            "ℹ️ О NeBlock AI\n━━━━━━━━━━━━━━━━\n\n"
            "🧠 Модель: NeBlock AI V1\n"
            "⚡ Быстрые и точные ответы\n"
            "💬 Понимание контекста\n"
            "🌐 Поддержка всех языков\n"
            "💰 Внутренняя экономика\n\n"
            "Создан с заботой о пользователях.",
            reply_markup=back_button()
        )
    elif data == "stats":
        user = get_user(user_id)
        extra = user.get("extra_requests", 0)
        total = DAILY_LIMIT + extra
        await query.edit_message_text(
            f"📊 Твоя статистика\n━━━━━━━━━━━━━━━━\n\n"
            f"📝 Запросов сегодня: {user.get('requests_today', 0)}/{total}\n"
            f"📈 Всего запросов: {user.get('total_requests', 0)}\n"
            f"💰 Баланс: {user.get('tokens', 0)} токенов\n"
            f"👥 Рефералов: {user.get('referrals', 0)}",
            reply_markup=back_button()
        )
    elif data == "shop":
        await query.edit_message_text(
            f"🛒 Магазин\n━━━━━━━━━━━━━━━━\n"
            f"💰 Баланс: {get_tokens(user_id)} токенов\n\n"
            f"Выбери товар:",
            reply_markup=shop_keyboard()
        )
    elif data == "earn":
        await query.edit_message_text(
            f"💰 Заработок\n━━━━━━━━━━━━━━━━\n"
            f"💎 Баланс: {get_tokens(user_id)}\n\n"
            f"🎁 Бонус: {DAILY_BONUS_MIN}-{DAILY_BONUS_MAX} токенов/день\n"
            f"👥 Рефералы: +{REFERRAL_BONUS} тебе, +{INVITED_BONUS} другу",
            reply_markup=earn_keyboard()
        )
    elif data == "promo":
        context.user_data["waiting_promo"] = True
        await query.edit_message_text("🎟 Отправь промокод в чат.", reply_markup=back_button())
    elif data == "faq":
        await query.edit_message_text(
            "📚 FAQ\n\n❓ Лимит 5 запросов - чтобы не перегружать нейросеть.\n"
            "❓ Сброс в 00:00 МСК.\n❓ Токены - внутренняя валюта.",
            reply_markup=back_button()
        )
    elif data == "daily_bonus":
        user = get_user(user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        if user.get("daily_bonus_claimed") == today:
            await query.answer("❌ Уже забирали сегодня!\n🔄 Сброс в 00:00 МСК.", show_alert=True)
        else:
            bonus = random.randint(DAILY_BONUS_MIN, DAILY_BONUS_MAX)
            users = load_users()
            uid = str(user_id)
            users[uid]["daily_bonus_claimed"] = today
            
            # Считаем серию
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            if users[uid].get("last_bonus_date") == yesterday:
                users[uid]["daily_bonus_streak"] = users[uid].get("daily_bonus_streak", 0) + 1
            elif users[uid].get("last_bonus_date") != today:
                users[uid]["daily_bonus_streak"] = 1
            
            users[uid]["last_bonus_date"] = today
            save_users(users)
            add_tokens(user_id, bonus)
            
            streak = users[uid].get("daily_bonus_streak", 1)
            await query.answer(f"🎉 +{bonus} NeBlock Tokens!\n🔥 Серия: {streak} дней", show_alert=True)
            await query.edit_message_text(
                f"🎁 Ежедневный бонус\n━━━━━━━━━━━━━━━━\n"
                f"✅ Получено: +{bonus} токенов\n"
                f"💰 Баланс: {get_tokens(user_id)}\n"
                f"🔥 Серия: {streak} дней\n\n"
                f"🔄 Приходи завтра!",
                reply_markup=back_button()
            )
    elif data == "ref_link":
        user = get_user(user_id)
        bot_username = (await context.bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start=ref_{user.get('referral_code', '')}"
        await query.edit_message_text(
            f"👥 Реферальная программа\n━━━━━━━━━━━━━━━━\n\n"
            f"🔗 Твоя ссылка:\n{ref_link}\n\n"
            f"💰 Ты получишь: +{REFERRAL_BONUS} токенов\n"
            f"🎁 Друг получит: +{INVITED_BONUS} токенов\n"
            f"👥 Уже приглашено: {user.get('referrals', 0)}",
            reply_markup=back_button()
        )
    elif data.startswith("confirm_"):
        item_id = data.replace("confirm_", "")
        item = SHOP_ITEMS.get(item_id)
        if not item: return
        tokens = get_tokens(user_id)
        if tokens < item["price"]:
            await query.answer(f"❌ Недостаточно токенов!\nНужно: {item['price']}\nУ вас: {tokens}", show_alert=True)
            return
        remove_tokens(user_id, item["price"])
        if item_id == "extra5": add_extra_requests(user_id, 5)
        elif item_id == "extra10": add_extra_requests(user_id, 10)
        elif item_id in ["unlimited_1h", "unlimited_24h", "unlimited_7d"]:
            hours = 1 if item_id == "unlimited_1h" else 24 if item_id == "unlimited_24h" else 168
            users = load_users()
            users[str(user_id)]["unlimited_until"] = (datetime.now() + timedelta(hours=hours)).isoformat()
            save_users(users)
        await query.answer(f"✅ {item['name']} активирован!", show_alert=True)
        await query.edit_message_text(
            f"✅ Покупка успешна!\n━━━━━━━━━━━━━━━━\n"
            f"🛒 {item['name']}\n"
            f"📝 {item['desc']}\n"
            f"💰 Потрачено: {item['price']} токенов\n"
            f"💎 Остаток: {get_tokens(user_id)} токенов",
            reply_markup=back_button()
        )
    elif data.startswith("buy_"):
        item_id = data.replace("buy_", "")
        item = SHOP_ITEMS.get(item_id)
        if not item: return
        tokens = get_tokens(user_id)
        can_buy = "✅ Достаточно средств" if tokens >= item["price"] else "❌ Недостаточно средств"
        await query.edit_message_text(
            f"🛒 Подтверждение покупки\n━━━━━━━━━━━━━━━━\n\n"
            f"{item['icon']} Товар: {item['name']}\n"
            f"📝 Описание: {item['desc']}\n"
            f"💰 Цена: {item['price']} токенов\n"
            f"💎 Ваш баланс: {tokens} токенов\n"
            f"{can_buy}\n\n"
            f"Подтвердите покупку:",
            reply_markup=confirm_keyboard(item_id)
        )

# ═══════════════════════════════════════════
# 💬 Сообщения
# ═══════════════════════════════════════════

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id
    
    if await reply_button_handler(update, context):
        return
    
    if context.user_data.get("waiting_promo"):
        context.user_data["waiting_promo"] = False
        success, result = use_promo(user_id, text)
        if success:
            await update.message.reply_text(
                f"🎟 Промокод активирован!\n━━━━━━━━━━━━━━━━\n"
                f"✅ Код: {text.upper()}\n"
                f"💰 Начислено: {result} NeBlock Tokens\n"
                f"💎 Баланс: {get_tokens(user_id)}"
            )
        else:
            await update.message.reply_text(f"❌ {result}")
        return
    
    if not can_request(user_id):
        user = get_user(user_id)
        extra = user.get("extra_requests", 0)
        total = DAILY_LIMIT + extra
        await update.message.reply_text(
            f"🚫 Дневной лимит исчерпан!\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📊 Использовано: {user.get('requests_today', 0)}/{total}\n"
            f"💰 Баланс: {user.get('tokens', 0)} токенов\n\n"
            f"Что делать?\n"
            f"• Купить доп запросы в Магазине\n"
            f"• Заработать токены\n"
            f"• Ввести промокод\n\n"
            f"🔄 Сброс в 00:00 МСК",
            reply_markup=limit_reached_keyboard()
        )
        return
    
    msg = await update.message.reply_text("⚡ Генерирую ответ...")
    await update.message.chat.send_action("typing")
    
    try:
        response = client.responses.create(prompt={"id": PROMPT_ID}, input=text)
        answer = response.output_text
        add_request(user_id)
        await msg.delete()
        
        if answer:
            rem = remaining(user_id)
            user = get_user(user_id)
            used = user.get("requests_today", 0)
            total = DAILY_LIMIT + user.get("extra_requests", 0)
            footer = f"\n\n━━━━━━━━━━━━━━━━\n📊 {used}/{total} | Осталось: {rem}"
            
            for i in range(0, len(answer), 4000):
                chunk = answer[i:i+4000]
                await update.message.reply_text(chunk + footer if i == 0 else chunk)
        else:
            await update.message.reply_text("🤷 Не удалось сгенерировать ответ.")
    except Exception as e:
        try: await msg.delete()
        except: pass
        logger.error(f"Ошибка: {str(e)[:100]}")
        await update.message.reply_text("❌ Ошибка генерации. Попробуй позже.")

# ═══════════════════════════════════════════
# 🚀 Запуск
# ═══════════════════════════════════════════

def main():
    print("🧠 NeBlock AI V1")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("give", admin_give))
    app.add_handler(CommandHandler("createpromo", admin_create_promo))
    app.add_handler(CommandHandler("promos", admin_promos))
    app.add_handler(CommandHandler("deletepromo", admin_delete_promo))
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CallbackQueryHandler(inline_button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    print("✅ Бот запущен!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
