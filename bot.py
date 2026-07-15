import openai
import base64
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import logging
import os
import json
import random
from datetime import datetime, timedelta

# ═══════════════════════════════════════════
# 🧠 NeBlock AI - Конфигурация
# ═══════════════════════════════════════════

TELEGRAM_TOKEN = "8700124191:AAE6qSSouLjlDxPWwoFObJORMbDotsby9co"
YANDEX_API_KEY = "AQVNy7Dm-dvQRzejHvH0383oHTZhhW2fda95I558"
YANDEX_FOLDER = "b1guk4h3j9t48lsjl6sq"
PROMPT_ID = "fvt621uiq1fftiu5qomu"
IMAGE_MODEL = "art://b1guk4h3j9t48lsjl6sq/aliceai-image-art-3.0/latest"

DAILY_LIMIT = 5
IMAGE_DAILY_LIMIT = 3
DATA_FILE = "users.json"
PROMO_FILE = "promos.json"
ADMIN_IDS = [1671403667]
START_BONUS = 50
DAILY_BONUS_MIN = 5
DAILY_BONUS_MAX = 15
REFERRAL_BONUS = 25
INVITED_BONUS = 10

SHOP_ITEMS = {
    "extra5": {"name": "+5 запросов", "price": 10, "icon": "📦", "desc": "+5 запросов к дневному лимиту", "category": "text"},
    "extra10": {"name": "+10 запросов", "price": 18, "icon": "📦", "desc": "+10 запросов к дневному лимиту", "category": "text"},
    "unlimited_1h": {"name": "Безлимит 1 час", "price": 30, "icon": "♾️", "desc": "Безлимит на 1 час", "category": "text"},
    "unlimited_24h": {"name": "Безлимит 24 часа", "price": 100, "icon": "♾️", "desc": "Безлимит на 24 часа", "category": "text"},
    "unlimited_7d": {"name": "Безлимит 7 дней", "price": 500, "icon": "♾️", "desc": "Безлимит на 7 дней", "category": "text"},
    "image1": {"name": "1 генерация фото", "price": 15, "icon": "🎨", "desc": "1 генерация изображения", "category": "image"},
    "image5": {"name": "5 генераций фото", "price": 60, "icon": "🎨", "desc": "5 генераций изображений", "category": "image"},
    "image_unlimited_1h": {"name": "Безлимит фото 1ч", "price": 50, "icon": "♾️", "desc": "Безлимит генераций фото на 1 час", "category": "image"},
}

FAQ_TEXT = """
📚 ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ
━━━━━━━━━━━━━━━━━━━━

❓ Что такое NeBlock AI?
Платформа с двумя ИИ-моделями в Telegram:
• NeBlock AI V1 — отвечает на вопросы, пишет код
• NeBlock Images V1 — генерирует изображения

❓ Как переключаться между моделями?
Используй кнопки «💬 Задать вопрос» (текст) или «🎨 Сгенерировать фото» (изображения). Бот сам поймёт что тебе нужно.

❓ Почему лимиты 5 вопросов и 3 фото в день?
Лимиты установлены чтобы не перегружать нейросеть и обеспечить стабильную работу для всех пользователей.

❓ Что такое NeBlock Tokens?
Внутренняя валюта для покупок в Магазине. Не продаётся за реальные деньги — только заработок.

❓ Как заработать токены?
• Ежедневный бонус: 5-15 токенов каждый день
• Реферальная программа: +25 тебе, +10 другу
• Стартовый бонус: 50 токенов при регистрации
• Промокоды от администратора

❓ 🆕 Как работает NeBlock Images V1?
Нажми кнопку «Сгенерировать фото», напиши описание, и модель создаст изображение за 10-30 секунд.

❓ Какие фото можно создавать?
Любые описания: пейзажи, персонажи, предметы, абстракции. Чем подробнее описание — тем лучше результат.

❓ Когда сбрасываются лимиты?
Каждый день в 00:00 по московскому времени. Дополнительные запросы тоже сгорают.

❓ Бот помнит историю диалога?
Да, можно вести диалог и задавать уточняющие вопросы (только текстовая модель).

❓ Бот работает круглосуточно?
Да, бот работает на сервере 24/7.
"""

