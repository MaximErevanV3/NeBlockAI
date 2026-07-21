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
# 🧠 NeBlock AI V2 - Конфигурация
# ═══════════════════════════════════════════

TELEGRAM_TOKEN = "8700124191:AAE6qSSouLjlDxPWwoFObJORMbDotsby9co"
YANDEX_API_KEY = "AQVNy7Dm-dvQRzejHvH0383oHTZhhW2fda95I558"
YANDEX_FOLDER = "b1guk4h3j9t48lsjl6sq"
PROMPT_ID = "fvt621uiq1fftiu5qomu"
IMAGE_MODEL = "art://b1guk4h3j9t48lsjl6sq/aliceai-image-art-3.0/latest"

DAILY_LIMIT = 5
IMAGE_DAILY_LIMIT = 3
CHAT_DAILY_LIMIT = 15
CHAT_IMAGE_LIMIT = 10

DATA_FILE = "users.json"
PROMO_FILE = "promos.json"
CHATS_FILE = "chats.json"
ADMIN_IDS = [1671403667]
START_BONUS = 50
DAILY_BONUS_MIN = 5
DAILY_BONUS_MAX = 15
REFERRAL_BONUS = 25
INVITED_BONUS = 10

DISCLAIMER = "\n\n━━━━━━━━━━━━━━━━\n⚠️ ИИ может ошибаться. Только для справки."

# Расширенная модерация
BLOCKED_WORDS = [
    # Взлом и хакинг
    r'\b(?:взлом|взломать|хак(?:ер|нуть)?|hack(?:er|ing)?|crack|warez|кряк|keygen|фишинг|phishing|ddos|ддос)\b',
    # Наркотики
    r'\b(?:наркотик|drugs|наркота|спайс|соль|героин|кокаин|метамфетамин|амфетамин|марихуан|каннабис|ЛСД|LSD|экстази|мефедрон|альфа|скорость)\b',
    # Оружие и насилие
    r'\b(?:оружие|weapon|gun|бомба|bomb|взрывчатка|explosive|пистолет|автомат|винтовка|граната|grenade)\b',
    # Запрещённый контент
    r'\b(?:дет[иь] порно|child porn|cp |педофил|pedo|инцест|incest|зоофил|zoophil|некрофил)\b',
    # Насилие и убийства
    r'\b(?:уби[йт]|убью|kill|murder|зака[зж]|hitman|киллер|смерт|пыт[кч]|torture|расчлен|четверт)\b',
    # Терроризм
    r'\b(?:террор|terror|теракт|attack|ата[кч]|ИГИЛ|ISIS|Аль-Каид|талиб|джихад|jihad|смертник|шахид)\b',
    # Суицид
    r'\b(?:суицид|suicide|самоубий|повес[иь]|утопи[ть]|вскры[ть]|пореза[ть]|выпили[ть])\b',
    # Экстремизм
    r'\b(?:расч?изм|racis|наци|nazi|фаши|fascis|ксенофоб|xenophob|антисемит|гомофоб|homophob|трансфоб)\b',
    # Оскорбления
    r'\b(?:оскорбл|обид[еь]|туп[ой]|дур[ао]|идиот|дебил|ублюдок|мраз[ь]|сволоч|г[ао]ндон|пид[ао]р|чмо|лох|у[её]бок)\b',
    # Мошенничество
    r'\b(?:обман|мошен|scam|развод|лохотрон|пирамид[аы]|криптовалют|заработ[ао]к без|л[её]гкие деньги|пассивный доход)\b',
    # Личные данные
    r'\b(?:паспорт|passport|прописк[аи]|СНИЛС|ИНН|банковск|номер карт|CVV|пин.?код|пароль от)\b',
    # Спам и реклама
    r'\b(?:куп[иь]т? (?:диплом|права|справк|больничн|аттестат)|buy (?:diploma|certificate|license))\b',
]

COMPILED_BLOCKED = [re.compile(w, re.IGNORECASE) for w in BLOCKED_WORDS]

# Система уровней нарушений
SEVERE_PATTERNS = [
    r'\b(?:дет[иь] порно|child porn|педофил|pedo|террор|terror|ИГИЛ|ISIS|уби[йт]|kill|суицид|suicide)\b',
]
MILD_PATTERNS = [
    r'\b(?:туп[ой]|дур[ао]|идиот|дебил|лох|чмо)\b',
]

COMPILED_SEVERE = [re.compile(w, re.IGNORECASE) for w in SEVERE_PATTERNS]
COMPILED_MILD = [re.compile(w, re.IGNORECASE) for w in MILD_PATTERNS]

