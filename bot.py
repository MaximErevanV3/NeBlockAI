import openai
import base64
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import logging
import os
import json
import random
import re
from datetime import datetime, timedelta

# ═══════════════════════════════════════════
# 🧠 NeBlock AI - Конфигурация
# ═══════════════════════════════════════════

TELEGRAM_TOKEN = "8700124191:AAE6qSSouLjlDxPWwoFObJORMbDotsby9co"
YANDEX_API_KEY = "AQVNy7Dm-dvQRzejHvH0383oHTZhhW2fda95I558"
YANDEX_FOLDER = "b1guk4h3j9t48lsjl6sq"
PROMPT_ID = "fvt621uiq1fftiu5qomu"
IMAGE_MODEL = "art://b1guk4h3j9t48lsjl6sq/aliceai-image-art-3.0/latest"

# Лимиты для ЛС
DAILY_LIMIT = 5
IMAGE_DAILY_LIMIT = 3

# Лимиты для чатов (больше)
CHAT_DAILY_LIMIT = 15
CHAT_IMAGE_LIMIT = 10

DATA_FILE = "users.json"
PROMO_FILE = "promos.json"
ADMIN_IDS = [1671403667]
START_BONUS = 50
DAILY_BONUS_MIN = 5
DAILY_BONUS_MAX = 15
REFERRAL_BONUS = 25
INVITED_BONUS = 10

DISCLAIMER = "\n\n━━━━━━━━━━━━━━━━\n⚠️ ИИ может ошибаться. Только для справки."

BLOCKED_WORDS = [
    r'\b(?:взлом|взломать|хак|hack|crack|warez|кряк)\b',
    r'\b(?:наркотик|drugs|наркота|спайс|соль|героин|кокаин|метамфетамин)\b',
    r'\b(?:оружие|weapon|gun|бомба|bomb|взрывчатка|explosive)\b',
    r'\b(?:дет[иь] порно|child porn|cp |педофил|pedo)\b',
    r'\b(?:уби[йт]|убью|kill|murder|зака[зж]|hitman|киллер)\b',
    r'\b(?:террор|terror|теракт|attack|ата[кч])\b',
    r'\b(?:суицид|suicide|самоубий|повес[иь])',
    r'\b(?:расч?изм|racis|наци|nazi|фаши|fascis)\b',
    r'\b(?:оскорбл|обид[еь]|туп[ой]|дур[ао]|идиот|дебил)\b',
]
COMPILED_BLOCKED = [re.compile(w, re.IGNORECASE) for w in BLOCKED_WORDS]

SHOP_ITEMS = {
    # Текстовые запросы
    "extra5": {"name": "+5 запросов", "price": 10, "icon": "📦", "desc": "+5 текстовых запросов", "category": "text"},
    "extra10": {"name": "+10 запросов", "price": 18, "icon": "📦", "desc": "+10 текстовых запросов", "category": "text"},
    "unlimited_1h": {"name": "Безлимит текст 1ч", "price": 30, "icon": "♾️", "desc": "Безлимит текстовых запросов на 1 час", "category": "text"},
    "unlimited_24h": {"name": "Безлимит текст 24ч", "price": 100, "icon": "♾️", "desc": "Безлимит текстовых запросов на 24 часа", "category": "text"},
    "unlimited_7d": {"name": "Безлимит текст 7д", "price": 500, "icon": "♾️", "desc": "Безлимит текстовых запросов на 7 дней", "category": "text"},
    # Генерации фото
    "image1": {"name": "1 генерация фото", "price": 15, "icon": "🎨", "desc": "1 генерация изображения", "category": "image"},
    "image5": {"name": "5 генераций фото", "price": 60, "icon": "🎨", "desc": "5 генераций изображений", "category": "image"},
    "image_unlimited_1h": {"name": "Безлимит фото 1ч", "price": 50, "icon": "♾️", "desc": "Безлимит генераций фото на 1 час", "category": "image"},
    # Для чатов
    "chat_extra10": {"name": "+10 запросов в чатах", "price": 15, "icon": "👥", "desc": "+10 текстовых запросов в группах", "category": "chat"},
    "chat_extra20": {"name": "+20 запросов в чатах", "price": 25, "icon": "👥", "desc": "+20 текстовых запросов в группах", "category": "chat"},
    "chat_unlimited_1h": {"name": "Безлимит чат 1ч", "price": 40, "icon": "♾️", "desc": "Безлимит в чатах на 1 час", "category": "chat"},
}