MODELS_INFO = """
🧠 МОДЕЛИ NeBlock AI
━━━━━━━━━━━━━━━━━━━━

💬 NeBlock AI V1
Текстовая модель для ответов на вопросы, помощи с кодом, объяснения тем, переводов и многого другого.

🎨 NeBlock Images V1 🆕
Модель для генерации изображений по текстовому описанию. Создаёт уникальные картинки за 10-30 секунд.

🔽 Для переключения используй кнопки внизу:
"""

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("NeBlockAI")

client = openai.OpenAI(
    api_key=YANDEX_API_KEY,
    base_url="https://ai.api.cloud.yandex.net/v1",
    project=YANDEX_FOLDER,
    timeout=60.0,
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
        "requests_today": 0, "extra_requests": 0,
        "image_requests_today": 0, "extra_image_requests": 0,
        "unlimited_until": None, "image_unlimited_until": None,
        "last_request": None, "total_requests": 0, "total_images": 0,
        "reset_date": datetime.now().strftime("%Y-%m-%d"),
        "tokens": START_BONUS, "daily_bonus_claimed": None,
        "daily_bonus_streak": 0, "last_bonus_date": None,
        "referral_code": "".join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(8)),
        "referred_by": None, "referrals": 0, "earned_tokens": 0, "spent_tokens": 0,
        "used_promos": [], "waiting_for_image": False, "current_model": "text",
    }
    
    if uid not in users:
        users[uid] = defaults.copy()
        save_users(users)
    else:
        for key, value in defaults.items():
            if key not in users[uid]: users[uid][key] = value
        save_users(users)
    
    today = datetime.now().strftime("%Y-%m-%d")
    if users[uid].get("reset_date") != today:
        users[uid]["requests_today"] = 0
        users[uid]["extra_requests"] = 0
        users[uid]["image_requests_today"] = 0
        users[uid]["extra_image_requests"] = 0
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

def add_image_request(user_id):
    users = load_users()
    uid = str(user_id)
    if uid in users:
        users[uid]["image_requests_today"] = users[uid].get("image_requests_today", 0) + 1
        users[uid]["total_images"] = users[uid].get("total_images", 0) + 1
        users[uid]["last_request"] = datetime.now().isoformat()
        save_users(users)

def can_request(user_id):
    user = get_user(user_id)
    if user.get("unlimited_until"):
        try:
            if datetime.now() < datetime.fromisoformat(user["unlimited_until"]): return True
        except: pass
    return user.get("requests_today", 0) < (DAILY_LIMIT + user.get("extra_requests", 0))

def can_image_request(user_id):
    user = get_user(user_id)
    if user.get("image_unlimited_until"):
        try:
            if datetime.now() < datetime.fromisoformat(user["image_unlimited_until"]): return True
        except: pass
    return user.get("image_requests_today", 0) < (IMAGE_DAILY_LIMIT + user.get("extra_image_requests", 0))

def remaining(user_id):
    user = get_user(user_id)
    if user.get("unlimited_until"):
        try:
            if datetime.now() < datetime.fromisoformat(user["unlimited_until"]): return "безлимит"
        except: pass
    return max(0, DAILY_LIMIT + user.get("extra_requests", 0) - user.get("requests_today", 0))

def image_remaining(user_id):
    user = get_user(user_id)
    if user.get("image_unlimited_until"):
        try:
            if datetime.now() < datetime.fromisoformat(user["image_unlimited_until"]): return "безлимит"
        except: pass
    return max(0, IMAGE_DAILY_LIMIT + user.get("extra_image_requests", 0) - user.get("image_requests_today", 0))

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

def get_tokens(user_id): return get_user(user_id).get("tokens", 0)

def create_promo(code, amount, max_uses=0):
    promos = load_promos()
    promos[code.upper()] = {"amount": amount, "max_uses": max_uses, "used_by": [], "created": datetime.now().isoformat()}
    save_promos(promos)

def use_promo(user_id, code):
    promos = load_promos()
    code = code.upper()
    if code not in promos: return False, "Промокод не найден"
    promo = promos[code]
    if promo["max_uses"] > 0 and len(promo["used_by"]) >= promo["max_uses"]: return False, "Лимит использований"
    if str(user_id) in promo["used_by"]: return False, "Уже использован"
    add_tokens(user_id, promo["amount"])
    promo["used_by"].append(str(user_id))
    save_promos(promos)
    return True, promo["amount"]

async def generate_image(prompt):
    try:
        response = client.images.generate(model=IMAGE_MODEL, prompt=prompt, size="1024x1024")
        return base64.b64decode(response.data[0].b64_json), None
    except Exception as e:
        return None, str(e)