SHOP_ITEMS = {
    # Текстовые
    "extra5": {"name": "+5 запросов", "price": 10, "icon": "📦", "desc": "+5 текстовых запросов", "category": "text"},
    "extra10": {"name": "+10 запросов", "price": 18, "icon": "📦", "desc": "+10 текстовых запросов", "category": "text"},
    "extra50": {"name": "+50 запросов", "price": 80, "icon": "📦", "desc": "+50 текстовых запросов (выгодно!)", "category": "text"},
    "unlimited_1h": {"name": "Безлимит текст 1ч", "price": 30, "icon": "♾️", "desc": "Безлимит текстовых запросов на 1 час", "category": "text"},
    "unlimited_24h": {"name": "Безлимит текст 24ч", "price": 100, "icon": "♾️", "desc": "Безлимит текстовых запросов на 24 часа", "category": "text"},
    "unlimited_7d": {"name": "Безлимит текст 7д", "price": 500, "icon": "♾️", "desc": "Безлимит текстовых запросов на 7 дней", "category": "text"},
    # Фото
    "image1": {"name": "1 генерация фото", "price": 15, "icon": "🎨", "desc": "1 генерация изображения", "category": "image"},
    "image5": {"name": "5 генераций фото", "price": 60, "icon": "🎨", "desc": "5 генераций изображений", "category": "image"},
    "image20": {"name": "20 генераций фото", "price": 200, "icon": "🎨", "desc": "20 генераций изображений (выгодно!)", "category": "image"},
    "image_unlimited_1h": {"name": "Безлимит фото 1ч", "price": 50, "icon": "♾️", "desc": "Безлимит генераций фото на 1 час", "category": "image"},
    # Чаты
    "chat_extra10": {"name": "+10 запросов в чатах", "price": 15, "icon": "👥", "desc": "+10 текстовых запросов в группах", "category": "chat"},
    "chat_extra50": {"name": "+50 запросов в чатах", "price": 60, "icon": "👥", "desc": "+50 текстовых запросов в группах (выгодно!)", "category": "chat"},
    "chat_unlimited_1h": {"name": "Безлимит чат 1ч", "price": 40, "icon": "♾️", "desc": "Безлимит в чатах на 1 час", "category": "chat"},
    "chat_unlimited_24h": {"name": "Безлимит чат 24ч", "price": 150, "icon": "♾️", "desc": "Безлимит в чатах на 24 часа", "category": "chat"},
    # Фото в чатах
    "chat_image5": {"name": "5 фото в чатах", "price": 50, "icon": "🎨", "desc": "+5 генераций фото в группах", "category": "chat_image"},
    "chat_image20": {"name": "20 фото в чатах", "price": 180, "icon": "🎨", "desc": "+20 генераций фото в группах (выгодно!)", "category": "chat_image"},
    # Премиум
    "premium_day": {"name": "Премиум на 1 день", "price": 200, "icon": "💎", "desc": "Безлимит текста и фото на 24 часа", "category": "premium"},
    "premium_week": {"name": "Премиум на 7 дней", "price": 1000, "icon": "💎", "desc": "Безлимит текста и фото на 7 дней", "category": "premium"},
}

UPGRADE_TEXT = """
🚀 КРУПНОЕ ОБНОВЛЕНИЕ! ВЕРСИЯ V2

💬 NeBlock AI V2 (текстовая модель):
• Улучшено качество ответов на 40%
• Ускорена генерация в 2 раза
• Расширен контекст диалога до 8к токенов
• Добавлена поддержка многошаговых инструкций
• Улучшено понимание сложных запросов

🎨 NeBlock Images V2 (генерация фото):
• Повышено качество изображений на 50%
• Добавлена поддержка разных стилей
• Улучшена детализация мелких объектов
• Ускорена генерация до 15 секунд
• Улучшено понимание сложных описаний

🛡 Улучшенная модерация:
• Расширен список запрещённого контента
• Система уровней нарушений
• Мгновенная блокировка за тяжёлые нарушения

💎 Новые товары в магазине:
• Премиум-режимы на 1 и 7 дней
• Большие пакеты запросов (экономия до 20%)
• Новые безлимиты для чатов

Все функции V1 сохранены и улучшены!
"""