FAQ_TEXT = """
📚 ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ
━━━━━━━━━━━━━━━━━━━━

❓ Что такое NeBlock AI?
Платформа с ИИ-моделями в Telegram:
• NeBlock AI V1 — отвечает на вопросы, пишет код
• NeBlock Images V1 — генерирует изображения

❓ Бот работает в группах?
Да! Добавь бота в чат и пиши @имя_бота вопрос. Также по ключевым словам: бот, нейробот, AI.
В чатах увеличенные лимиты: 15 текстовых и 10 фото в день!

❓ Какие лимиты?
• ЛС: 5 вопросов + 3 фото/день
• Чаты: 15 вопросов + 10 фото/день
Можно купить дополнительные запросы в Магазине.

❓ Как переключаться между моделями?
Кнопки «💬 NeBlock AI V1» или «🎨 NeBlock Images V1».

❓ Что такое NeBlock Tokens?
Внутренняя валюта для покупок в Магазине. Не продаётся за деньги.

❓ Как заработать токены?
• Ежедневный бонус: 5-15 токенов
• Рефералы: +25 тебе, +10 другу
• Стартовый бонус: 50 токенов
• Промокоды от администратора

❓ 🆕 Как работает NeBlock Images V1?
Опиши что нарисовать — модель создаст изображение за 10-30 секунд.

❓ Когда сбрасываются лимиты?
Каждый день в 00:00 по Москве.

⚠️ ИИ может ошибаться. Все ответы только для справки.
⚠️ Запрещённый контент не обрабатывается.
"""