# ═══════════════════════════════════════════
# 🎛 Клавиатуры
# ═══════════════════════════════════════════

def main_reply_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("💬 NeBlock AI V1"), KeyboardButton("🎨 NeBlock Images V1 🆕")],
        [KeyboardButton("👤 Профиль"), KeyboardButton("🛒 Магазин")],
        [KeyboardButton("💰 Заработать"), KeyboardButton("📚 FAQ")],
        [KeyboardButton("🧠 Модели")],
    ], resize_keyboard=True)

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("ℹ️ О боте", callback_data="about"),
         InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🧠 Модели", callback_data="models")],
    ])

def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="menu")]])

def shop_keyboard():
    keyboard = []
    # Текстовые товары
    text_items = [item for item in SHOP_ITEMS.items() if item[1]["category"] == "text"]
    image_items = [item for item in SHOP_ITEMS.items() if item[1]["category"] == "image"]
    
    keyboard.append([InlineKeyboardButton("── 💬 NeBlock AI V1 ──", callback_data="none")])
    for item_id, item in text_items:
        keyboard.append([InlineKeyboardButton(f"{item['icon']} {item['name']} — {item['price']} токенов", callback_data=f"buy_{item_id}")])
    
    keyboard.append([InlineKeyboardButton("── 🎨 NeBlock Images V1 ──", callback_data="none")])
    for item_id, item in image_items:
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