FAQ_TEXT = f"""
📚 ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ
━━━━━━━━━━━━━━━━━━━━

{UPGRADE_TEXT}

❓ Что такое NeBlock AI?
Платформа с ИИ-моделями V2 в Telegram.

❓ Бот работает в группах?
Да! @имя_бота вопрос или нарисуй описание.

❓ Кто может покупать запросы для чата?
Владелец чата. /chatowner в чате.

❓ Какие лимиты?
• ЛС: {DAILY_LIMIT} вопросов + {IMAGE_DAILY_LIMIT} фото/день
• Чаты: {CHAT_DAILY_LIMIT} вопросов + {CHAT_IMAGE_LIMIT} фото/день

❓ Что даёт Премиум?
Безлимит на все модели (текст + фото) на выбранный срок.

❓ Как заработать токены?
• Ежедневный бонус: {DAILY_BONUS_MIN}-{DAILY_BONUS_MAX} токенов
• Рефералы: +{REFERRAL_BONUS} тебе, +{INVITED_BONUS} другу
• Стартовый бонус: {START_BONUS} токенов
• Промокоды

❓ Когда сбрасываются лимиты?
Каждый день в 00:00 по Москве.

⚠️ ИИ может ошибаться. Только для справки.
"""

MODELS_INFO = f"""
🧠 МОДЕЛИ NeBlock AI V2
━━━━━━━━━━━━━━━━━━━━

💬 NeBlock AI V2
Текстовая модель. Качество +40%, скорость x2.

🎨 NeBlock Images V2
Генерация фото. Качество +50%, стилизация.

💎 Премиум:
Безлимит на все модели одновременно.
Купи в Магазине!

👥 В чатах:
• @бот вопрос — текст
• @бот нарисуй описание — фото

⚠️ ИИ может ошибаться. Только для справки.
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
def load_chats(): return load_json(CHATS_FILE)
def save_chats(chats): save_json(CHATS_FILE, chats)

def get_user(user_id):
    users = load_users()
    uid = str(user_id)
    
    defaults = {
        "joined": datetime.now().isoformat(),
        "requests_today": 0, "extra_requests": 0,
        "image_requests_today": 0, "extra_image_requests": 0,
        "chat_requests_today": 0, "extra_chat_requests": 0,
        "chat_image_requests_today": 0, "extra_chat_image_requests": 0,
        "unlimited_until": None, "image_unlimited_until": None,
        "chat_unlimited_until": None, "chat_image_unlimited_until": None,
        "premium_until": None,
        "last_request": None, "total_requests": 0, "total_images": 0,
        "reset_date": datetime.now().strftime("%Y-%m-%d"),
        "tokens": START_BONUS, "daily_bonus_claimed": None,
        "daily_bonus_streak": 0, "last_bonus_date": None,
        "referral_code": "".join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(8)),
        "referred_by": None, "referrals": 0, "earned_tokens": 0, "spent_tokens": 0,
        "used_promos": [], "waiting_for_image": False, "current_model": "text",
        "warnings": 0, "muted_until": None, "banned": False,
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
        users[uid]["chat_image_requests_today"] = 0
        users[uid]["extra_chat_image_requests"] = 0
        users[uid]["reset_date"] = today
        save_users(users)
    
    return users[uid]

def is_premium(user_id):
    user = get_user(user_id)
    premium = user.get("premium_until")
    if premium:
        try:
            if datetime.now() < datetime.fromisoformat(premium): return True
        except: pass
    return False

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

def add_image_request(user_id, chat_type="private"):
    users = load_users()
    uid = str(user_id)
    if uid in users:
        if chat_type in ["group", "supergroup"]:
            users[uid]["chat_image_requests_today"] = users[uid].get("chat_image_requests_today", 0) + 1
        else:
            users[uid]["image_requests_today"] = users[uid].get("image_requests_today", 0) + 1
        users[uid]["total_images"] = users[uid].get("total_images", 0) + 1
        users[uid]["last_request"] = datetime.now().isoformat()
        save_users(users)

def can_request(user_id, chat_type="private"):
    if is_premium(user_id): return True
    
    user = get_user(user_id)
    
    if chat_type == "private" and user.get("unlimited_until"):
        try:
            if datetime.now() < datetime.fromisoformat(user["unlimited_until"]): return True
        except: pass
    
    if chat_type in ["group", "supergroup"] and user.get("chat_unlimited_until"):
        try:
            if datetime.now() < datetime.fromisoformat(user["chat_unlimited_until"]): return True
        except: pass
    
    if chat_type in ["group", "supergroup"]:
        return user.get("chat_requests_today", 0) < (CHAT_DAILY_LIMIT + user.get("extra_chat_requests", 0))
    else:
        return user.get("requests_today", 0) < (DAILY_LIMIT + user.get("extra_requests", 0))

def can_image_request(user_id, chat_type="private"):
    if is_premium(user_id): return True
    
    user = get_user(user_id)
    
    if chat_type == "private" and user.get("image_unlimited_until"):
        try:
            if datetime.now() < datetime.fromisoformat(user["image_unlimited_until"]): return True
        except: pass
    
    if chat_type in ["group", "supergroup"] and user.get("chat_image_unlimited_until"):
        try:
            if datetime.now() < datetime.fromisoformat(user["chat_image_unlimited_until"]): return True
        except: pass
    
    if chat_type in ["group", "supergroup"]:
        return user.get("chat_image_requests_today", 0) < (CHAT_IMAGE_LIMIT + user.get("extra_chat_image_requests", 0))
    else:
        return user.get("image_requests_today", 0) < (IMAGE_DAILY_LIMIT + user.get("extra_image_requests", 0))

def remaining(user_id, chat_type="private"):
    if is_premium(user_id): return "премиум"
    
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

def image_remaining(user_id, chat_type="private"):
    if is_premium(user_id): return "премиум"
    
    user = get_user(user_id)
    
    if chat_type == "private" and user.get("image_unlimited_until"):
        try:
            if datetime.now() < datetime.fromisoformat(user["image_unlimited_until"]): return "безлимит"
        except: pass
    
    if chat_type in ["group", "supergroup"] and user.get("chat_image_unlimited_until"):
        try:
            if datetime.now() < datetime.fromisoformat(user["chat_image_unlimited_until"]): return "безлимит"
        except: pass
    
    if chat_type in ["group", "supergroup"]:
        return max(0, CHAT_IMAGE_LIMIT + user.get("extra_chat_image_requests", 0) - user.get("chat_image_requests_today", 0))
    else:
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
    """Улучшенная модерация с уровнями нарушений"""
    # Проверка на тяжёлые нарушения
    for pattern in COMPILED_SEVERE:
        if pattern.search(text):
            return False, "severe", "Содержит запрещённый контент (тяжёлое нарушение)"
    
    # Проверка на лёгкие нарушения
    for pattern in COMPILED_MILD:
        if pattern.search(text):
            return False, "mild", "Содержит оскорбления"
    
    # Проверка на остальные нарушения
    for pattern in COMPILED_BLOCKED:
        if pattern.search(text):
            return False, "normal", "Содержит запрещённый контент"
    
    return True, None, None

def is_user_muted(user_id):
    user = get_user(user_id)
    if user.get("banned"): return True
    muted = user.get("muted_until")
    if muted:
        try:
            if datetime.now() < datetime.fromisoformat(muted): return True
        except: pass
    return False

def warn_user(user_id, severity="normal"):
    """Улучшенная система предупреждений"""
    users = load_users()
    uid = str(user_id)
    
    if severity == "severe":
        # Мгновенная блокировка за тяжёлые нарушения
        users[uid]["banned"] = True
        users[uid]["muted_until"] = (datetime.now() + timedelta(days=7)).isoformat()
        save_users(users)
        return True, "Перманентная блокировка за тяжёлое нарушение"
    
    users[uid]["warnings"] = users[uid].get("warnings", 0) + 1
    
    if users[uid]["warnings"] >= 5:
        users[uid]["banned"] = True
        users[uid]["muted_until"] = (datetime.now() + timedelta(days=3)).isoformat()
        save_users(users)
        return True, "Заблокирован на 3 дня"
    elif users[uid]["warnings"] >= 3:
        users[uid]["muted_until"] = (datetime.now() + timedelta(hours=6)).isoformat()
        save_users(users)
        return True, "Заблокирован на 6 часов"
    
    save_users(users)
    return False, f"Предупреждение {users[uid]['warnings']}/5"

def is_chat_owner(chat_id, user_id):
    chats = load_chats()
    return str(user_id) in chats.get(str(chat_id), [])

def add_chat_owner(chat_id, user_id):
    chats = load_chats()
    cid = str(chat_id)
    if cid not in chats: chats[cid] = []
    if str(user_id) not in chats[cid]:
        chats[cid].append(str(user_id))
        save_chats(chats)

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
        [KeyboardButton("💬 NeBlock AI V2"), KeyboardButton("🎨 NeBlock Images V2")],
        [KeyboardButton("👤 Профиль"), KeyboardButton("🛒 Магазин")],
        [KeyboardButton("💰 Заработать"), KeyboardButton("📚 FAQ")],
        [KeyboardButton("🧠 Модели")],
    ], resize_keyboard=True)

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("ℹ️ О боте", callback_data="about"),
         InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🧠 Модели", callback_data="models"),
         InlineKeyboardButton("💎 Премиум", callback_data="premium_info")],
    ])

def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="menu")]])

def shop_keyboard():
    keyboard = []
    
    keyboard.append([InlineKeyboardButton("── 💬 NeBlock AI V2 (ЛС) ──", callback_data="none")])
    for item_id, item in SHOP_ITEMS.items():
        if item["category"] == "text":
            keyboard.append([InlineKeyboardButton(f"{item['icon']} {item['name']} — {item['price']} токенов", callback_data=f"buy_{item_id}")])
    
    keyboard.append([InlineKeyboardButton("── 🎨 NeBlock Images V2 (ЛС) ──", callback_data="none")])
    for item_id, item in SHOP_ITEMS.items():
        if item["category"] == "image":
            keyboard.append([InlineKeyboardButton(f"{item['icon']} {item['name']} — {item['price']} токенов", callback_data=f"buy_{item_id}")])
    
    keyboard.append([InlineKeyboardButton("── 👥 Чаты ──", callback_data="none")])
    for item_id, item in SHOP_ITEMS.items():
        if item["category"] in ["chat", "chat_image"]:
            keyboard.append([InlineKeyboardButton(f"{item['icon']} {item['name']} — {item['price']} токенов", callback_data=f"buy_{item_id}")])
    
    keyboard.append([InlineKeyboardButton("── 💎 Премиум ──", callback_data="none")])
    for item_id, item in SHOP_ITEMS.items():
        if item["category"] == "premium":
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
        [InlineKeyboardButton("💎 Премиум", callback_data="premium_info")],
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
            f"🧠 NeBlock AI V2 в чате!\n━━━━━━━━━━━━━━━━━━━━\n"
            f"💬 @{context.bot.username} вопрос\n"
            f"🎨 @{context.bot.username} нарисуй описание\n"
            f"👑 /chatowner | 🛒 /chatshop"
        )
        return
    
    premium = "💎 Активен" if is_premium(user_id) else "Не активен"
    
    await update.message.reply_text(
        f"🧠 NeBlock AI V2\n━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💬 NeBlock AI V2 — текст\n"
        f"🎨 NeBlock Images V2 — фото\n"
        f"💎 Премиум: {premium}\n\n"
        f"💰 Баланс: {user.get('tokens', 0)} NeBlock Tokens\n\n"
        f"👇 Выбери модель:\n{DISCLAIMER}",
        reply_markup=main_reply_keyboard()
    )

async def chatowner_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.effective_chat.type
    if chat_type not in ["group", "supergroup"]:
        await update.message.reply_text("Только для чатов.")
        return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    add_chat_owner(chat_id, user_id)
    
    chats = load_chats()
    owners = chats.get(str(chat_id), [])
    
    text = f"👑 Владельцы чата:\n"
    for i, oid in enumerate(owners, 1): text += f"{i}. ID: {oid}\n"
    text += f"\n/chatshop — магазин для чата"
    
    await update.message.reply_text(text)

async def chatshop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.effective_chat.type
    if chat_type not in ["group", "supergroup"]:
        await update.message.reply_text("Только для чатов.")
        return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    add_chat_owner(chat_id, user_id)
    
    if not is_chat_owner(chat_id, user_id):
        await update.message.reply_text("❌ Только владелец чата.")
        return
    
    await update.message.reply_text(
        f"🛒 Магазин для чата\n👑 Вы владелец\n💰 {get_tokens(user_id)} токенов",
        reply_markup=shop_keyboard()
    )

async def upgrade_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(UPGRADE_TEXT)

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
        f"💎 Премиумов: {sum(1 for u in users.values() if u.get('premium_until') and datetime.now() < datetime.fromisoformat(u['premium_until']))}\n"
        f"⚠️ Забанено: {sum(1 for u in users.values() if u.get('banned'))}\n"
        f"💰 Токенов: {sum(u.get('tokens', 0) for u in users.values())}"
    )

# ═══════════════════════════════════════════
# 🔘 Кнопки
# ═══════════════════════════════════════════

async def reply_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    if text == "💬 NeBlock AI V2":
        users = load_users()
        users[str(user_id)]["current_model"] = "text"
        users[str(user_id)]["waiting_for_image"] = False
        save_users(users)
        await update.message.reply_text(
            f"💬 NeBlock AI V2 активирована\n━━━━━━━━━━━━━━━━\n"
            f"Задай свой вопрос в чат.\n"
            f"Что нового: качество +40%, скорость x2\n\n"
            f"📊 Осталось запросов: {remaining(user_id)}\n"
            f"{DISCLAIMER}"
        )
        return True
    
    if text == "🎨 NeBlock Images V2":
        users = load_users()
        users[str(user_id)]["current_model"] = "image"
        users[str(user_id)]["waiting_for_image"] = True
        save_users(users)
        await update.message.reply_text(
            f"🎨 NeBlock Images V2 активирована\n━━━━━━━━━━━━━━━━\n"
            f"Опиши что нарисовать.\n"
            f"Что нового: качество +50%, разные стили\n\n"
            f"📊 Осталось генераций: {image_remaining(user_id)}\n"
            f"⏳ 10-15 секунд"
        )
        return True
    
    if text == "👤 Профиль":
        await update.message.reply_text(get_full_profile(user_id), reply_markup=main_menu())
        return True
    
    if text == "🛒 Магазин":
        await update.message.reply_text(
            f"🛒 Магазин\n━━━━━━━━━━━━━━━━\n💰 {get_tokens(user_id)} токенов\n\n💬 ЛС | 🎨 Фото | 👥 Чаты | 💎 Премиум",
            reply_markup=shop_keyboard()
        )
        return True
    
    if text == "💰 Заработать":
        await update.message.reply_text(
            f"💰 Заработок\n━━━━━━━━━━━━━━━━\n💎 {get_tokens(user_id)}\n\n"
            f"🎁 Бонус: {DAILY_BONUS_MIN}-{DAILY_BONUS_MAX}/день\n"
            f"👥 Рефералы: +{REFERRAL_BONUS} тебе, +{INVITED_BONUS} другу",
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
    
    current_model = "💬 NeBlock AI V2" if user.get("current_model") == "text" else "🎨 NeBlock Images V2"
    premium = "💎 Активен" if is_premium(user_id) else "Не активен"
    
    def fmt_unlim(until_str):
        if not until_str: return "Не активен"
        try:
            if datetime.now() < datetime.fromisoformat(until_str):
                diff = datetime.fromisoformat(until_str) - datetime.now()
                d, h = diff.days, diff.seconds // 3600
                return f"Активен ({d}д {h}ч)" if d > 0 else f"Активен ({h}ч)"
        except: pass
        return "Не активен"
    
    return (
        f"👤 Профиль V2\n━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🆔 {user_id}\n📅 {joined}\n🔮 {current_model}\n"
        f"💎 Премиум: {premium}\n\n"
        f"💰 {user.get('tokens', 0)} токенов\n💎 Заработано: {user.get('earned_tokens', 0)}\n💸 Потрачено: {user.get('spent_tokens', 0)}\n\n"
        f"💬 ЛС: {user.get('requests_today', 0)}/{DAILY_LIMIT + user.get('extra_requests', 0)} | {fmt_unlim(user.get('unlimited_until'))}\n"
        f"🎨 ЛС фото: {user.get('image_requests_today', 0)}/{IMAGE_DAILY_LIMIT + user.get('extra_image_requests', 0)} | {fmt_unlim(user.get('image_unlimited_until'))}\n"
        f"👥 Чаты: {user.get('chat_requests_today', 0)}/{CHAT_DAILY_LIMIT + user.get('extra_chat_requests', 0)} | {fmt_unlim(user.get('chat_unlimited_until'))}\n"
        f"🎨 Чаты фото: {user.get('chat_image_requests_today', 0)}/{CHAT_IMAGE_LIMIT + user.get('extra_chat_image_requests', 0)} | {fmt_unlim(user.get('chat_image_unlimited_until'))}\n\n"
        f"📈 Всего: {user.get('total_requests', 0)} текст, {user.get('total_images', 0)} фото\n"
        f"🛡 Предупреждений: {user.get('warnings', 0)}/5\n"
        f"👥 Рефералов: {user.get('referrals', 0)}\n🕐 {last}\n{DISCLAIMER}"
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
        await query.edit_message_text(f"🧠 NeBlock AI V2\n💰 {get_tokens(user_id)} токенов", reply_markup=main_menu())
    elif data == "about":
        await query.edit_message_text(
            "ℹ️ NeBlock AI V2\n━━━━━━━━━━━━━━━━\n\n"
            "💬 NeBlock AI V2 — текст\n🎨 NeBlock Images V2 — фото\n"
            "👥 Чаты | 🛡 Модерация | 💎 Премиум",
            reply_markup=back_button()
        )
    elif data == "models":
        await query.edit_message_text(MODELS_INFO, reply_markup=back_button())
    elif data == "premium_info":
        await query.edit_message_text(
            "💎 Премиум NeBlock AI V2\n━━━━━━━━━━━━━━━━\n\n"
            "Безлимит на все модели одновременно:\n"
            "• 💬 Текстовые запросы без ограничений\n"
            "• 🎨 Генерация фото без ограничений\n"
            "• 👥 Чаты без ограничений\n\n"
            "💰 Купи в Магазине:\n"
            "• 1 день — 200 токенов\n"
            "• 7 дней — 1000 токенов",
            reply_markup=back_button()
        )
    elif data == "stats":
        user = get_user(user_id)
        await query.edit_message_text(
            f"📊 Статистика V2\n\n💬 ЛС: {user.get('requests_today', 0)}\n"
            f"👥 Чаты: {user.get('chat_requests_today', 0)}\n"
            f"🎨 Фото: {user.get('image_requests_today', 0)}\n"
            f"💎 Премиум: {'Да' if is_premium(user_id) else 'Нет'}",
            reply_markup=back_button()
        )
    elif data == "shop":
        await query.edit_message_text(f"🛒 Магазин\n💰 {get_tokens(user_id)} токенов", reply_markup=shop_keyboard())
    elif data == "earn":
        await query.edit_message_text(f"💰 Заработок\n💎 {get_tokens(user_id)}", reply_markup=earn_keyboard())
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
        
        actions = {
            "extra5": ("extra_requests", 5), "extra10": ("extra_requests", 10), "extra50": ("extra_requests", 50),
            "image1": ("extra_image_requests", 1), "image5": ("extra_image_requests", 5), "image20": ("extra_image_requests", 20),
            "chat_extra10": ("extra_chat_requests", 10), "chat_extra50": ("extra_chat_requests", 50),
            "chat_image5": ("extra_chat_image_requests", 5), "chat_image20": ("extra_chat_image_requests", 20),
        }
        
        time_actions = {
            "unlimited_1h": ("unlimited_until", 1), "unlimited_24h": ("unlimited_until", 24),
            "unlimited_7d": ("unlimited_until", 168), "image_unlimited_1h": ("image_unlimited_until", 1),
            "chat_unlimited_1h": ("chat_unlimited_until", 1), "chat_unlimited_24h": ("chat_unlimited_until", 24),
        }
        
        if item_id in actions:
            field, amount = actions[item_id]
            users[uid][field] = users[uid].get(field, 0) + amount
        elif item_id in time_actions:
            field, hours = time_actions[item_id]
            users[uid][field] = (datetime.now() + timedelta(hours=hours)).isoformat()
        elif item_id == "premium_day":
            users[uid]["premium_until"] = (datetime.now() + timedelta(hours=24)).isoformat()
        elif item_id == "premium_week":
            users[uid]["premium_until"] = (datetime.now() + timedelta(days=7)).isoformat()
        
        save_users(users)
        await query.answer(f"✅ {item['name']}!", show_alert=True)
        await query.edit_message_text(f"✅ {item['name']}\n💎 {get_tokens(user_id)}", reply_markup=back_button())
    elif data.startswith("buy_"):
        item_id = data.replace("buy_", "")
        item = SHOP_ITEMS.get(item_id)
        if not item: return
        tokens = get_tokens(user_id)
        can = "✅ Хватает" if tokens >= item["price"] else "❌ Не хватает"
        await query.edit_message_text(
            f"🛒 {item['icon']} {item['name']}\n📝 {item['desc']}\n💰 {item['price']}\n💎 {tokens}\n{can}",
            reply_markup=confirm_keyboard(item_id)
        )

# ═══════════════════════════════════════════
# 💬 Сообщения
# ═══════════════════════════════════════════

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip() if update.message.text else ""
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type
    bot_username = context.bot.username
    
    if is_user_muted(user_id):
        await update.message.reply_text("🚫 Вы заблокированы за нарушения.")
        return
    
    is_clean, severity, reason = moderate_content(text)
    if not is_clean:
        muted, warn = warn_user(user_id, severity)
        await update.message.reply_text(f"⚠️ {reason}\n{warn}")
        logger.warning(f"Модерация: user={user_id}, severity={severity}, text={text[:50]}")
        return
    
    if chat_type == "private":
        if await reply_button_handler(update, context):
            return
    
    is_image_request = False
    if chat_type in ["group", "supergroup"]:
        mention = f"@{bot_username}"
        
        if mention not in text:
            keywords = ["бот ", "нейробот ", "нейросеть ", "ai ", "AI ", "нарисуй "]
            for kw in keywords:
                if text.lower().startswith(kw.lower()):
                    text = text[len(kw):].strip()
                    if kw == "нарисуй ": is_image_request = True
                    break
            else:
                return
        else:
            text = text.replace(mention, "").strip()
            if text.lower().startswith("нарисуй"):
                text = text[7:].strip()
                is_image_request = True
        
        if not text:
            await update.message.reply_text(
                f"🧠 NeBlock AI V2!\n💬 @{bot_username} вопрос\n🎨 @{bot_username} нарисуй описание",
                reply_to_message_id=update.message.message_id
            )
            return
    
    user = get_user(user_id)
    
    if context.user_data.get("waiting_promo"):
        context.user_data["waiting_promo"] = False
        success, result = use_promo(user_id, text)
        await update.message.reply_text(f"🎟 +{result}!\n💎 {get_tokens(user_id)}" if success else f"❌ {result}")
        return
    
    # Генерация изображения
    if is_image_request or user.get("current_model") == "image" or user.get("waiting_for_image"):
        users = load_users()
        users[str(user_id)]["waiting_for_image"] = False
        save_users(users)
        
        if not can_image_request(user_id, chat_type):
            rem = image_remaining(user_id, chat_type)
            await update.message.reply_text(
                f"🚫 Лимит фото!\n📊 Осталось: {rem}",
                reply_to_message_id=update.message.message_id if chat_type != "private" else None,
                reply_markup=limit_reached_keyboard() if chat_type == "private" else None
            )
            return
        
        msg = await update.message.reply_text(
            "🎨 NeBlock Images V2 генерирует...",
            reply_to_message_id=update.message.message_id if chat_type != "private" else None
        )
        
        try:
            image_bytes, error = await generate_image(text)
            if image_bytes:
                add_image_request(user_id, chat_type)
                await msg.delete()
                rem = image_remaining(user_id, chat_type)
                await update.message.reply_photo(
                    photo=image_bytes,
                    caption=f"🎨 NeBlock Images V2\n📝 {text[:200]}\n📊 Осталось: {rem}",
                    reply_to_message_id=update.message.message_id if chat_type != "private" else None
                )
            else:
                await msg.edit_text(f"❌ Ошибка: {error[:100] if error else '?'}")
        except:
            try: await msg.delete()
            except: pass
            await update.message.reply_text("❌ Ошибка.")
        return
    
    # Текст
    if not can_request(user_id, chat_type):
        rem = remaining(user_id, chat_type)
        await update.message.reply_text(
            f"🚫 Лимит!\n📊 Осталось: {rem}",
            reply_markup=limit_reached_keyboard() if chat_type == "private" else None,
            reply_to_message_id=update.message.message_id if chat_type != "private" else None
        )
        return
    
    msg = await update.message.reply_text(
        "💬 NeBlock AI V2 генерирует ответ...",
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
                label = "👥 Чат"
            else:
                used = user.get("requests_today", 0) + 1
                total = DAILY_LIMIT + user.get("extra_requests", 0)
                label = "💬 NeBlock AI V2"
            
            footer = f"\n\n━━━━━━━━━━━━━━━━\n{label} | 📊 {used}/{total} | Осталось: {rem}\n{DISCLAIMER}"
            
            for i in range(0, len(answer), 4000):
                chunk = answer[i:i+4000]
                await update.message.reply_text(
                    chunk + footer if i == 0 else chunk,
                    reply_to_message_id=update.message.message_id if chat_type != "private" else None
                )
        else:
            await update.message.reply_text(f"🤷 Пусто\n{DISCLAIMER}")
    except:
        try: await msg.delete()
        except: pass
        await update.message.reply_text(f"❌ Ошибка.\n{DISCLAIMER}")

# ═══════════════════════════════════════════
# 🚀 Запуск
# ═══════════════════════════════════════════

def main():
    print("🧠 NeBlock AI V2")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("chatowner", chatowner_cmd))
    app.add_handler(CommandHandler("chatshop", chatshop_cmd))
    app.add_handler(CommandHandler("upgrade", upgrade_cmd))
    app.add_handler(CommandHandler("shop", lambda u, c: u.message.reply_text("🛒 Магазин", reply_markup=shop_keyboard())))
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