MODELS_INFO = """
🧠 МОДЕЛИ NeBlock AI
━━━━━━━━━━━━━━━━━━━━

💬 NeBlock AI V1
Текстовая модель для ответов на вопросы, помощи с кодом, объяснения тем и переводов.

🎨 NeBlock Images V1 🆕
Модель для генерации изображений по текстовому описанию.

👥 Поддержка чатов:
• @бот вопрос — бот ответит
• Ключевые слова: бот, нейробот, AI
• Увеличенные лимиты для групп!

⚠️ ИИ может ошибаться. Только для справки.

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
        "chat_requests_today": 0, "extra_chat_requests": 0,
        "unlimited_until": None, "image_unlimited_until": None, "chat_unlimited_until": None,
        "last_request": None, "total_requests": 0, "total_images": 0,
        "reset_date": datetime.now().strftime("%Y-%m-%d"),
        "tokens": START_BONUS, "daily_bonus_claimed": None,
        "daily_bonus_streak": 0, "last_bonus_date": None,
        "referral_code": "".join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(8)),
        "referred_by": None, "referrals": 0, "earned_tokens": 0, "spent_tokens": 0,
        "used_promos": [], "waiting_for_image": False, "current_model": "text",
        "warnings": 0, "muted_until": None,
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
        users[uid]["chat_requests_today"] = 0
        users[uid]["extra_chat_requests"] = 0
        users[uid]["reset_date"] = today
        save_users(users)
    
    return users[uid]

def add_request(user_id, chat_type="private"):
    users = load_users()
    uid = str(user_id)
    if uid in users:
        if chat_type in ["group", "supergroup"]:
            users[uid]["chat_requests_today"] = users[uid].get("chat_requests_today", 0) + 1
        else:
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

def can_request(user_id, chat_type="private"):
    user = get_user(user_id)
    
    # Безлимит для ЛС
    if chat_type == "private" and user.get("unlimited_until"):
        try:
            if datetime.now() < datetime.fromisoformat(user["unlimited_until"]): return True
        except: pass
    
    # Безлимит для чатов
    if chat_type in ["group", "supergroup"] and user.get("chat_unlimited_until"):
        try:
            if datetime.now() < datetime.fromisoformat(user["chat_unlimited_until"]): return True
        except: pass
    
    if chat_type in ["group", "supergroup"]:
        return user.get("chat_requests_today", 0) < (CHAT_DAILY_LIMIT + user.get("extra_chat_requests", 0))
    else:
        return user.get("requests_today", 0) < (DAILY_LIMIT + user.get("extra_requests", 0))

def can_image_request(user_id):
    user = get_user(user_id)
    if user.get("image_unlimited_until"):
        try:
            if datetime.now() < datetime.fromisoformat(user["image_unlimited_until"]): return True
        except: pass
    return user.get("image_requests_today", 0) < (IMAGE_DAILY_LIMIT + user.get("extra_image_requests", 0))

def remaining(user_id, chat_type="private"):
    user = get_user(user_id)
    
    if chat_type == "private" and user.get("unlimited_until"):
        try:
            if datetime.now() < datetime.fromisoformat(user["unlimited_until"]): return "безлимит"
        except: pass
    
    if chat_type in ["group", "supergroup"] and user.get("chat_unlimited_until"):
        try:
            if datetime.now() < datetime.fromisoformat(user["chat_unlimited_until"]): return "безлимит"
        except: pass
    
    if chat_type in ["group", "supergroup"]:
        return max(0, CHAT_DAILY_LIMIT + user.get("extra_chat_requests", 0) - user.get("chat_requests_today", 0))
    else:
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

def moderate_content(text):
    for pattern in COMPILED_BLOCKED:
        if pattern.search(text): return False, "Содержит запрещённый контент"
    return True, None

def is_user_muted(user_id):
    user = get_user(user_id)
    muted = user.get("muted_until")
    if muted:
        try:
            if datetime.now() < datetime.fromisoformat(muted): return True
        except: pass
    return False

def warn_user(user_id):
    users = load_users()
    uid = str(user_id)
    users[uid]["warnings"] = users[uid].get("warnings", 0) + 1
    if users[uid]["warnings"] >= 3:
        users[uid]["muted_until"] = (datetime.now() + timedelta(hours=1)).isoformat()
        users[uid]["warnings"] = 0
        save_users(users)
        return True, "Заблокирован на 1 час"
    save_users(users)
    return False, f"Предупреждение {users[uid]['warnings']}/3"

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
    text_items = [item for item in SHOP_ITEMS.items() if item[1]["category"] == "text"]
    image_items = [item for item in SHOP_ITEMS.items() if item[1]["category"] == "image"]
    chat_items = [item for item in SHOP_ITEMS.items() if item[1]["category"] == "chat"]
    
    keyboard.append([InlineKeyboardButton("── 💬 NeBlock AI V1 (ЛС) ──", callback_data="none")])
    for item_id, item in text_items:
        keyboard.append([InlineKeyboardButton(f"{item['icon']} {item['name']} — {item['price']} токенов", callback_data=f"buy_{item_id}")])
    
    keyboard.append([InlineKeyboardButton("── 👥 Чаты и группы ──", callback_data="none")])
    for item_id, item in chat_items:
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

def limit_reached_keyboard():
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
    chat_type = update.effective_chat.type
    
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
    
    if chat_type in ["group", "supergroup"]:
        await update.message.reply_text(
            f"🧠 NeBlock AI активирован в чате!\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 Лимиты чата: {CHAT_DAILY_LIMIT} вопросов + {CHAT_IMAGE_LIMIT} фото/день\n"
            f"Пишите: @{context.bot.username} ваш вопрос\n"
            f"Или: бот, нейробот, AI — и ваш вопрос\n"
            f"🛒 /shop — магазин запросов для чата\n"
            f"{DISCLAIMER}"
        )
        return
    
    await update.message.reply_text(
        f"🧠 NeBlock AI\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💬 NeBlock AI V1 — ответы на вопросы\n"
        f"🎨 NeBlock Images V1 🆕 — генерация фото\n"
        f"👥 Работает в чатах\n\n"
        f"📊 Лимиты (ЛС):\n"
        f"   • Текст: {DAILY_LIMIT} запросов/день\n"
        f"   • Фото: {IMAGE_DAILY_LIMIT} генераций/день\n"
        f"📊 Лимиты (Чаты):\n"
        f"   • Текст: {CHAT_DAILY_LIMIT} запросов/день\n"
        f"   • Фото: {CHAT_IMAGE_LIMIT} генераций/день\n"
        f"💰 Баланс: {user.get('tokens', 0)} NeBlock Tokens\n\n"
        f"👇 Выбери модель:\n"
        f"{DISCLAIMER}",
        reply_markup=main_reply_keyboard()
    )

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
        f"💬 Запросов: {sum(u.get('total_requests', 0) for u in users.values())}\n"
        f"🎨 Изображений: {sum(u.get('total_images', 0) for u in users.values())}\n"
        f"⚠️ Предупреждений: {sum(u.get('warnings', 0) for u in users.values())}\n"
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
            f"📊 Осталось запросов: {remaining(user_id)}\n"
            f"{DISCLAIMER}"
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
            f"⏳ 10-30 секунд\n{DISCLAIMER}"
        )
        return True
    
    if text == "👤 Профиль":
        await update.message.reply_text(get_full_profile(user_id), reply_markup=main_menu())
        return True
    
    if text == "🛒 Магазин":
        await update.message.reply_text(
            f"🛒 Магазин\n━━━━━━━━━━━━━━━━\n💰 Баланс: {get_tokens(user_id)} токенов\n\n"
            f"💬 ЛС | 👥 Чаты | 🎨 Фото | ♾️ Безлимиты\n{DISCLAIMER}",
            reply_markup=shop_keyboard()
        )
        return True
    
    if text == "💰 Заработать":
        await update.message.reply_text(
            f"💰 Заработок\n━━━━━━━━━━━━━━━━\n💎 Баланс: {get_tokens(user_id)}\n\n"
            f"🎁 Бонус: {DAILY_BONUS_MIN}-{DAILY_BONUS_MAX} токенов/день\n"
            f"👥 Рефералы: +{REFERRAL_BONUS} тебе, +{INVITED_BONUS} другу\n"
            f"🎟 Промокоды",
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
    
    warnings = user.get("warnings", 0)
    muted = "Нет" if not is_user_muted(user_id) else "Да"
    
    return (
        f"👤 Личный кабинет\n━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🆔 ID: {user_id}\n📅 Регистрация: {joined}\n"
        f"🔮 Модель: {current_model}\n\n"
        f"💰 Баланс: {user.get('tokens', 0)} токенов\n"
        f"💎 Заработано: {user.get('earned_tokens', 0)}\n"
        f"💸 Потрачено: {user.get('spent_tokens', 0)}\n\n"
        f"💬 NeBlock AI V1 (ЛС):\n"
        f"   • Сегодня: {user.get('requests_today', 0)}/{DAILY_LIMIT + user.get('extra_requests', 0)}\n"
        f"   • Всего: {user.get('total_requests', 0)}\n"
        f"   • Безлимит: {format_unlimited(user.get('unlimited_until'))}\n\n"
        f"👥 Чаты и группы:\n"
        f"   • Сегодня: {user.get('chat_requests_today', 0)}/{CHAT_DAILY_LIMIT + user.get('extra_chat_requests', 0)}\n"
        f"   • Безлимит: {format_unlimited(user.get('chat_unlimited_until'))}\n\n"
        f"🎨 NeBlock Images V1:\n"
        f"   • Сегодня: {user.get('image_requests_today', 0)}/{IMAGE_DAILY_LIMIT + user.get('extra_image_requests', 0)}\n"
        f"   • Всего: {user.get('total_images', 0)}\n"
        f"   • Безлимит: {format_unlimited(user.get('image_unlimited_until'))}\n\n"
        f"🛡 Модерация:\n"
        f"   • Предупреждений: {warnings}/3\n"
        f"   • Заблокирован: {muted}\n\n"
        f"🔥 Серия бонусов: {user.get('daily_bonus_streak', 0)} дней\n"
        f"👥 Рефералов: {user.get('referrals', 0)}\n"
        f"🕐 Активность: {last}\n"
        f"{DISCLAIMER}"
    )

# ═══════════════════════════════════════════
# 🔘 Inline кнопки
# ═══════════════════════════════════════════

async def inline_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if data == "none": return
    
    if data == "menu":
        await query.edit_message_text(f"🧠 NeBlock AI\n💰 {get_tokens(user_id)} токенов\n{DISCLAIMER}", reply_markup=main_menu())
    elif data == "about":
        await query.edit_message_text(
            "ℹ️ NeBlock AI\n━━━━━━━━━━━━━━━━\n\n"
            "💬 NeBlock AI V1 — текстовая модель\n"
            "🎨 NeBlock Images V1 — генерация фото 🆕\n"
            "👥 Поддержка чатов (отдельные лимиты)\n"
            "🛡 Умная модерация\n\n"
            f"{DISCLAIMER}",
            reply_markup=back_button()
        )
    elif data == "models":
        await query.edit_message_text(MODELS_INFO, reply_markup=back_button())
    elif data == "stats":
        user = get_user(user_id)
        await query.edit_message_text(
            f"📊 Статистика\n━━━━━━━━━━━━━━━━\n\n"
            f"💬 Запросов в ЛС: {user.get('requests_today', 0)}/{DAILY_LIMIT + user.get('extra_requests', 0)}\n"
            f"👥 Запросов в чатах: {user.get('chat_requests_today', 0)}/{CHAT_DAILY_LIMIT + user.get('extra_chat_requests', 0)}\n"
            f"🎨 Фото: {user.get('image_requests_today', 0)}/{IMAGE_DAILY_LIMIT + user.get('extra_image_requests', 0)}\n"
            f"💰 Баланс: {user.get('tokens', 0)}",
            reply_markup=back_button()
        )
    elif data == "shop":
        await query.edit_message_text(
            f"🛒 Магазин\n💰 {get_tokens(user_id)} токенов\n💬 ЛС | 👥 Чаты | 🎨 Фото\n{DISCLAIMER}",
            reply_markup=shop_keyboard()
        )
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
            await query.answer(f"❌ Недостаточно токенов!\nНужно {item['price']}, у вас {tokens}", show_alert=True)
            return
        remove_tokens(user_id, item["price"])
        users = load_users()
        uid = str(user_id)
        
        if item_id == "extra5": users[uid]["extra_requests"] += 5
        elif item_id == "extra10": users[uid]["extra_requests"] += 10
        elif item_id == "image1": users[uid]["extra_image_requests"] += 1
        elif item_id == "image5": users[uid]["extra_image_requests"] += 5
        elif item_id == "chat_extra10": users[uid]["extra_chat_requests"] += 10
        elif item_id == "chat_extra20": users[uid]["extra_chat_requests"] += 20
        elif item_id == "unlimited_1h": users[uid]["unlimited_until"] = (datetime.now() + timedelta(hours=1)).isoformat()
        elif item_id == "unlimited_24h": users[uid]["unlimited_until"] = (datetime.now() + timedelta(hours=24)).isoformat()
        elif item_id == "unlimited_7d": users[uid]["unlimited_until"] = (datetime.now() + timedelta(days=7)).isoformat()
        elif item_id == "image_unlimited_1h": users[uid]["image_unlimited_until"] = (datetime.now() + timedelta(hours=1)).isoformat()
        elif item_id == "chat_unlimited_1h": users[uid]["chat_unlimited_until"] = (datetime.now() + timedelta(hours=1)).isoformat()
        
        save_users(users)
        await query.answer(f"✅ {item['name']} активирован!", show_alert=True)
        await query.edit_message_text(
            f"✅ Покупка успешна!\n━━━━━━━━━━━━━━━━\n"
            f"{item['icon']} {item['name']}\n📝 {item['desc']}\n"
            f"💰 Потрачено: {item['price']} токенов\n💎 Остаток: {get_tokens(user_id)}",
            reply_markup=back_button()
        )
    elif data.startswith("buy_"):
        item_id = data.replace("buy_", "")
        item = SHOP_ITEMS.get(item_id)
        if not item: return
        tokens = get_tokens(user_id)
        can = "✅ Достаточно средств" if tokens >= item["price"] else "❌ Недостаточно средств"
        cat_names = {"text": "NeBlock AI V1 (ЛС)", "image": "NeBlock Images V1", "chat": "Чаты и группы"}
        model_name = cat_names.get(item["category"], "")
        await query.edit_message_text(
            f"🛒 Подтверждение покупки\n━━━━━━━━━━━━━━━━\n\n"
            f"{item['icon']} {item['name']}\n📝 Для: {model_name}\n📝 {item['desc']}\n"
            f"💰 Цена: {item['price']} токенов\n💎 Баланс: {tokens}\n{can}\n\nПодтвердите:",
            reply_markup=confirm_keyboard(item_id)
        )

# ═══════════════════════════════════════════
# 💬 Обработчик сообщений
# ═══════════════════════════════════════════

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip() if update.message.text else ""
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type
    bot_username = context.bot.username
    
    if is_user_muted(user_id):
        await update.message.reply_text("🚫 Вы временно заблокированы за нарушения.")
        return
    
    is_clean, mod_reason = moderate_content(text)
    if not is_clean:
        muted_now, warn_msg = warn_user(user_id)
        await update.message.reply_text(
            f"⚠️ {mod_reason}\n{warn_msg}\n\n"
            f"{'🚫 Заблокирован на 1 час' if muted_now else '⚠️ Нарушение правил'}"
        )
        logger.warning(f"Модерация: user={user_id}, text={text[:50]}, action={warn_msg}")
        return
    
    if chat_type == "private":
        if await reply_button_handler(update, context):
            return
    
    # Обработка чатов
    if chat_type in ["group", "supergroup"]:
        mention = f"@{bot_username}"
        keywords = ["бот", "нейробот", "бот ", "нейросеть", "ai ", "AI "]
        
        should_respond = False
        clean_text = text
        
        if mention in text:
            should_respond = True
            clean_text = text.replace(mention, "").strip()
        
        if not should_respond:
            for kw in keywords:
                if text.lower().startswith(kw.lower()):
                    should_respond = True
                    clean_text = text[len(kw):].strip()
                    break
        
        if not should_respond:
            return
        
        text = clean_text
        if not text:
            await update.message.reply_text(
                f"🧠 NeBlock AI слушает!\nНапишите: @{bot_username} ваш вопрос",
                reply_to_message_id=update.message.message_id
            )
            return
    
    user = get_user(user_id)
    current_model = user.get("current_model", "text")
    
    # Промокод
    if context.user_data.get("waiting_promo"):
        context.user_data["waiting_promo"] = False
        success, result = use_promo(user_id, text)
        await update.message.reply_text(
            f"🎟 +{result} токенов!\n💎 {get_tokens(user_id)}" if success else f"❌ {result}",
            reply_to_message_id=update.message.message_id if chat_type != "private" else None
        )
        return
    
    # Модель изображений
    if current_model == "image" or user.get("waiting_for_image"):
        users = load_users()
        users[str(user_id)]["waiting_for_image"] = False
        save_users(users)
        
        if not can_image_request(user_id):
            await update.message.reply_text(
                f"🚫 Лимит генераций исчерпан!\n"
                f"📊 {user.get('image_requests_today', 0)}/{IMAGE_DAILY_LIMIT + user.get('extra_image_requests', 0)}\n"
                f"🛒 Купи генерации в Магазине",
                reply_to_message_id=update.message.message_id if chat_type != "private" else None
            )
            return
        
        msg = await update.message.reply_text(
            "🎨 NeBlock Images V1 генерирует...\n⏳ 10-30 секунд",
            reply_to_message_id=update.message.message_id if chat_type != "private" else None
        )
        
        try:
            image_bytes, error = await generate_image(text)
            if image_bytes:
                add_image_request(user_id)
                await msg.delete()
                rem = image_remaining(user_id)
                await update.message.reply_photo(
                    photo=image_bytes,
                    caption=f"🎨 NeBlock Images V1\n📝 {text[:200]}\n\n📊 Осталось: {rem}\n{DISCLAIMER}",
                    reply_to_message_id=update.message.message_id if chat_type != "private" else None
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
    if not can_request(user_id, chat_type):
        if chat_type in ["group", "supergroup"]:
            limit_msg = f"🚫 Лимит чата исчерпан!\n📊 {user.get('chat_requests_today', 0)}/{CHAT_DAILY_LIMIT + user.get('extra_chat_requests', 0)}\n🛒 Купи запросы: /shop"
        else:
            limit_msg = f"🚫 Лимит исчерпан!\n📊 {user.get('requests_today', 0)}/{DAILY_LIMIT + user.get('extra_requests', 0)}"
        
        await update.message.reply_text(
            limit_msg,
            reply_markup=limit_reached_keyboard() if chat_type == "private" else None,
            reply_to_message_id=update.message.message_id if chat_type != "private" else None
        )
        return
    
    msg = await update.message.reply_text(
        "💬 NeBlock AI V1 генерирует ответ...",
        reply_to_message_id=update.message.message_id if chat_type != "private" else None
    )
    
    try:
        response = client.responses.create(prompt={"id": PROMPT_ID}, input=text)
        answer = response.output_text
        add_request(user_id, chat_type)
        await msg.delete()
        
        if answer:
            rem = remaining(user_id, chat_type)
            if chat_type in ["group", "supergroup"]:
                used = user.get("chat_requests_today", 0) + 1
                total = CHAT_DAILY_LIMIT + user.get("extra_chat_requests", 0)
                model_name = "👥 Чат"
            else:
                used = user.get("requests_today", 0) + 1
                total = DAILY_LIMIT + user.get("extra_requests", 0)
                model_name = "💬 NeBlock AI V1"
            
            footer = f"\n\n━━━━━━━━━━━━━━━━\n{model_name} | 📊 {used}/{total} | Осталось: {rem}\n{DISCLAIMER}"
            
            for i in range(0, len(answer), 4000):
                chunk = answer[i:i+4000]
                await update.message.reply_text(
                    chunk + footer if i == 0 else chunk,
                    reply_to_message_id=update.message.message_id if chat_type != "private" else None
                )
        else:
            await update.message.reply_text(f"🤷 Пустой ответ\n{DISCLAIMER}")
    except Exception as e:
        try: await msg.delete()
        except: pass
        await update.message.reply_text(f"❌ Ошибка.\n{DISCLAIMER}")

# ═══════════════════════════════════════════
# 🚀 Запуск
# ═══════════════════════════════════════════

def main():
    print("🧠 NeBlock AI (V1 + Images V1 + Groups + Shop)")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("shop", lambda u, c: u.message.reply_text(f"🛒 Магазин\n💰 {get_tokens(u.effective_user.id)} токенов", reply_markup=shop_keyboard())))
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