def limit_reached_keyboard(category="text"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Купить запросы", callback_data="shop")],
        [InlineKeyboardButton("💰 Заработать", callback_data="earn")],
        [InlineKeyboardButton("🎟 Промокод", callback_data="promo")],
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
    
    await update.message.reply_text(
        f"🧠 NeBlock AI\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💬 NeBlock AI V1 — ответы на вопросы\n"
        f"🎨 NeBlock Images V1 🆕 — генерация фото\n\n"
        f"📊 Лимиты:\n"
        f"   • Текст: {DAILY_LIMIT} запросов/день\n"
        f"   • Фото: {IMAGE_DAILY_LIMIT} генераций/день\n"
        f"💰 Баланс: {user.get('tokens', 0)} NeBlock Tokens\n\n"
        f"👇 Выбери модель:",
        reply_markup=main_reply_keyboard()
    )
    await update.message.reply_text(MODELS_INFO, reply_markup=main_menu())

async def admin_give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args or len(context.args) < 2: return
    try:
        add_tokens(int(context.args[0]), int(context.args[1]))
        await update.message.reply_text(f"✅ Начислено {context.args[1]} токенов")
    except: pass

async def admin_create_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args or len(context.args) < 2: return
    create_promo(context.args[0].upper(), int(context.args[1]), int(context.args[2]) if len(context.args) > 2 else 0)
    await update.message.reply_text(f"✅ Промокод {context.args[0].upper()} создан!")

async def admin_promos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    promos = load_promos()
    if not promos: await update.message.reply_text("Нет промокодов."); return
    text = "🎟 Промокоды:\n\n"
    for code, data in promos.items(): text += f"{code}: {data['amount']} токенов\n"
    await update.message.reply_text(text)

async def admin_delete_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args: return
    promos = load_promos()
    code = context.args[0].upper()
    if code in promos: del promos[code]; save_promos(promos); await update.message.reply_text(f"✅ Удалён")

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    users = load_users()
    await update.message.reply_text(
        f"📊 Статистика\n━━━━━━━━━━━━━━━━\n"
        f"👥 Пользователей: {len(users)}\n"
        f"💬 Текстовых запросов: {sum(u.get('total_requests', 0) for u in users.values())}\n"
        f"🎨 Изображений: {sum(u.get('total_images', 0) for u in users.values())}\n"
        f"💰 Токенов: {sum(u.get('tokens', 0) for u in users.values())}"
    )

# ═══════════════════════════════════════════
# 🔘 Обычные кнопки
# ═══════════════════════════════════════════

async def reply_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    if text == "💬 NeBlock AI V1":
        users = load_users()
        users[str(user_id)]["current_model"] = "text"
        users[str(user_id)]["waiting_for_image"] = False
        save_users(users)
        await update.message.reply_text(
            f"💬 NeBlock AI V1 активирована\n━━━━━━━━━━━━━━━━\n"
            f"Задай свой вопрос в чат.\n\n"
            f"📊 Осталось запросов: {remaining(user_id)}"
        )
        return True
    
    if text == "🎨 NeBlock Images V1 🆕":
        users = load_users()
        users[str(user_id)]["current_model"] = "image"
        users[str(user_id)]["waiting_for_image"] = True
        save_users(users)
        await update.message.reply_text(
            f"🎨 NeBlock Images V1 активирована\n━━━━━━━━━━━━━━━━\n"
            f"Опиши что нарисовать.\nНапример: космический кот на луне\n\n"
            f"📊 Осталось генераций: {image_remaining(user_id)}\n"
            f"⏳ Генерация занимает 10-30 секунд"
        )
        return True
    
    if text == "👤 Профиль":
        await update.message.reply_text(get_full_profile(user_id), reply_markup=main_menu())
        return True
    
    if text == "🛒 Магазин":
        await update.message.reply_text(
            f"🛒 Магазин\n━━━━━━━━━━━━━━━━\n💰 Баланс: {get_tokens(user_id)} токенов\n\n"
            f"Выбери категорию:",
            reply_markup=shop_keyboard()
        )
        return True
    
    if text == "💰 Заработать":
        await update.message.reply_text(
            f"💰 Заработок\n━━━━━━━━━━━━━━━━\n💎 Баланс: {get_tokens(user_id)}\n\n"
            f"🎁 Бонус: {DAILY_BONUS_MIN}-{DAILY_BONUS_MAX} токенов/день\n"
            f"👥 Рефералы: +{REFERRAL_BONUS} тебе, +{INVITED_BONUS} другу\n"
            f"🎟 Промокоды от админа",
            reply_markup=earn_keyboard()
        )
        return True
    
    if text == "📚 FAQ":
        await update.message.reply_text(FAQ_TEXT)
        return True
    
    if text == "🧠 Модели":
        await update.message.reply_text(MODELS_INFO)
        return True
    
    return False

def get_full_profile(user_id):
    user = get_user(user_id)
    joined = datetime.fromisoformat(user.get("joined", "")).strftime("%d.%m.%Y")
    last = "Никогда"
    if user.get("last_request"): last = datetime.fromisoformat(user["last_request"]).strftime("%d.%m.%Y в %H:%M")
    
    current_model = "💬 NeBlock AI V1" if user.get("current_model") == "text" else "🎨 NeBlock Images V1"
    
    def format_unlimited(until_str):
        if not until_str: return "Не активен"
        try:
            if datetime.now() < datetime.fromisoformat(until_str):
                diff = datetime.fromisoformat(until_str) - datetime.now()
                days, hours = diff.days, diff.seconds // 3600
                return f"Активен ({days}д {hours}ч)" if days > 0 else f"Активен ({hours}ч)"
        except: pass
        return "Не активен"
    
    return (
        f"👤 Личный кабинет\n━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🆔 ID: {user_id}\n"
        f"📅 Регистрация: {joined}\n"
        f"🔮 Активная модель: {current_model}\n\n"
        f"💰 Баланс: {user.get('tokens', 0)} токенов\n"
        f"💎 Заработано: {user.get('earned_tokens', 0)}\n"
        f"💸 Потрачено: {user.get('spent_tokens', 0)}\n\n"
        f"💬 NeBlock AI V1:\n"
        f"   • Сегодня: {user.get('requests_today', 0)}/{DAILY_LIMIT + user.get('extra_requests', 0)}\n"
        f"   • Всего: {user.get('total_requests', 0)}\n"
        f"   • Безлимит: {format_unlimited(user.get('unlimited_until'))}\n\n"
        f"🎨 NeBlock Images V1:\n"
        f"   • Сегодня: {user.get('image_requests_today', 0)}/{IMAGE_DAILY_LIMIT + user.get('extra_image_requests', 0)}\n"
        f"   • Всего: {user.get('total_images', 0)}\n"
        f"   • Безлимит: {format_unlimited(user.get('image_unlimited_until'))}\n\n"
        f"🔥 Серия бонусов: {user.get('daily_bonus_streak', 0)} дней\n"
        f"👥 Рефералов: {user.get('referrals', 0)}\n"
        f"🕐 Активность: {last}"
    )

# ═══════════════════════════════════════════
# 🔘 Inline кнопки
# ═══════════════════════════════════════════

async def inline_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if data == "none":
        return
    
    if data == "menu":
        await query.edit_message_text(f"🧠 NeBlock AI\n💰 {get_tokens(user_id)} токенов", reply_markup=main_menu())
    elif data == "about":
        await query.edit_message_text(
            "ℹ️ NeBlock AI\n━━━━━━━━━━━━━━━━\n\n"
            "💬 NeBlock AI V1 — текстовая модель\n"
            "🎨 NeBlock Images V1 — генерация фото 🆕\n\n"
            "🌐 Все языки | 💰 Токены | 🔄 Сброс в 00:00",
            reply_markup=back_button()
        )
    elif data == "models":
        await query.edit_message_text(MODELS_INFO, reply_markup=back_button())
    elif data == "stats":
        user = get_user(user_id)
        await query.edit_message_text(
            f"📊 Статистика\n━━━━━━━━━━━━━━━━\n\n"
            f"💬 NeBlock AI V1: {user.get('total_requests', 0)} запросов\n"
            f"🎨 NeBlock Images V1: {user.get('total_images', 0)} фото\n"
            f"💰 Баланс: {user.get('tokens', 0)} токенов",
            reply_markup=back_button()
        )
    elif data == "shop":
        await query.edit_message_text(f"🛒 Магазин\n💰 {get_tokens(user_id)} токенов\n\n💬 Текст | 🎨 Фото | ♾️ Безлимиты", reply_markup=shop_keyboard())
    elif data == "earn":
        await query.edit_message_text(f"💰 Заработок\n💎 {get_tokens(user_id)}\n🎁 Бонус: {DAILY_BONUS_MIN}-{DAILY_BONUS_MAX}", reply_markup=earn_keyboard())
    elif data == "promo":
        context.user_data["waiting_promo"] = True
        await query.edit_message_text("🎟 Отправь промокод.", reply_markup=back_button())
    elif data == "faq":
        await query.edit_message_text(FAQ_TEXT, reply_markup=back_button())
    elif data == "daily_bonus":
        user = get_user(user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        if user.get("daily_bonus_claimed") == today:
            await query.answer("❌ Уже забирали сегодня!", show_alert=True)
        else:
            bonus = random.randint(DAILY_BONUS_MIN, DAILY_BONUS_MAX)
            users = load_users()
            uid = str(user_id)
            users[uid]["daily_bonus_claimed"] = today
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            users[uid]["daily_bonus_streak"] = users[uid].get("daily_bonus_streak", 0) + 1 if users[uid].get("last_bonus_date") == yesterday else 1
            users[uid]["last_bonus_date"] = today
            save_users(users)
            add_tokens(user_id, bonus)
            await query.answer(f"🎉 +{bonus} токенов!", show_alert=True)
            await query.edit_message_text(f"🎁 +{bonus}\n💰 {get_tokens(user_id)}", reply_markup=back_button())
    elif data == "ref_link":
        user = get_user(user_id)
        bot_username = (await context.bot.get_me()).username
        await query.edit_message_text(
            f"👥 Ссылка:\nhttps://t.me/{bot_username}?start=ref_{user.get('referral_code', '')}\n\n💰 +{REFERRAL_BONUS} тебе\n🎁 +{INVITED_BONUS} другу",
            reply_markup=back_button()
        )
    elif data.startswith("confirm_"):
        item_id = data.replace("confirm_", "")
        item = SHOP_ITEMS.get(item_id)
        if not item: return
        tokens = get_tokens(user_id)
        if tokens < item["price"]:
            await query.answer(f"❌ Недостаточно!", show_alert=True)
            return
        remove_tokens(user_id, item["price"])
        users = load_users()
        uid = str(user_id)
        if item_id == "extra5": users[uid]["extra_requests"] += 5
        elif item_id == "extra10": users[uid]["extra_requests"] += 10
        elif item_id == "image1": users[uid]["extra_image_requests"] += 1
        elif item_id == "image5": users[uid]["extra_image_requests"] += 5
        elif item_id == "unlimited_1h": users[uid]["unlimited_until"] = (datetime.now() + timedelta(hours=1)).isoformat()
        elif item_id == "unlimited_24h": users[uid]["unlimited_until"] = (datetime.now() + timedelta(hours=24)).isoformat()
        elif item_id == "unlimited_7d": users[uid]["unlimited_until"] = (datetime.now() + timedelta(days=7)).isoformat()
        elif item_id == "image_unlimited_1h": users[uid]["image_unlimited_until"] = (datetime.now() + timedelta(hours=1)).isoformat()
        save_users(users)
        await query.answer(f"✅ {item['name']}!", show_alert=True)
        await query.edit_message_text(f"✅ {item['name']}\n💎 {get_tokens(user_id)}", reply_markup=back_button())
    elif data.startswith("buy_"):
        item_id = data.replace("buy_", "")
        item = SHOP_ITEMS.get(item_id)
        if not item: return
        tokens = get_tokens(user_id)
        can = "✅ Хватает" if tokens >= item["price"] else "❌ Не хватает"
        model_name = "NeBlock AI V1" if item["category"] == "text" else "NeBlock Images V1"
        await query.edit_message_text(
            f"🛒 {item['icon']} {item['name']}\n📝 Для: {model_name}\n💰 Цена: {item['price']}\n💎 Баланс: {tokens}\n{can}",
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
    
    user = get_user(user_id)
    current_model = user.get("current_model", "text")
    
    # Промокод
    if context.user_data.get("waiting_promo"):
        context.user_data["waiting_promo"] = False
        success, result = use_promo(user_id, text)
        await update.message.reply_text(f"🎟 +{result} токенов!\n💎 {get_tokens(user_id)}" if success else f"❌ {result}")
        return
    
    # Если активна модель изображений
    if current_model == "image" or user.get("waiting_for_image"):
        users = load_users()
        users[str(user_id)]["waiting_for_image"] = False
        save_users(users)
        
        if not can_image_request(user_id):
            await update.message.reply_text(
                f"🚫 Лимит NeBlock Images V1 исчерпан!\n"
                f"📊 {user.get('image_requests_today', 0)}/{IMAGE_DAILY_LIMIT + user.get('extra_image_requests', 0)}\n"
                f"🛒 Купи генерации в Магазине",
                reply_markup=limit_reached_keyboard()
            )
            return
        
        msg = await update.message.reply_text("🎨 NeBlock Images V1 генерирует...\n⏳ 10-30 секунд")
        await update.message.chat.send_action("upload_photo")
        
        try:
            image_bytes, error = await generate_image(text)
            if image_bytes:
                add_image_request(user_id)
                await msg.delete()
                rem = image_remaining(user_id)
                await update.message.reply_photo(
                    photo=image_bytes,
                    caption=f"🎨 NeBlock Images V1\n📝 {text[:200]}\n\n📊 Осталось: {rem}"
                )
            else:
                await msg.edit_text(f"❌ Ошибка: {error[:100] if error else 'Неизвестная'}")
        except Exception as e:
            try: await msg.delete()
            except: pass
            logger.error(f"Ошибка фото: {str(e)[:100]}")
            await update.message.reply_text("❌ Ошибка генерации.")
        return
    
    # Текстовая модель
    if not can_request(user_id):
        await update.message.reply_text(
            f"🚫 Лимит NeBlock AI V1 исчерпан!\n"
            f"📊 {user.get('requests_today', 0)}/{DAILY_LIMIT + user.get('extra_requests', 0)}",
            reply_markup=limit_reached_keyboard()
        )
        return
    
    msg = await update.message.reply_text("💬 NeBlock AI V1 генерирует ответ...")
    await update.message.chat.send_action("typing")
    
    try:
        response = client.responses.create(prompt={"id": PROMPT_ID}, input=text)
        answer = response.output_text
        add_request(user_id)
        await msg.delete()
        
        if answer:
            rem = remaining(user_id)
            used = user.get("requests_today", 0) + 1
            total = DAILY_LIMIT + user.get("extra_requests", 0)
            footer = f"\n\n━━━━━━━━━━━━━━━━\n💬 NeBlock AI V1 | 📊 {used}/{total} | Осталось: {rem}"
            for i in range(0, len(answer), 4000):
                chunk = answer[i:i+4000]
                await update.message.reply_text(chunk + footer if i == 0 else chunk)
        else:
            await update.message.reply_text("🤷 Пустой ответ")
    except Exception as e:
        try: await msg.delete()
        except: pass
        await update.message.reply_text("❌ Ошибка.")

# ═══════════════════════════════════════════
# 🚀 Запуск
# ═══════════════════════════════════════════

def main():
    print("🧠 NeBlock AI (V1 + Images V1)")
    
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
