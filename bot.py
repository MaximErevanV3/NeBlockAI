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
import math
from datetime import datetime, timedelta

# ═══════════════════════════════════════════
# 🧠 NeBlock AI V5.7 - Конфигурация
# ═══════════════════════════════════════════

TELEGRAM_TOKEN = "8700124191:AAE6qSSouLjlDxPWwoFObJORMbDotsby9co"
YANDEX_API_KEY = "AQVNy7Dm-dvQRzejHvH0383oHTZhhW2fda95I558"
YANDEX_FOLDER = "b1guk4h3j9t48lsjl6sq"
PROMPT_ID = "fvt621uiq1fftiu5qomu"
IMAGE_MODEL = "art://b1guk4h3j9t48lsjl6sq/aliceai-image-art-3.0/latest"

# ═══════════════════════════════════════════
# 📊 БАЛАНСИРОВКА ЭКОНОМИКИ V5.7
# ═══════════════════════════════════════════

DAILY_LIMIT = 3
IMAGE_DAILY_LIMIT = 2
CHAT_DAILY_LIMIT = 10
CHAT_IMAGE_LIMIT = 5

DATA_FILE = "users.json"
PROMO_FILE = "promos.json"
CHATS_FILE = "chats.json"
DISCOUNTS_FILE = "discounts.json"
TOKEN_RATE_FILE = "token_rate.json"
TOKEN_HISTORY_FILE = "token_history.json"
TRANSFER_LOG_FILE = "transfer_log.json"
DONATION_FILE = "donations.json"
ADMIN_IDS = [1671403667]

START_BONUS = 25
REFERRAL_BONUS = 10
INVITED_BONUS = 5
PREMIUM_REFERRAL_BONUS = 30
PREMIUM_INVITED_BONUS = 10
CASHBACK_PERCENT = 15
PASSIVE_INCOME_HOURLY = 5
PASSIVE_INCOME_MAX_HOURS = 12
PREMIUM_RENEWAL_DISCOUNT = 15
PREMIUM_CHAT_DISCOUNT = 10
BOT_VERSION = "5.7"

# Интервалы уведомлений
NOTIFY_INTERVAL_FREE = 24
DEFAULT_NOTIFY_INTERVAL_PREMIUM = 6
PREMIUM_NOTIFY_OPTIONS = [1, 3, 6, 12, 24]  # Доступные интервалы для Premium

MIN_TRANSFER = 1
MAX_TRANSFER = 5000
DAILY_TRANSFER_LIMIT = 25000
MIN_DONATION = 1
MAX_DONATION = 50000

PREMIUM_MAX_TRANSFER = 25000
PREMIUM_DAILY_TRANSFER_LIMIT = 100000
PREMIUM_MAX_DONATION = 250000

# ═══════════════════════════════════════════
# 🔥 СИСТЕМА ЕЖЕДНЕВНЫХ НАГРАД
# ═══════════════════════════════════════════

STREAK_BASE_REWARDS = {
    1: {"name": "День 1", "base_min": 1, "base_max": 3, "icon": "🌱", "desc": "Начало пути!"},
    2: {"name": "День 2", "base_min": 2, "base_max": 4, "icon": "🌿", "desc": "Второй день."},
    3: {"name": "День 3", "base_min": 2, "base_max": 5, "icon": "🌳", "desc": "Третий день!"},
    4: {"name": "День 4", "base_min": 3, "base_max": 6, "icon": "🍀", "desc": "Четвёртый день."},
    5: {"name": "День 5", "base_min": 3, "base_max": 7, "icon": "⭐", "desc": "Пятый день."},
    6: {"name": "День 6", "base_min": 4, "base_max": 8, "icon": "🌟", "desc": "Шестой день."},
    7: {"name": "НЕДЕЛЯ! 🎉", "base_min": 5, "base_max": 10, "icon": "🔥", "desc": "Целая неделя!"},
    10: {"name": "День 10 🎊", "base_min": 6, "base_max": 13, "icon": "🎯", "desc": "Юбилейный!"},
    14: {"name": "2 НЕДЕЛИ! 🏆", "base_min": 8, "base_max": 18, "icon": "👑", "desc": "Две недели!"},
    21: {"name": "3 НЕДЕЛИ! 🌟", "base_min": 12, "base_max": 27, "icon": "💫", "desc": "Три недели!"},
    28: {"name": "4 НЕДЕЛИ! 🌍", "base_min": 16, "base_max": 36, "icon": "🌍", "desc": "Месяц!"},
    30: {"name": "ДЕНЬ 30! 👑✨", "base_min": 18, "base_max": 40, "icon": "👑", "desc": "МЕГА-ДЕНЬ! +Premium 1д", "premium_bonus": True},
}
MAX_STREAK_DAY = 30

for day in range(1, 31):
    if day not in STREAK_BASE_REWARDS:
        prev = STREAK_BASE_REWARDS.get(day - 1, STREAK_BASE_REWARDS[1])
        STREAK_BASE_REWARDS[day] = {"name": f"День {day}", "base_min": prev["base_min"] + 1, "base_max": prev["base_max"] + 2, "icon": "📅", "desc": f"День {day} подряд!"}

# ═══════════════════════════════════════════
# 📝 СИСТЕМА ПРЕСЕТОВ
# ═══════════════════════════════════════════

PREMIUM_PRESETS = {
    "programmer": {"id": "programmer", "name": "💻 Программист", "icon": "💻", "system_prompt": "Ты — опытный senior-разработчик. Отвечай технически точно, с примерами кода на Python/JavaScript. Объясняй сложное простым языком. Предлагай best practices и альтернативные решения.", "category": "professional", "description": "Код, архитектура, дебаггинг, best practices"},
    "copywriter": {"id": "copywriter", "name": "📝 Копирайтер", "icon": "📝", "system_prompt": "Ты — профессиональный копирайтер. Пиши убедительные тексты по формуле AIDA. Предлагай 3 варианта заголовков. Адаптируй стиль под аудиторию. Завершай призывом к действию.", "category": "professional", "description": "Реклама, лендинги, рассылки, SMM"},
    "business": {"id": "business", "name": "💼 Бизнес-консультант", "icon": "💼", "system_prompt": "Ты — бизнес-консультант с опытом запуска стартапов. Анализируй рынок, предлагай стратегии с цифрами. Используй SWOT-анализ. Давай дорожную карту действий.", "category": "professional", "description": "Стратегия, стартапы, маркетинг, финансы"},
    "teacher": {"id": "teacher", "name": "📚 Учитель", "icon": "📚", "system_prompt": "Ты — опытный педагог. Объясняй от простого к сложному. Используй яркие примеры и аналогии. Проверяй понимание вопросами. Разбивай материал на блоки.", "category": "education", "description": "Обучение, объяснение, подготовка"},
    "psychologist": {"id": "psychologist", "name": "🧠 Психолог", "icon": "🧠", "system_prompt": "Ты — психолог-консультант. Проявляй эмпатию, задавай открытые вопросы. Предлагай практические техники. Не ставь диагнозов. При серьёзных симптомах рекомендуй врача.", "category": "life", "description": "Отношения, стресс, мотивация"},
    "chef": {"id": "chef", "name": "👨‍🍳 Шеф-повар", "icon": "👨‍🍳", "system_prompt": "Ты — шеф-повар ресторана. Давай рецепты с точными граммовками. Предлагай замены для аллергиков. Объясняй технику приготовления. Советуй сервировку и сочетания с напитками.", "category": "life", "description": "Рецепты, кулинария, сочетания"},
    "fitness": {"id": "fitness", "name": "💪 Фитнес-тренер", "icon": "💪", "system_prompt": "Ты — фитнес-тренер и нутрициолог. Составляй программы тренировок. Объясняй технику. Рассчитывай КБЖУ. Мотивируй и предупреждай о травмах.", "category": "life", "description": "Тренировки, питание, похудение"},
    "creative": {"id": "creative", "name": "🎨 Креативный директор", "icon": "🎨", "system_prompt": "Ты — креативный директор. Генерируй нестандартные идеи. Используй сторителлинг и визуальные метафоры. Предлагай несколько концепций. Мысли смело.", "category": "professional", "description": "Креатив, брендинг, реклама"},
    "lawyer": {"id": "lawyer", "name": "⚖️ Юрист", "icon": "⚖️", "system_prompt": "Ты — практикующий юрист. Ссылайся на законы. Объясняй термины простым языком. Предупреждай о рисках. Уточняй: консультация не заменяет очного юриста.", "category": "professional", "description": "Право, договоры, консультации"},
    "doctor": {"id": "doctor", "name": "🏥 Врач-терапевт", "icon": "🏥", "system_prompt": "Ты — врач-терапевт. Собирай анамнез: спрашивай о симптомах. Объясняй возможные причины. При тревожных симптомах настаивай на визите к врачу. Не назначай лекарства.", "category": "life", "description": "Здоровье, симптомы, профилактика"},
}

def get_daily_bonus_info():
    text = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🔥 ЕЖЕДНЕВНЫЕ НАГРАДЫ (ДО 30 ДНЕЙ)\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n📐 Формула: база дня × множитель курса\n⚠️ Не забрали до 00:00 МСК — серия СГОРИТ!\n👑 30-й день: Premium ЛС 1 день!\n\n📅 НАГРАДЫ:\n\n"
    for day in [1,2,3,5,7,10,14,21,28,30]:
        r = STREAK_BASE_REWARDS[day]
        text += f"{r['icon']} {r['name']}: {r['base_min']}-{r['base_max']} 💮"
        if r.get("premium_bonus"): text += " + 🎁 Premium"
        text += "\n"
    return text

def get_user_bonus(streak, rate=0.01):
    reward = STREAK_BASE_REWARDS.get(min(streak, MAX_STREAK_DAY), STREAK_BASE_REWARDS[1])
    is_max = streak >= MAX_STREAK_DAY
    rate_multiplier = max(0.5, min(1.5, 1.0 + (rate * 10 - 0.1)))
    base_bonus = random.randint(reward["base_min"], reward["base_max"])
    bonus = max(1, int(base_bonus * rate_multiplier))
    premium_bonus = reward.get("premium_bonus", False) and not (is_max and streak > MAX_STREAK_DAY)
    return bonus, reward["icon"], reward["name"], premium_bonus, rate_multiplier

STREAK_INFO = get_daily_bonus_info()

TRANSFER_TAX_BRACKETS = [{"min": 0, "max": 99, "tax_percent": 0}, {"min": 100, "max": 249, "tax_percent": 3}, {"min": 250, "max": 499, "tax_percent": 5}, {"min": 500, "max": 999, "tax_percent": 8}, {"min": 1000, "max": 2499, "tax_percent": 12}, {"min": 2500, "max": 5000, "tax_percent": 15}]
PREMIUM_TRANSFER_TAX_BRACKETS = [{"min": 0, "max": 499, "tax_percent": 0}, {"min": 500, "max": 999, "tax_percent": 2}, {"min": 1000, "max": 4999, "tax_percent": 5}, {"min": 5000, "max": 14999, "tax_percent": 8}, {"min": 15000, "max": 25000, "tax_percent": 10}]

DAY_FACTORS = {0: ("Понедельник", 1.05, "📈"), 1: ("Вторник", 1.02, "📊"), 2: ("Среда", 1.03, "📊"), 3: ("Четверг", 1.04, "📈"), 4: ("Пятница", 1.10, "🚀"), 5: ("Суббота", 0.95, "📉"), 6: ("Воскресенье", 0.95, "📉")}

BASE_PRICES_USD = {
    "extra5": 5, "extra10": 8, "extra50": 35, "unlimited_1h": 15, "unlimited_24h": 50, "unlimited_7d": 250,
    "image1": 8, "image5": 30, "image20": 100, "image_unlimited_1h": 25,
    "premium_day": 100, "premium_week": 500, "premium_30d": 1500, "premium_60d": 2500,
    "premium_90d": 3500, "premium_year": 10000, "premium_forever": 25000,
    "chat_extra10": 8, "chat_extra50": 30, "chat_unlimited_1h": 20, "chat_unlimited_24h": 75,
    "chat_image5": 25, "chat_image20": 90,
    "chat_premium_day": 150, "chat_premium_week": 750, "chat_premium_30d": 2500, "chat_premium_60d": 4000,
    "chat_premium_90d": 5500, "chat_premium_year": 15000, "chat_premium_forever": 35000,
}

AI_DISCLAIMER = "\n\n━━━━━━━━━━━━━━━━\n⚠️ NeBlock AI V2 • Только для справки"

CHANGELOG = """
📋 ЛОГ ОБНОВЛЕНИЙ NeBlock AI
━━━━━━━━━━━━━━━━━━━━

Версия 5.7
• 🔔 Premium: кастомизация интервала уведомлений (1/3/6/12/24ч)
• 🔔 Команда /notify — настройка интервала уведомлений
• 📊 Расширенная информация во всех разделах
• 🔧 Возвращены все удалённые команды
• 🆕 Новые команды: /notify, /chatowner, /chatshop

Версия 5.6
• Умные уведомления (Free: 24ч, Premium: 6ч)
• Пассивный доход 5 💮/час
• Кэшбек 15% на чат-покупки
• Команда /id
"""

FAQ_TEXT = f"""
📚 ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ
━━━━━━━━━━━━━━━━━━━━

❓ Что такое NeBlock AI?
Платформа с собственными ИИ-моделями в Telegram:
• 💬 NeBlock AI V2 — текстовая модель
• 🎨 NeBlock Images V2 — генерация изображений

❓ Что даёт Premium? 💎
• Безлимит текста и фото в ЛС
• 10 проф. пресетов (Программист, Юрист, Врач...)
• Кэшбек 15% на чат-покупки
• Скидка 15% на продление Premium
• Скидка 10% на чат-товары
• Пассивный доход 5 💮/час (до 60 💮/день!)
• Рефералы ×3 (30/10 💮)
• Лимит перевода 25 000 💮 (налог 0-10%)
• Умные уведомления (кастомизируемый интервал!)
• Значок 💎 в профиле и топах

❓ Как настроить уведомления? 🔔
• Free: раз в 24 часа (фиксировано)
• Premium: /notify — выбрать интервал (1/3/6/12/24 часа)

❓ Как работает кэшбек? 🔄
15% от покупок в чатах возвращается на баланс (только Premium).

❓ Лимиты?
Free: {DAILY_LIMIT} текст + {IMAGE_DAILY_LIMIT} фото/день
Premium: безлимит в ЛС
"""

DONATE_INFO_TEXT = f"""
🌍 БЛАГОТВОРИТЕЛЬНОСТЬ
━━━━━━━━━━━━━━━━━━━━
🔥 Сжигание NBT повышает курс для всех.
📊 Free: до {MAX_DONATION:,} 💮 | Premium 💎: до {PREMIUM_MAX_DONATION:,} 💮
🏆 /donatetop — топ (💎 = Premium)
"""

TRANSFER_INFO = f"""
💸 ПЕРЕВОДЫ 💮 NBT
━━━━━━━━━━━━━━━━━━━━
/transfer ID КОЛИЧЕСТВО | @username | ответ
📊 FREE: {MAX_TRANSFER:,} 💮/раз | {DAILY_TRANSFER_LIMIT:,} 💮/день | налог 0-15%
💎 PREMIUM: {PREMIUM_MAX_TRANSFER:,} 💮/раз | {PREMIUM_DAILY_TRANSFER_LIMIT:,} 💮/день | налог 0-10%
"""

COMMANDS_LIST = """
📋 КОМАНДЫ NeBlock AI V5.7
━━━━━━━━━━━━━━━━━━━━

💬 ОСНОВНЫЕ:
/start — главное меню | /faq — вопросы
/commands — команды | /changelog — обновления
🆔 /id — ваш ID | /profile — профиль

💎 PREMIUM:
/premium — Premium-меню | /buy_premium — купить
/notify — настройка уведомлений (Premium)

🛒 МАГАЗИН:
/shop — магазин | /tokenrate — курс NBT
/discounts — скидки | /promo — промокод

🔥 НАГРАДЫ:
/streak — серия | /streak_info — все 30 дней

💸 ФИНАНСЫ:
/transfer — перевод | /transferinfo — инфо
/donate — донат | /donatetop — топ донатов

🎨 ГЕНЕРАЦИЯ:
/genimage — изображения

📝 ПРЕСЕТЫ (Premium):
/presets — выбрать пресет

👥 ЧАТЫ:
/chatowner — владельцы | /chatshop — магазин чата
/shopdesc — описание магазина

🔧 АДМИН (для админов):
/give | /take | /resetuser | /setpremium
/userinfo | /top | /stats | /broadcast
/createpromo | /promos | /deletepromo
/forcediscounts | /forcerate | /cleardiscounts
"""

DISCOUNT_TYPES = {"regular": {"name": "Обычная", "min": 5, "max": 25, "color": "🟢", "chance": 40, "icon": "🏷️"}, "super": {"name": "Супер", "min": 30, "max": 50, "color": "🔴", "chance": 20, "icon": "🔥"}, "flash": {"name": "Флеш", "min": 40, "max": 70, "color": "⚡", "chance": 8, "icon": "⏰"}, "bundle": {"name": "Набор", "min": 15, "max": 35, "color": "📦", "chance": 12, "icon": "🎁"}, "premium_discount": {"name": "Premium", "min": 10, "max": 30, "color": "👑", "chance": 5, "icon": "💎"}, "legendary": {"name": "ЛЕГЕНДАРНАЯ", "min": 100, "max": 100, "color": "🌟", "chance": 0.5, "icon": "💫"}}

SHOP_ITEMS_BASE = {
    "extra5": {"name": "+5 запросов", "price": 5, "icon": "📝", "category": "text", "desc": "5 доп. текстовых запросов.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "private", "type": "consumable", "duration": "до 00:00 МСК", "benefits": ["+5 текстовых запросов"]},
    "extra10": {"name": "+10 запросов", "price": 8, "icon": "📝", "category": "text", "desc": "10 доп. текстовых запросов.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "private", "type": "consumable", "duration": "до 00:00 МСК", "benefits": ["+10 запросов"]},
    "extra50": {"name": "+50 запросов", "price": 35, "icon": "📝", "category": "text", "desc": "50 доп. текстовых запросов.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "private", "type": "consumable", "duration": "до 00:00 МСК", "benefits": ["+50 запросов", "Экономия 30%"]},
    "unlimited_1h": {"name": "Безлимит текста 1ч", "price": 15, "icon": "♾️", "category": "text", "desc": "Безлимит текста на 1 час.", "warning": "⚠️ 1 час.", "location": "private", "type": "unlimited", "duration": "1 час", "benefits": ["Безлимит текста"]},
    "unlimited_24h": {"name": "Безлимит текста 24ч", "price": 50, "icon": "♾️", "category": "text", "desc": "Безлимит текста на 24 часа.", "warning": "⚠️ 24 часа.", "location": "private", "type": "unlimited", "duration": "24 часа", "benefits": ["Безлимит текста"]},
    "unlimited_7d": {"name": "Безлимит текста 7д", "price": 250, "icon": "♾️", "category": "text", "desc": "Безлимит текста на 7 дней.", "warning": "⚠️ 7 дней.", "location": "private", "type": "unlimited", "duration": "7 дней", "benefits": ["Безлимит текста"]},
    "image1": {"name": "1 фото", "price": 8, "icon": "🎨", "category": "image", "desc": "1 генерация. 1024×1024.", "warning": "⚠️ Сгорает.", "location": "private", "type": "consumable", "duration": "до 00:00 МСК", "benefits": ["1 изображение"]},
    "image5": {"name": "5 фото", "price": 30, "icon": "🎨", "category": "image", "desc": "5 генераций. 1024×1024.", "warning": "⚠️ Сгорают.", "location": "private", "type": "consumable", "duration": "до 00:00 МСК", "benefits": ["5 изображений"]},
    "image20": {"name": "20 фото", "price": 100, "icon": "🎨", "category": "image", "desc": "20 генераций. 1024×1024.", "warning": "⚠️ Сгорают.", "location": "private", "type": "consumable", "duration": "до 00:00 МСК", "benefits": ["20 изображений"]},
    "image_unlimited_1h": {"name": "Безлимит фото 1ч", "price": 25, "icon": "♾️", "category": "image", "desc": "Безлимит фото на 1 час.", "warning": "⚠️ 1 час.", "location": "private", "type": "unlimited", "duration": "1 час", "benefits": ["Безлимит фото"]},
    "premium_day": {"name": "Premium 1 день", "price": 100, "icon": "⭐", "category": "premium", "desc": "Все Premium-привилегии на 24 часа.", "warning": "⚠️ 24 часа. Только ЛС.", "location": "private", "type": "premium", "duration": "1 день", "benefits": ["Безлимит текста и фото", "10 проф. пресетов", "Кэшбек 15% на чат", "Пассивный доход 5 💮/час", "Рефералы ×3", "Уведомления (настраиваемые)", "Значок 💎"]},
    "premium_week": {"name": "Premium 7 дней", "price": 500, "icon": "⭐", "category": "premium", "desc": "Неделя Premium-привилегий.", "warning": "⚠️ 7 дней.", "location": "private", "type": "premium", "duration": "7 дней", "benefits": ["Всё из Premium 1 день", "Экономия 28%"]},
    "premium_30d": {"name": "Premium 30 дней 🔥", "price": 1500, "icon": "💎", "category": "premium", "desc": "Месяц Premium. Экономия 25%!", "warning": "⚠️ 30 дней.", "location": "private", "type": "premium", "duration": "30 дней", "benefits": ["Всё из Premium 1 день", "Экономия 25%"]},
    "premium_60d": {"name": "Premium 60 дней 🚀", "price": 2500, "icon": "💎", "category": "premium", "desc": "2 месяца Premium. Экономия 37%!", "warning": "⚠️ 60 дней.", "location": "private", "type": "premium", "duration": "60 дней", "benefits": ["Всё из Premium 1 день", "Экономия 37%"]},
    "premium_90d": {"name": "Premium 90 дней 👑", "price": 3500, "icon": "💎", "category": "premium", "desc": "3 месяца Premium. Экономия 50%!", "warning": "⚠️ 90 дней.", "location": "private", "type": "premium", "duration": "90 дней", "benefits": ["Всё из Premium 1 день", "Экономия 50%"]},
    "premium_year": {"name": "Premium 1 год 💫", "price": 10000, "icon": "👑", "category": "premium", "desc": "Год Premium. Экономия 72%!", "warning": "⚠️ 365 дней.", "location": "private", "type": "premium", "duration": "1 год", "benefits": ["Всё из Premium 1 день", "Экономия 72%"]},
    "premium_forever": {"name": "Premium НАВСЕГДА ✨", "price": 25000, "icon": "🌟", "category": "premium", "desc": "Пожизненный Premium.", "warning": "⚠️ Только ЛС.", "location": "private", "type": "premium", "duration": "Навсегда", "benefits": ["Всё из Premium 1 день", "Пожизненно", "Легендарный значок"]},
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("NeBlockAI")

client = openai.OpenAI(api_key=YANDEX_API_KEY, base_url="https://ai.api.cloud.yandex.net/v1", project=YANDEX_FOLDER, timeout=60.0)

def load_json(filename):
    if os.path.exists(filename): return json.load(open(filename, "r", encoding="utf-8"))
    return {}

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f: json.dump(data, f, indent=2, ensure_ascii=False)

def load_users(): return load_json(DATA_FILE)
def save_users(users): save_json(DATA_FILE, users)
def load_promos(): return load_json(PROMO_FILE)
def save_promos(promos): save_json(PROMO_FILE, promos)
def load_chats(): return load_json(CHATS_FILE)
def save_chats(chats): save_json(CHATS_FILE, chats)
def load_discounts(): return load_json(DISCOUNTS_FILE)
def save_discounts(discounts): save_json(DISCOUNTS_FILE, discounts)
def load_donations(): return load_json(DONATION_FILE)
def save_donations(donations): save_json(DONATION_FILE, donations)

def get_donation_stats():
    donations = load_donations()
    total = sum(d.get("amount", 0) for d in donations.get("donations", []))
    count = len(donations.get("donations", []))
    users = {}
    for d in donations.get("donations", []):
        uid = str(d.get("user_id", "")); users[uid] = users.get(uid, 0) + d.get("amount", 0)
    top_donors = sorted(users.items(), key=lambda x: x[1], reverse=True)[:10]
    return total, count, top_donors

def get_day_factor():
    today = datetime.now().weekday(); info = DAY_FACTORS.get(today, ("Неизвестно", 1.0, "❓"))
    return info[1], info[0], info[2]

def get_current_rate_block():
    now = datetime.now(); hour = now.hour; block_hour = (hour // 4) * 4
    return f"{now.strftime('%Y-%m-%d')}-{block_hour:02d}", block_hour

def get_next_rate_update():
    now = datetime.now(); hour = now.hour; block_hour = (hour // 4) * 4
    next_block = block_hour + 4
    return (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0) if next_block >= 24 else now.replace(hour=next_block, minute=0, second=0, microsecond=0)

def get_transfer_tax(amount, is_premium=False):
    brackets = PREMIUM_TRANSFER_TAX_BRACKETS if is_premium else TRANSFER_TAX_BRACKETS
    for b in brackets:
        if b["min"] <= amount <= b["max"]: return int(amount * b["tax_percent"] / 100), b["tax_percent"], ""
    return 0, 0, ""

def log_transfer(from_id, to_id, amount, tax, final_amount):
    log = load_json(TRANSFER_LOG_FILE)
    if "transfers" not in log: log["transfers"] = []
    log["transfers"].append({"date": datetime.now().strftime("%Y-%m-%d"), "from_id": from_id, "to_id": to_id, "amount": amount, "tax": tax, "final_amount": final_amount})
    save_json(TRANSFER_LOG_FILE, log)

def log_donation(user_id, amount):
    donations = load_donations()
    if "donations" not in donations: donations["donations"] = []
    donations["donations"].append({"date": datetime.now().strftime("%Y-%m-%d"), "user_id": user_id, "amount": amount})
    save_donations(donations)

def get_token_rate():
    rate_data = load_json(TOKEN_RATE_FILE); history = load_json(TOKEN_HISTORY_FILE)
    now = datetime.now(); current_block, block_hour = get_current_rate_block()
    if rate_data.get("rate_block") != current_block:
        users = load_users()
        total_tokens = sum(u.get("tokens", 0) for u in users.values())
        total_earned = sum(u.get("earned_tokens", 0) for u in users.values())
        total_spent = sum(u.get("spent_tokens", 0) for u in users.values())
        donated_total, _, _ = get_donation_stats()
        total_burned = total_spent + donated_total
        active_users = sum(1 for u in users.values() if u.get("requests_today", 0) > 0)
        total_users = len(users)
        base_rate = 0.005; ideal_supply = 5000
        supply_factor = max(0.1, min(50.0, (ideal_supply / max(total_tokens, 1)) ** 0.6)) if total_tokens > 0 else 1.0
        activity_factor = 0.5 + ((active_users / max(total_users, 1)) * 1.5) if total_users > 0 else 1.0
        total_supply = total_earned + donated_total
        burn_factor = 0.7 + ((total_burned / max(total_supply, 1)) * 3.0) if total_supply > 0 else 1.0
        day_factor, day_name, day_icon = get_day_factor()
        volatility = 1.0
        if history:
            rates = [h.get("rate", base_rate) for h in history.values() if h.get("rate")]
            if len(rates) > 1:
                avg_rate = sum(rates) / len(rates); std_dev = math.sqrt(sum((r - avg_rate) ** 2 for r in rates) / len(rates))
                volatility = max(0.5, min(3.0, 1.0 + (std_dev / max(avg_rate, 0.0001)) * 0.8))
        market_noise = random.uniform(0.92, 1.08)
        rate = max(0.00001, base_rate * supply_factor * activity_factor * burn_factor * day_factor * volatility * market_noise)
        market_cap = round(total_tokens * rate, 2)
        yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_rate = history.get(yesterday, {}).get("rate", rate)
        change_24h = round(((rate - yesterday_rate) / max(yesterday_rate, 0.0001)) * 100, 2)
        trend = "📈" if change_24h > 0.5 else "📉" if change_24h < -0.5 else "📊"
        next_update = get_next_rate_update()
        rate_data = {"rate_block": current_block, "block_hour": block_hour, "rate": rate, "total_supply": total_tokens, "total_burned": total_burned, "total_donated": donated_total, "day_factor": day_factor, "day_name": day_name, "day_icon": day_icon, "supply_factor": round(supply_factor, 4), "activity_factor": round(activity_factor, 4), "burn_factor": round(burn_factor, 4), "volatility_index": round(volatility, 4), "market_cap": market_cap, "change_24h": change_24h, "trend": trend, "next_update": next_update.strftime("%H:%M МСК")}
        save_json(TOKEN_RATE_FILE, rate_data)
        history[now.strftime("%Y-%m-%d")] = {"rate": rate}
        if len(history) > 30: history = dict(sorted(history.items())[-30:])
        save_json(TOKEN_HISTORY_FILE, history)
    return rate_data

def get_item_price(item_id, user_id=None):
    rate_data = get_token_rate()
    base_price = max(1, int(BASE_PRICES_USD.get(item_id, 10) / 100 / rate_data.get("rate", 0.005)))
    if user_id and is_premium(user_id):
        item = SHOP_ITEMS_BASE.get(item_id, {})
        if item.get("category") == "premium" and item.get("location") == "private": base_price = max(1, int(base_price * 0.85))
        elif item.get("location") == "chat": base_price = max(1, int(base_price * 0.90))
    return base_price

def get_shop_items(user_id=None):
    return {item_id: {**item, "price": get_item_price(item_id, user_id)} for item_id, item in SHOP_ITEMS_BASE.items()}

def generate_discounts():
    all_items = list(SHOP_ITEMS_BASE.keys()); discounts = {"generated_at": datetime.now().isoformat()}; used_items = set()
    if random.uniform(0, 100) < DISCOUNT_TYPES["legendary"]["chance"]:
        item_id = random.choice(all_items)
        discounts[item_id] = {"percent": 100, "type": "legendary", "type_name": "ЛЕГЕНДАРНАЯ", "color": "🌟", "icon": "💫", "expires": (datetime.now() + timedelta(hours=3)).isoformat()}
        used_items.add(item_id)
    available_types = [d for d, c in DISCOUNT_TYPES.items() if d != "legendary" and random.randint(1, 100) <= c["chance"]] or ["regular"]
    for _ in range(random.randint(3, 5)):
        if len(used_items) >= len(all_items): break
        disc_type = random.choice(available_types); dconfig = DISCOUNT_TYPES[disc_type]
        available = [i for i in all_items if i not in used_items]
        if not available: break
        item_id = random.choice(available); used_items.add(item_id)
        discounts[item_id] = {"percent": random.randint(dconfig["min"], dconfig["max"]), "type": disc_type, "type_name": dconfig["name"], "color": dconfig["color"], "icon": dconfig["icon"], "expires": (datetime.now() + timedelta(hours=24)).isoformat() if disc_type == "flash" else None}
    return discounts

def get_discounts():
    discounts = load_discounts(); last_update = discounts.get("last_update", ""); now = datetime.now()
    if discounts:
        to_delete = [i for i, d in discounts.items() if i not in ["last_update", "generated_at"] and d.get("expires") and now > datetime.fromisoformat(d["expires"])]
        for i in to_delete: del discounts[i]
        if to_delete: save_discounts(discounts)
    if last_update and now >= datetime.fromisoformat(last_update).replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=2):
        new_d = generate_discounts(); new_d["last_update"] = now.strftime("%Y-%m-%d"); save_discounts(new_d); return new_d
    if not discounts or "last_update" not in discounts:
        discounts = generate_discounts(); discounts["last_update"] = now.strftime("%Y-%m-%d"); save_discounts(discounts)
    return discounts

def get_discounted_price(item_id, user_id=None):
    discounts = get_discounts(); shop_items = get_shop_items(user_id)
    if item_id not in shop_items: return 0, 0, None
    current_price = shop_items[item_id]["price"]
    if item_id in discounts and item_id not in ["last_update", "generated_at"]:
        d = discounts[item_id]
        if not d.get("expires") or datetime.now() <= datetime.fromisoformat(d["expires"]):
            return max(1, int(current_price * (1 - d["percent"] / 100))), d["percent"], d
    return current_price, 0, None

def get_user(user_id):
    users = load_users(); uid = str(user_id)
    defaults = {"joined": datetime.now().isoformat(), "username": None, "requests_today": 0, "extra_requests": 0, "image_requests_today": 0, "extra_image_requests": 0, "chat_requests_today": 0, "extra_chat_requests": 0, "chat_image_requests_today": 0, "extra_chat_image_requests": 0, "unlimited_until": None, "image_unlimited_until": None, "chat_unlimited_until": None, "chat_image_unlimited_until": None, "premium_until": None, "chat_premium_until": None, "last_request": None, "total_requests": 0, "total_images": 0, "reset_date": datetime.now().strftime("%Y-%m-%d"), "tokens": START_BONUS, "daily_bonus_claimed": None, "daily_bonus_streak": 0, "last_bonus_date": None, "streak_30_premium_claimed": False, "referral_code": "".join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(8)), "referred_by": None, "referrals": 0, "earned_tokens": 0, "spent_tokens": 0, "donated_tokens": 0, "cashback_earned": 0, "used_promos": [], "waiting_for_image": False, "current_model": "text", "active_preset": None, "warnings": 0, "muted_until": None, "banned": False, "daily_transfer_total": 0, "transfer_reset_date": datetime.now().strftime("%Y-%m-%d"), "last_passive_income": None, "last_notification": None, "notify_interval": DEFAULT_NOTIFY_INTERVAL_PREMIUM}
    if uid not in users: users[uid] = defaults.copy(); save_users(users)
    else:
        for k, v in defaults.items():
            if k not in users[uid]: users[uid][k] = v
        save_users(users)
    today = datetime.now().strftime("%Y-%m-%d")
    if users[uid].get("reset_date") != today:
        for f in ["requests_today", "extra_requests", "image_requests_today", "extra_image_requests", "chat_requests_today", "extra_chat_requests", "chat_image_requests_today", "extra_chat_image_requests"]: users[uid][f] = 0
        users[uid]["reset_date"] = today; save_users(users)
    if users[uid].get("transfer_reset_date") != today: users[uid]["daily_transfer_total"] = 0; users[uid]["transfer_reset_date"] = today; save_users(users)
    return users[uid]

def process_passive_income(user_id):
    users = load_users(); uid = str(user_id)
    if uid not in users or not is_premium(user_id): return 0
    now = datetime.now(); last_income = users[uid].get("last_passive_income")
    hours_passed = min((now - datetime.fromisoformat(last_income)).total_seconds() / 3600 if last_income else 1, PASSIVE_INCOME_MAX_HOURS)
    income = int(hours_passed * PASSIVE_INCOME_HOURLY)
    if income > 0: users[uid]["tokens"] = users[uid].get("tokens", 0) + income; users[uid]["earned_tokens"] = users[uid].get("earned_tokens", 0) + income; users[uid]["last_passive_income"] = now.isoformat(); save_users(users)
    return income

# ═══════════════════════════════════════════
# 🔔 СИСТЕМА УМНЫХ УВЕДОМЛЕНИЙ
# ═══════════════════════════════════════════

async def send_smart_notification(user_id, context):
    """Отправляет умное уведомление пользователю"""
    user = get_user(user_id)
    premium = is_premium(user_id)
    interval = user.get("notify_interval", NOTIFY_INTERVAL_FREE) if premium else NOTIFY_INTERVAL_FREE
    
    # Проверяем интервал
    last_notify = user.get("last_notification")
    if last_notify:
        last_time = datetime.fromisoformat(last_notify)
        hours_passed = (datetime.now() - last_time).total_seconds() / 3600
        if hours_passed < interval: return
    
    # Обновляем время уведомления
    users = load_users(); uid = str(user_id)
    users[uid]["last_notification"] = datetime.now().isoformat(); save_users(users)
    
    rate_data = get_token_rate(); rate = rate_data.get("rate", 0.005)
    streak = user.get("daily_bonus_streak", 0)
    tokens = user.get("tokens", 0); usd = tokens * rate
    donated_total, _, _ = get_donation_stats()
    passive_income = process_passive_income(user_id)
    
    premium_icon = "💎" if premium else ""
    notify_type = "PREMIUM" if premium else "БЕСПЛАТНАЯ"
    
    text = (
        f"🔔 СВОДКА {notify_type} {premium_icon}\n━━━━━━━━━━━━━━━━\n\n"
        f"💰 Баланс: {tokens:,} 💮 (~${usd:.2f})\n"
        f"💮 Курс NBT: 1 = ${rate:.8f}\n"
        f"🔥 Серия бонусов: {streak} дн.\n"
    )
    
    if passive_income > 0:
        text += f"💤 Пассивный доход: +{passive_income} 💮 (5 💮/час)\n"
    
    text += f"🌍 Всего сожжено: {donated_total:,} 💮\n\n"
    
    if premium:
        prem_until = user.get("premium_until")
        if prem_until:
            remaining = datetime.fromisoformat(prem_until) - datetime.now()
            if remaining.total_seconds() > 0:
                text += f"💎 Premium: активно (осталось {remaining.days} дн. {remaining.seconds // 3600} ч.)\n"
                text += f"🔄 Скидка на продление: {PREMIUM_RENEWAL_DISCOUNT}%\n"
                text += f"🔔 Интервал уведомлений: каждые {interval} ч.\n"
        text += f"🔄 Кэшбек с чат-покупок: {CASHBACK_PERCENT}% (накоплено: {user.get('cashback_earned', 0):,} 💮)\n"
        
        if prem_until:
            remaining = datetime.fromisoformat(prem_until) - datetime.now()
            if timedelta(0) < remaining <= timedelta(hours=6):
                text += f"\n⚠️ Premium истекает через {remaining.seconds // 3600} ч.!\nПродлите в /premium со скидкой {PREMIUM_RENEWAL_DISCOUNT}%!\n"
    else:
        text += f"\n💡 С Premium:\n• Безлимит текста и фото\n• Пассивный доход 5 💮/час\n• Уведомления от 1 часа\n• 10 проф. пресетов\n💎 /premium — узнать больше\n"
    
    text += f"\n━━━━━━━━━━━━━━━━\n🕐 Следующая: через {interval} ч."
    try: await context.bot.send_message(user_id, text)
    except: pass

def is_premium(user_id):
    u = get_user(user_id); p = u.get("premium_until")
    return p and datetime.now() < datetime.fromisoformat(p) if p else False

def is_chat_premium(chat_id):
    c = load_chats().get(str(chat_id), {})
    if isinstance(c, list): return False
    p = c.get("premium_until")
    return p and datetime.now() < datetime.fromisoformat(p) if p else False

def add_request(user_id, chat_type="private"):
    users = load_users(); uid = str(user_id)
    if uid in users:
        if chat_type in ["group", "supergroup"]: users[uid]["chat_requests_today"] = users[uid].get("chat_requests_today", 0) + 1
        else: users[uid]["requests_today"] = users[uid].get("requests_today", 0) + 1
        users[uid]["total_requests"] = users[uid].get("total_requests", 0) + 1; users[uid]["last_request"] = datetime.now().isoformat(); save_users(users)

def add_image_request(user_id, chat_type="private"):
    users = load_users(); uid = str(user_id)
    if uid in users:
        if chat_type in ["group", "supergroup"]: users[uid]["chat_image_requests_today"] = users[uid].get("chat_image_requests_today", 0) + 1
        else: users[uid]["image_requests_today"] = users[uid].get("image_requests_today", 0) + 1
        users[uid]["total_images"] = users[uid].get("total_images", 0) + 1; users[uid]["last_request"] = datetime.now().isoformat(); save_users(users)

def can_request(user_id, chat_type="private", chat_id=None):
    if chat_type == "private" and is_premium(user_id): return True
    if chat_type in ["group", "supergroup"] and chat_id and is_chat_premium(chat_id): return True
    u = get_user(user_id)
    if chat_type == "private" and u.get("unlimited_until") and datetime.now() < datetime.fromisoformat(u["unlimited_until"]): return True
    if chat_type in ["group", "supergroup"] and u.get("chat_unlimited_until") and datetime.now() < datetime.fromisoformat(u["chat_unlimited_until"]): return True
    if chat_type in ["group", "supergroup"]: return u.get("chat_requests_today", 0) < (CHAT_DAILY_LIMIT + u.get("extra_chat_requests", 0))
    return u.get("requests_today", 0) < (DAILY_LIMIT + u.get("extra_requests", 0))

def can_image_request(user_id, chat_type="private", chat_id=None):
    if chat_type == "private" and is_premium(user_id): return True
    if chat_type in ["group", "supergroup"] and chat_id and is_chat_premium(chat_id): return True
    u = get_user(user_id)
    if chat_type == "private" and u.get("image_unlimited_until") and datetime.now() < datetime.fromisoformat(u["image_unlimited_until"]): return True
    if chat_type in ["group", "supergroup"] and u.get("chat_image_unlimited_until") and datetime.now() < datetime.fromisoformat(u["chat_image_unlimited_until"]): return True
    if chat_type in ["group", "supergroup"]: return u.get("chat_image_requests_today", 0) < (CHAT_IMAGE_LIMIT + u.get("extra_chat_image_requests", 0))
    return u.get("image_requests_today", 0) < (IMAGE_DAILY_LIMIT + u.get("extra_image_requests", 0))

def remaining(user_id, chat_type="private", chat_id=None):
    if chat_type == "private" and is_premium(user_id): return "премиум"
    if chat_type in ["group", "supergroup"] and chat_id and is_chat_premium(chat_id): return "премиум"
    u = get_user(user_id)
    if chat_type == "private" and u.get("unlimited_until") and datetime.now() < datetime.fromisoformat(u["unlimited_until"]): return "безлимит"
    if chat_type in ["group", "supergroup"] and u.get("chat_unlimited_until") and datetime.now() < datetime.fromisoformat(u["chat_unlimited_until"]): return "безлимит"
    if chat_type in ["group", "supergroup"]: return max(0, CHAT_DAILY_LIMIT + u.get("extra_chat_requests", 0) - u.get("chat_requests_today", 0))
    return max(0, DAILY_LIMIT + u.get("extra_requests", 0) - u.get("requests_today", 0))

def image_remaining(user_id, chat_type="private", chat_id=None):
    if chat_type == "private" and is_premium(user_id): return "премиум"
    if chat_type in ["group", "supergroup"] and chat_id and is_chat_premium(chat_id): return "премиум"
    u = get_user(user_id)
    if chat_type == "private" and u.get("image_unlimited_until") and datetime.now() < datetime.fromisoformat(u["image_unlimited_until"]): return "безлимит"
    if chat_type in ["group", "supergroup"] and u.get("chat_image_unlimited_until") and datetime.now() < datetime.fromisoformat(u["chat_image_unlimited_until"]): return "безлимит"
    if chat_type in ["group", "supergroup"]: return max(0, CHAT_IMAGE_LIMIT + u.get("extra_chat_image_requests", 0) - u.get("chat_image_requests_today", 0))
    return max(0, IMAGE_DAILY_LIMIT + u.get("extra_image_requests", 0) - u.get("image_requests_today", 0))

def add_tokens(user_id, amount):
    users = load_users(); uid = str(user_id)
    if uid not in users: get_user(user_id); users = load_users()
    users[uid]["tokens"] = users[uid].get("tokens", 0) + amount; users[uid]["earned_tokens"] = users[uid].get("earned_tokens", 0) + amount; save_users(users)

def remove_tokens(user_id, amount):
    users = load_users()
    if str(user_id) in users: users[str(user_id)]["tokens"] = users[str(user_id)].get("tokens", 0) - amount; users[str(user_id)]["spent_tokens"] = users[str(user_id)].get("spent_tokens", 0) + amount; save_users(users)

def process_cashback(user_id, amount, item_id=None):
    if not is_premium(user_id): return 0
    if item_id:
        item = SHOP_ITEMS_BASE.get(item_id, {})
        if item.get("location") != "chat": return 0
    cashback = int(amount * CASHBACK_PERCENT / 100)
    if cashback > 0:
        users = load_users(); uid = str(user_id)
        if uid in users: users[uid]["tokens"] = users[uid].get("tokens", 0) + cashback; users[uid]["earned_tokens"] = users[uid].get("earned_tokens", 0) + cashback; users[uid]["cashback_earned"] = users[uid].get("cashback_earned", 0) + cashback; save_users(users)
        return cashback
    return 0

def donate_tokens(user_id, amount):
    users = load_users(); uid = str(user_id)
    max_don = PREMIUM_MAX_DONATION if is_premium(user_id) else MAX_DONATION
    if amount > max_don: return False
    if uid in users: users[uid]["tokens"] = users[uid].get("tokens", 0) - amount; users[uid]["spent_tokens"] = users[uid].get("spent_tokens", 0) + amount; users[uid]["donated_tokens"] = users[uid].get("donated_tokens", 0) + amount; save_users(users); log_donation(user_id, amount); return True
    return False

def get_tokens(user_id): return get_user(user_id).get("tokens", 0)

def create_promo(code, amount, max_uses=0):
    promos = load_promos(); promos[code.upper()] = {"amount": amount, "max_uses": max_uses, "used_by": [], "created": datetime.now().isoformat()}; save_promos(promos)

def use_promo(user_id, code):
    promos = load_promos(); code = code.upper()
    if code not in promos: return False, "Не найден"
    p = promos[code]
    if p["max_uses"] > 0 and len(p["used_by"]) >= p["max_uses"]: return False, "Лимит"
    if str(user_id) in p["used_by"]: return False, "Уже использован"
    add_tokens(user_id, p["amount"]); p["used_by"].append(str(user_id)); save_promos(promos); return True, p["amount"]

def moderate_content(text):
    for pat in [re.compile(w, re.IGNORECASE) for w in [r'\b(?:взлом|хак|hack|crack|warez)\b', r'\b(?:наркотик|drugs)\b', r'\b(?:оружие|weapon|gun|бомба|bomb)\b', r'\b(?:дет[иь] порно|child porn|педофил|pedo)\b', r'\b(?:уби[йт]|kill|murder)\b', r'\b(?:террор|terror|ИГИЛ|ISIS)\b']]:
        if pat.search(text): return False, "normal", "Запрещённый контент"
    return True, None, None

def is_user_muted(user_id):
    u = get_user(user_id)
    if u.get("banned"): return True
    m = u.get("muted_until"); return m and datetime.now() < datetime.fromisoformat(m) if m else False

def warn_user(user_id, severity="normal"):
    users = load_users(); uid = str(user_id)
    if severity == "severe": users[uid]["banned"] = True; save_users(users); return True, "Заблокирован"
    users[uid]["warnings"] = users[uid].get("warnings", 0) + 1
    if users[uid]["warnings"] >= 5: users[uid]["banned"] = True; save_users(users); return True, "Заблокирован"
    elif users[uid]["warnings"] >= 3: users[uid]["muted_until"] = (datetime.now() + timedelta(hours=6)).isoformat(); save_users(users); return True, "Мут на 6 часов"
    save_users(users); return False, f"Предупреждение {users[uid]['warnings']}/5"

def is_chat_owner(chat_id, user_id):
    c = load_chats().get(str(chat_id), {})
    if isinstance(c, list): return str(user_id) in c
    return str(user_id) in c.get("owners", [])

def add_chat_owner(chat_id, user_id):
    chats = load_chats(); cid = str(chat_id)
    if cid not in chats or isinstance(chats[cid], list): chats[cid] = {"owners": chats.get(cid, []), "premium_until": None}
    if str(user_id) not in chats[cid]["owners"]: chats[cid]["owners"].append(str(user_id)); save_chats(chats)

async def generate_image(prompt):
    try:
        r = client.images.generate(model=IMAGE_MODEL, prompt=prompt, size="1024x1024")
        return base64.b64decode(r.data[0].b64_json), None
    except Exception as e: return None, str(e)

def main_reply_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("💬 NeBlock AI V2"), KeyboardButton("🎨 NeBlock Images V2")],
        [KeyboardButton("👤 Профиль"), KeyboardButton("🛒 Магазин")],
        [KeyboardButton("🔥 Награды"), KeyboardButton("💸 Перевод")],
        [KeyboardButton("🌍 Донат"), KeyboardButton("💮 Курс NBT")],
        [KeyboardButton("💎 Premium"), KeyboardButton("📝 Пресеты")],
    ], resize_keyboard=True)

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("ℹ️ О боте", callback_data="about"), InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🧠 Модели", callback_data="models"), InlineKeyboardButton("💎 Premium", callback_data="premium_menu")],
        [InlineKeyboardButton("🔥 Награды", callback_data="earn"), InlineKeyboardButton("💮 Курс NBT", callback_data="tokenrate")],
        [InlineKeyboardButton("💸 Перевод", callback_data="transfer"), InlineKeyboardButton("🌍 Донат", callback_data="donate_info")],
        [InlineKeyboardButton("📝 Пресеты", callback_data="presets_menu")],
    ])

def back_button(): return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="menu")]])

def shop_keyboard(location="private", user_id=None):
    keyboard = []
    discounts = get_discounts(); shop_items = get_shop_items(user_id)
    active = {k: v for k, v in discounts.items() if k not in ["last_update", "generated_at"]}
    if active:
        legendary = any(d.get("type") == "legendary" for d in active.values())
        keyboard.append([InlineKeyboardButton("🌟 ЛЕГЕНДАРНАЯ СКИДКА! 🌟" if legendary else "🎫 Скидки", callback_data="discounts_info")])
    cats = {"private": [("📝 Текст", "text"), ("🎨 Фото", "image"), ("⭐ Premium", "premium")], "chat": [("👥 Запросы", "chat"), ("🖼️ Фото", "chat_image"), ("⭐ Premium", "chat_premium")]}
    for label, cat in cats.get(location, cats["private"]):
        items_in_cat = False
        for item_id, item in shop_items.items():
            if item["category"] == cat and item.get("location") == location:
                if not items_in_cat: keyboard.append([InlineKeyboardButton(f"── {label} ──", callback_data="none")]); items_in_cat = True
                price, percent, disc = get_discounted_price(item_id, user_id)
                if percent > 0 and disc:
                    if disc.get("type") == "legendary": price_text = "🌟 БЕСПЛАТНО!"
                    else: price_text = f"{disc.get('color', '🟢')} {price} 💮 -{percent}%"
                else: price_text = f"{price} 💮"
                keyboard.append([InlineKeyboardButton(f"{item['icon']} {item['name']} — {price_text}", callback_data=f"buy_{item_id}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="menu")])
    return InlineKeyboardMarkup(keyboard)

def confirm_keyboard(item_id):
    return InlineKeyboardMarkup([[InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_{item_id}"), InlineKeyboardButton("❌ Отмена", callback_data="shop")]])

def transfer_confirm_keyboard(to_id, amount):
    return InlineKeyboardMarkup([[InlineKeyboardButton("✅ Подтвердить перевод", callback_data=f"transfer_confirm_{to_id}_{amount}")], [InlineKeyboardButton("❌ Отменить", callback_data="transfer_cancel")]])

def donate_confirm_keyboard(amount):
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔥 Подтвердить сжигание", callback_data=f"donate_confirm_{amount}")], [InlineKeyboardButton("❌ Отменить", callback_data="donate_cancel")]])

def earn_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🎁 Забрать ежедневный бонус", callback_data="daily_bonus")], [InlineKeyboardButton("👥 Реферальная ссылка", callback_data="ref_link")], [InlineKeyboardButton("📅 Подробно о наградах", callback_data="streak_info")], [InlineKeyboardButton("🔙 Назад", callback_data="menu")]])

def limit_reached_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🛒 Купить запросы", callback_data="shop"), InlineKeyboardButton("🔥 Награды", callback_data="earn")], [InlineKeyboardButton("💎 Premium", callback_data="premium_menu")]])

def presets_keyboard():
    keyboard = []
    for pid, preset in PREMIUM_PRESETS.items():
        keyboard.append([InlineKeyboardButton(f"{preset['icon']} {preset['name']}", callback_data=f"preset_{pid}")])
    keyboard.append([InlineKeyboardButton("❌ Без пресета", callback_data="preset_off")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="menu")])
    return InlineKeyboardMarkup(keyboard)

def notify_keyboard():
    """Клавиатура выбора интервала уведомлений"""
    keyboard = []
    for interval in PREMIUM_NOTIFY_OPTIONS:
        label = f"Каждые {interval} ч." + (" (чаще)" if interval <= 3 else "")
        keyboard.append([InlineKeyboardButton(label, callback_data=f"notify_{interval}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="premium_menu")])
    return InlineKeyboardMarkup(keyboard)

# ═══════════════════════════════════════════
# ОБРАБОТЧИКИ КОМАНД
# ═══════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id; user = get_user(user_id); chat_type = update.effective_chat.type
    username = update.effective_user.username
    if username: users = load_users(); users[str(user_id)]["username"] = username; save_users(users)
    
    passive_income = process_passive_income(user_id)
    await send_smart_notification(user_id, context)
    
    if context.args and context.args[0].startswith("ref_"):
        ref_code = context.args[0].replace("ref_", ""); users = load_users(); uid = str(user_id)
        for u_id, u_data in users.items():
            if u_data.get("referral_code") == ref_code and u_id != uid and not users[uid].get("referred_by"):
                users[uid]["referred_by"] = u_id
                ref_bonus = PREMIUM_REFERRAL_BONUS if is_premium(int(u_id)) else REFERRAL_BONUS
                inv_bonus = PREMIUM_INVITED_BONUS if is_premium(int(u_id)) else INVITED_BONUS
                add_tokens(int(u_id), ref_bonus); add_tokens(user_id, inv_bonus)
                users[u_id]["referrals"] = users[u_id].get("referrals", 0) + 1; save_users(users)
                try: await context.bot.send_message(int(u_id), f"🎉 Реферал!\n💰 +{ref_bonus} 💮")
                except: pass
                break
    
    if chat_type in ["group", "supergroup"]:
        await update.message.reply_text(f"🧠 NeBlock AI V{BOT_VERSION}\n\n💬 @{context.bot.username} вопрос\n🎨 /genimage | 💸 /transfer\n💎 /premium | 👤 /profile | 🆔 /id")
        return
    
    premium = "💎 Активен" if is_premium(user_id) else "Не активен"
    rate_data = get_token_rate(); rate = rate_data.get("rate", 0.005)
    passive_text = f"\n💤 Пассивный доход: +{passive_income} 💮" if passive_income > 0 else ""
    notify_interval = user.get("notify_interval", DEFAULT_NOTIFY_INTERVAL_PREMIUM)
    notify_text = f"\n🔔 Уведомления: каждые {notify_interval} ч." if is_premium(user_id) else "\n🔔 Уведомления: каждые 24 ч."
    
    await update.message.reply_text(
        f"🧠 NeBlock AI V{BOT_VERSION}\n━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💎 Premium: {premium}\n💰 Баланс: {user.get('tokens', 0):,} 💮 (~${user.get('tokens', 0) * rate:.2f})\n"
        f"💮 Курс: 1 NBT = ${rate:.8f}\n🔥 Серия: {user.get('daily_bonus_streak', 0)} дн.\n"
        f"📊 Лимиты: {DAILY_LIMIT} текст + {IMAGE_DAILY_LIMIT} фото/день{passive_text}{notify_text}\n\n"
        f"👇 Выберите модель:",
        reply_markup=main_reply_keyboard()
    )

async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if context.args:
        try: user_id = int(context.args[0])
        except: pass
    username = update.effective_user.username
    name = f"@{username}" if username else "Не указан"
    await update.message.reply_text(f"🆔 ИНФОРМАЦИЯ\n━━━━━━━━━━━━━━━━\n\n👤 Имя: {name}\n🆔 ID: `{user_id}`\n\n💡 /profile {user_id} — профиль", parse_mode="Markdown")

async def notify_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Настройка интервала уведомлений (Premium)"""
    user_id = update.effective_user.id
    if not is_premium(user_id):
        await update.message.reply_text("❌ Настройка уведомлений доступна только Premium пользователям!\n💎 /premium — купить Premium\n\nFree пользователи получают уведомления раз в 24 часа.")
        return
    
    if context.args:
        try:
            interval = int(context.args[0])
            if interval in PREMIUM_NOTIFY_OPTIONS:
                users = load_users(); uid = str(user_id)
                users[uid]["notify_interval"] = interval; save_users(users)
                await update.message.reply_text(f"✅ Интервал уведомлений: каждые {interval} ч.\n\nСледующая сводка придёт через {interval} ч. после последней.")
                return
        except: pass
        await update.message.reply_text(f"❌ Доступные интервалы: {', '.join(map(str, PREMIUM_NOTIFY_OPTIONS))} часов\nПример: /notify 3")
        return
    
    user = get_user(user_id)
    current = user.get("notify_interval", DEFAULT_NOTIFY_INTERVAL_PREMIUM)
    await update.message.reply_text(
        f"🔔 НАСТРОЙКА УВЕДОМЛЕНИЙ\n━━━━━━━━━━━━━━━━\n\n"
        f"Текущий интервал: каждые {current} ч.\n\n"
        f"Выберите новый интервал:",
        reply_markup=notify_keyboard()
    )

async def premium_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id; premium = is_premium(user_id)
    shop_items = get_shop_items(user_id)
    
    if premium:
        user = get_user(user_id); prem_until = user.get("premium_until")
        remaining_text = ""
        if prem_until:
            remaining = datetime.fromisoformat(prem_until) - datetime.now()
            if remaining.total_seconds() > 0:
                remaining_text = f"⏳ Осталось: {remaining.days} дн. {remaining.seconds // 3600} ч.\n🔄 Скидка на продление: {PREMIUM_RENEWAL_DISCOUNT}%\n"
        
        active_preset = user.get("active_preset")
        preset_name = "Нет"
        if active_preset:
            p = PREMIUM_PRESETS.get(active_preset)
            if p: preset_name = f"{p['icon']} {p['name']}"
        
        notify_interval = user.get("notify_interval", DEFAULT_NOTIFY_INTERVAL_PREMIUM)
        
        text = (
            f"💎 PREMIUM-МЕНЮ\n━━━━━━━━━━━━━━━━\n\n"
            f"💎 Статус: АКТИВЕН\n{remaining_text}\n"
            f"📊 ВАШИ ПРИВИЛЕГИИ:\n"
            f"• Безлимит текста и фото в ЛС\n"
            f"• 10 профессиональных пресетов\n"
            f"• Активный пресет: {preset_name}\n"
            f"• Кэшбек {CASHBACK_PERCENT}% на чат-покупки (накоплено: {user.get('cashback_earned', 0):,} 💮)\n"
            f"• Скидка {PREMIUM_RENEWAL_DISCOUNT}% на продление Premium\n"
            f"• Скидка {PREMIUM_CHAT_DISCOUNT}% на чат-товары\n"
            f"• Пассивный доход: {PASSIVE_INCOME_HOURLY} 💮/час (до {PASSIVE_INCOME_HOURLY * PASSIVE_INCOME_MAX_HOURS} 💮/день)\n"
            f"• Рефералы: {PREMIUM_REFERRAL_BONUS}/{PREMIUM_INVITED_BONUS} 💮\n"
            f"• Лимит перевода: {PREMIUM_MAX_TRANSFER:,} 💮 (налог 0-10%)\n"
            f"• Лимит доната: {PREMIUM_MAX_DONATION:,} 💮\n"
            f"• Умные уведомления: каждые {notify_interval} ч. (/notify)\n"
            f"• Значок 💎 в профиле и топах\n\n"
            f"🛒 /buy_premium | 📝 /presets | 🔔 /notify"
        )
    else:
        text = (
            f"💎 NeBlock Premium\n━━━━━━━━━━━━━━━━\n\n"
            f"📊 СРАВНЕНИЕ FREE vs PREMIUM:\n\n"
            f"┌──────────────────────────┬────────────┬────────────┐\n"
            f"│ Возможность              │    FREE    │  PREMIUM   │\n"
            f"├──────────────────────────┼────────────┼────────────┤\n"
            f"│ Текстовые запросы (ЛС)   │  {DAILY_LIMIT}/день     │ Безлимит   │\n"
            f"│ Генерация фото (ЛС)      │  {IMAGE_DAILY_LIMIT}/день     │ Безлимит   │\n"
            f"│ Профессиональные пресеты │     ❌     │  10 ролей  │\n"
            f"│ Кэшбек с чат-покупок     │     0%     │    {CASHBACK_PERCENT}%     │\n"
            f"│ Скидка на продление      │     -      │    {PREMIUM_RENEWAL_DISCOUNT}%     │\n"
            f"│ Скидка на чат-товары     │     -      │    {PREMIUM_CHAT_DISCOUNT}%     │\n"
            f"│ Пассивный доход          │     ❌     │ {PASSIVE_INCOME_HOURLY} 💮/час     │\n"
            f"│ Реферальный бонус        │ {REFERRAL_BONUS}/{INVITED_BONUS} 💮      │ {PREMIUM_REFERRAL_BONUS}/{PREMIUM_INVITED_BONUS} 💮      │\n"
            f"│ Макс. перевод            │ {MAX_TRANSFER:,} 💮  │ {PREMIUM_MAX_TRANSFER:,} 💮  │\n"
            f"│ Налог на перевод         │   0-15%    │   0-10%    │\n"
            f"│ Макс. донат              │ {MAX_DONATION:,} 💮 │ {PREMIUM_MAX_DONATION:,} 💮│\n"
            f"│ Умные уведомления        │ каждые 24ч │ 1-24ч     │\n"
            f"│ Настройка уведомлений    │     ❌     │     ✅     │\n"
            f"│ Значок 💎                │     ❌     │     ✅     │\n"
            f"└──────────────────────────┴────────────┴────────────┘\n\n"
            f"🛒 ТАРИФЫ:\n"
            f"⭐ 1 день — {shop_items.get('premium_day', {}).get('price', '?')} 💮\n"
            f"⭐ 7 дней — {shop_items.get('premium_week', {}).get('price', '?')} 💮 (-28%)\n"
            f"💎 30 дней — {shop_items.get('premium_30d', {}).get('price', '?')} 💮 (-25%)\n"
            f"🚀 60 дней — {shop_items.get('premium_60d', {}).get('price', '?')} 💮 (-37%)\n"
            f"👑 90 дней — {shop_items.get('premium_90d', {}).get('price', '?')} 💮 (-50%)\n"
            f"💫 1 год — {shop_items.get('premium_year', {}).get('price', '?')} 💮 (-72%)\n"
            f"🌟 Навсегда — {shop_items.get('premium_forever', {}).get('price', '?')} 💮\n\n"
            f"🛒 /buy_premium — купить Premium\n"
            f"💡 30-й день серии даёт Premium 1 день!"
        )
    
    keyboard = []
    keyboard.append([InlineKeyboardButton("🛒 Купить/Продлить Premium", callback_data="premium_shop")])
    if premium:
        keyboard.append([InlineKeyboardButton("📝 Управление пресетами", callback_data="presets_menu")])
        keyboard.append([InlineKeyboardButton("🔔 Настройка уведомлений", callback_data="notify_menu")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="menu")])
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def buy_premium_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(f"🛒 ПОКУПКА PREMIUM\n━━━━━━━━━━━━━━━━\n💰 Баланс: {get_tokens(user_id):,} 💮\n\nВыберите тариф:", reply_markup=shop_keyboard("private", user_id))

async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_id = update.effective_user.id
    if context.args:
        try: target_id = int(context.args[0])
        except: pass
    u = get_user(target_id)
    if not u.get("joined"): await update.message.reply_text("❌ Не найден."); return
    username = f"@{u['username']}" if u.get("username") else f"ID:{target_id}"
    premium_icon = " 💎" if is_premium(target_id) else ""
    joined = datetime.fromisoformat(u.get("joined", "")).strftime("%d.%m.%Y") if u.get("joined") else "?"
    premium_status = "💎 Активен" if is_premium(target_id) else "Не активен"
    rate_data = get_token_rate(); usd = u.get("tokens", 0) * rate_data.get("rate", 0.005)
    
    premium_info = ""
    if is_premium(target_id):
        prem_until = u.get("premium_until")
        if prem_until:
            remaining = datetime.fromisoformat(prem_until) - datetime.now()
            if remaining.total_seconds() > 0:
                notify_interval = u.get("notify_interval", DEFAULT_NOTIFY_INTERVAL_PREMIUM)
                premium_info = f"\n⏳ Premium: {remaining.days} дн. {remaining.seconds // 3600} ч.\n🔄 Кэшбек: {u.get('cashback_earned', 0):,} 💮\n🔔 Уведомления: каждые {notify_interval} ч."
    
    text = (
        f"👤 ПРОФИЛЬ{premium_icon}\n━━━━━━━━━━━━━━━━\n\n"
        f"🆔 {username}\n📅 В боте с: {joined}\n💎 Premium: {premium_status}{premium_info}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💰 Баланс: {u.get('tokens', 0):,} 💮 (~${usd:.2f})\n"
        f"🔥 Серия: {u.get('daily_bonus_streak', 0)} дн.\n"
        f"💎 Заработано: {u.get('earned_tokens', 0):,} 💮\n"
        f"🌍 Донатов: {u.get('donated_tokens', 0):,} 💮\n"
        f"👥 Рефералов: {u.get('referrals', 0)}\n"
        f"📈 Запросов: {u.get('total_requests', 0):,} | Фото: {u.get('total_images', 0):,}\n"
        f"🆔 ID: `{target_id}`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def streak_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id; streak = get_user(user_id).get("daily_bonus_streak", 0)
    rate = get_token_rate().get("rate", 0.005)
    text = f"🔥 ВАША СЕРИЯ: {streak} дн.\n━━━━━━━━━━━━━━━━\n\n"
    if streak == 0: text += "🌱 Начните сегодня!\n"
    elif streak >= MAX_STREAK_DAY: text += f"👑 Максимум ({MAX_STREAK_DAY} дней)!\n"
    else:
        nr = STREAK_BASE_REWARDS.get(streak + 1, STREAK_BASE_REWARDS[MAX_STREAK_DAY])
        rm = max(0.5, min(1.5, 1.0 + (rate * 10 - 0.1)))
        text += f"➡️ Завтра: {nr['icon']} {nr['name']}\n   ~{max(1, int(nr['base_min']*rm))}-{max(1, int(nr['base_max']*rm))} 💮\n\n"
    text += f"📐 Курс: ${rate:.8f}\n⚠️ До 00:00 МСК!"
    await update.message.reply_text(text)

async def tokenrate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rd = get_token_rate(); history = load_json(TOKEN_HISTORY_FILE)
    text = f"💮 КУРС NBT\n━━━━━━━━━━━━━━━━\n\n💰 1 NBT = ${rd.get('rate', 0.005):.8f}\n💎 Кап: ${rd.get('market_cap', 0):,.2f}\n🪙 В обороте: {rd.get('total_supply', 0):,} NBT\n🔥 Сожжено: {rd.get('total_donated', 0):,} 💮\n📅 {rd.get('day_icon', '📊')} {rd.get('day_name', '')}\n🕐 Обновление: {rd.get('next_update', '')}\n\n💡 Курс влияет на ежедневные награды!\n💡 Донаты повышают курс!\n\n📈 История за 7 дней:\n"
    for date, h in sorted(history.items())[-7:]: text += f"• {date}: ${h.get('rate', 0):.8f}\n"
    await update.message.reply_text(text)

async def donate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    max_don = PREMIUM_MAX_DONATION if is_premium(user_id) else MAX_DONATION
    if not context.args: await update.message.reply_text(f"{DONATE_INFO_TEXT}\n\n/donate СУММА\nЛимит: до {max_don:,} 💮"); return
    try: amount = int(context.args[0])
    except: return
    if amount < 1 or amount > max_don: await update.message.reply_text(f"❌ Лимит: 1 – {max_don:,} 💮"); return
    if get_user(user_id).get("tokens", 0) < amount: await update.message.reply_text("❌ Недостаточно!"); return
    await update.message.reply_text(f"🌍 ПОДТВЕРЖДЕНИЕ\n━━━━━━━━━━━━━━━━\n\n💰 {amount:,} 💮\n💎 Баланс: {get_tokens(user_id):,} → {get_tokens(user_id) - amount:,} 💮\n\nПодтвердите:", reply_markup=donate_confirm_keyboard(amount))

async def donatetop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total, count, top_donors = get_donation_stats()
    if not top_donors: await update.message.reply_text("🌍 ТОП БЛАГОТВОРИТЕЛЕЙ\n\nПока никого."); return
    text = f"🌍 ТОП БЛАГОТВОРИТЕЛЕЙ\n━━━━━━━━━━━━━━━━\n\n🔥 Сожжено: {total:,} 💮 | Донатов: {count}\n\n🏆 ТОП-10:\n"
    users = load_users(); medals = ["🥇", "🥈", "🥉"]
    for i, (uid, donated) in enumerate(top_donors):
        name = f"@{users.get(uid, {}).get('username', '?')}" if uid in users else f"ID:{uid}"
        mark = " 💎" if is_premium(int(uid)) else ""
        medal = medals[i] if i < 3 else f"{i+1}."
        text += f"{medal} {name}{mark}: {donated:,} 💮\n"
    await update.message.reply_text(text)

async def genimage_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id; chat_type = update.effective_chat.type
    if not context.args: await update.message.reply_text("🎨 /genimage ОПИСАНИЕ\nПример: /genimage красивый закат"); return
    text = " ".join(context.args)
    if not can_image_request(user_id, chat_type): await update.message.reply_text("🚫 Лимит!\n💡 /shop или 💎 Premium"); return
    msg = await update.message.reply_text("🎨 Генерирую...")
    try:
        image_bytes, error = await generate_image(text)
        if image_bytes: add_image_request(user_id, chat_type); await msg.delete(); await update.message.reply_photo(photo=image_bytes, caption=f"🎨 NeBlock Images V2\n📝 {text[:200]}")
        else: await msg.edit_text("❌ Ошибка")
    except: await msg.edit_text("❌ Ошибка")

async def transfer_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id; premium = is_premium(user_id)
    max_t = PREMIUM_MAX_TRANSFER if premium else MAX_TRANSFER
    if not context.args or len(context.args) < 2: await update.message.reply_text(f"{TRANSFER_INFO}\n\n/transfer ID КОЛИЧЕСТВО"); return
    try: to_id = int(context.args[0]); amount = int(context.args[1])
    except: return
    if amount > max_t: await update.message.reply_text(f"❌ Лимит: до {max_t:,} 💮"); return
    sender = get_user(user_id)
    if sender.get("tokens", 0) < amount: await update.message.reply_text("❌ Недостаточно!"); return
    tax, tax_percent, _ = get_transfer_tax(amount, premium)
    receiver = get_user(to_id)
    if not receiver: return
    final_amount = amount - tax
    tax_info = f"Налог: {tax} 💮 ({tax_percent}%)" if tax > 0 else "Без налога"
    await update.message.reply_text(f"⚠️ ПРОВЕРЬТЕ\n━━━━━━━━━━━━━━━━\n👤 ID {to_id}\n💸 {amount:,} 💮\n📊 {tax_info}\n💰 Получит: {final_amount:,} 💮\n\nПодтвердите:", reply_markup=transfer_confirm_keyboard(to_id, amount))

async def presets_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_premium(user_id): await update.message.reply_text("❌ Пресеты только для Premium 💎\n💎 /premium — купить Premium\n\n10 профессиональных ролей ждут вас!"); return
    user = get_user(user_id); active = user.get("active_preset")
    text = "📝 ПРЕСЕТЫ (Premium 💎)\n━━━━━━━━━━━━━━━━\n\n"
    if active:
        p = PREMIUM_PRESETS.get(active)
        if p: text += f"🎯 Выбран: {p['icon']} {p['name']}\n📋 Инструкция добавится к запросу.\n\n"
    text += "Выберите роль:"
    await update.message.reply_text(text, reply_markup=presets_keyboard())

async def chatowner_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]: await update.message.reply_text("❌ Только в чатах!"); return
    chat_id = update.effective_chat.id; user_id = update.effective_user.id; add_chat_owner(chat_id, user_id)
    chats = load_chats(); c = chats.get(str(chat_id), {})
    owners = c.get("owners", []) if isinstance(c, dict) else c
    text = "👑 ВЛАДЕЛЬЦЫ ЧАТА\n━━━━━━━━━━━━━━━━\n\n"
    for i, oid in enumerate(owners, 1): text += f"{i}. ID: {oid}\n"
    await update.message.reply_text(text)

async def chatshop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]: await update.message.reply_text("❌ Только в чатах!"); return
    chat_id = update.effective_chat.id; user_id = update.effective_user.id; add_chat_owner(chat_id, user_id)
    if not is_chat_owner(chat_id, user_id): await update.message.reply_text("❌ Только владельцы чата!"); return
    await update.message.reply_text(f"🛒 МАГАЗИН ЧАТА\n━━━━━━━━━━━━━━━━\n💰 {get_tokens(user_id)} 💮", reply_markup=shop_keyboard("chat", user_id))

# Админ команды
async def admin_give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args or len(context.args) < 2: return
    try: add_tokens(int(context.args[0]), int(context.args[1])); await update.message.reply_text(f"✅ +{context.args[1]} 💮")
    except: pass

async def admin_take(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args or len(context.args) < 2: return
    try:
        uid = str(int(context.args[0])); amount = int(context.args[1])
        if get_user(int(context.args[0])).get("tokens", 0) < amount: return
        users = load_users(); users[uid]["tokens"] = users[uid].get("tokens", 0) - amount; users[uid]["spent_tokens"] = users[uid].get("spent_tokens", 0) + amount; save_users(users)
    except: pass

async def admin_resetuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args: return
    try:
        uid = str(int(context.args[0])); users = load_users()
        if uid in users:
            for f in ["requests_today", "extra_requests", "image_requests_today", "extra_image_requests", "warnings"]: users[uid][f] = 0
            users[uid]["muted_until"] = None; users[uid]["banned"] = False; save_users(users)
    except: pass

async def admin_setpremium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args or len(context.args) < 2: return
    try:
        uid = str(int(context.args[0])); days = int(context.args[1]); users = load_users()
        if uid in users:
            existing = users[uid].get("premium_until")
            base = datetime.fromisoformat(existing) if existing and datetime.now() < datetime.fromisoformat(existing) else datetime.now()
            users[uid]["premium_until"] = (base + timedelta(days=days)).isoformat(); save_users(users)
    except: pass

async def admin_userinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args: return
    try:
        u = get_user(int(context.args[0])); un = u.get("username") or "Не указан"
        await update.message.reply_text(f"👤 @{un}\n💰 {u.get('tokens', 0):,} 💮\n🔥 Серия: {u.get('daily_bonus_streak', 0)} дн.")
    except: pass

async def admin_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    users = load_users()
    top = sorted(users.items(), key=lambda x: x[1].get("tokens", 0), reverse=True)[:10]
    text = "🏆 ТОП ПО ТОКЕНАМ\n\n"
    for i, (uid, data) in enumerate(top, 1):
        name = f"@{data['username']}" if data.get("username") else f"ID:{uid}"
        mark = " 💎" if is_premium(int(uid)) else ""
        text += f"{i}. {name}{mark} — {data.get('tokens', 0):,} 💮\n"
    await update.message.reply_text(text)

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    users = load_users(); rate_data = get_token_rate()
    donated_total, _, _ = get_donation_stats()
    premium_count = sum(1 for u in users.values() if u.get("premium_until") and datetime.now() < datetime.fromisoformat(u["premium_until"]))
    await update.message.reply_text(f"📊 СТАТИСТИКА\n👥 {len(users)} (💎{premium_count})\n💮 {rate_data.get('total_supply', 0):,} NBT\n🔥 {donated_total:,} 💮")

async def admin_forcediscounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    new_d = generate_discounts(); new_d["last_update"] = datetime.now().strftime("%Y-%m-%d"); save_discounts(new_d)

async def admin_force_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    rate_data = load_json(TOKEN_RATE_FILE); rate_data["rate_block"] = ""; save_json(TOKEN_RATE_FILE, rate_data)
    await update.message.reply_text(f"💮 Курс: ${get_token_rate().get('rate', 0.005):.8f}")

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args: return
    text = " ".join(context.args); users = load_users(); sent = 0
    for uid in users:
        try: await context.bot.send_message(int(uid), f"📢 {text}"); sent += 1; await asyncio.sleep(0.05)
        except: pass
    await update.message.reply_text(f"✅ Отправлено: {sent}")

async def admin_create_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args or len(context.args) < 2: return
    create_promo(context.args[0].upper(), int(context.args[1]), int(context.args[2]) if len(context.args) > 2 else 0)

async def admin_promos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    promos = load_promos()
    if not promos: await update.message.reply_text("🎟 ПРОМОКОДЫ\n\nНет активных."); return
    text = "🎟 ПРОМОКОДЫ:\n\n"
    for code, data in promos.items(): text += f"{code}: {data['amount']} 💮 (исп: {len(data['used_by'])}/{data['max_uses'] or '∞'})\n"
    await update.message.reply_text(text)

async def admin_delete_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args: return
    promos = load_promos(); code = context.args[0].upper()
    if code in promos: del promos[code]; save_promos(promos); await update.message.reply_text(f"✅ Промокод {code} удалён.")

async def admin_cleardiscounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    save_discounts({"last_update": datetime.now().strftime("%Y-%m-%d")}); await update.message.reply_text("✅ Скидки очищены.")

async def reply_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text; user_id = update.effective_user.id
    username = update.effective_user.username
    if username: users = load_users(); users[str(user_id)]["username"] = username; save_users(users)
    
    if text == "💬 NeBlock AI V2":
        users = load_users(); users[str(user_id)]["current_model"] = "text"; users[str(user_id)]["waiting_for_image"] = False; save_users(users)
        await update.message.reply_text(f"💬 NeBlock AI V2\n━━━━━━━━━━━━━━━━\n📊 Осталось: {remaining(user_id)}\n📝 Отправьте вопрос.")
        return True
    if text == "🎨 NeBlock Images V2":
        users = load_users(); users[str(user_id)]["current_model"] = "image"; users[str(user_id)]["waiting_for_image"] = True; save_users(users)
        await update.message.reply_text(f"🎨 NeBlock Images V2\n━━━━━━━━━━━━━━━━\n📊 Осталось: {image_remaining(user_id)}\n📝 Опишите изображение.")
        return True
    if text == "👤 Профиль": await profile_cmd(update, context); return True
    if text == "🛒 Магазин": 
        await update.message.reply_text(f"🛒 МАГАЗИН\n━━━━━━━━━━━━━━━━\n💰 {get_tokens(user_id)} 💮\n\nВыберите категорию:", reply_markup=shop_keyboard("private", user_id))
        return True
    if text == "💎 Premium": await premium_cmd(update, context); return True
    if text == "🔥 Награды": 
        streak = get_user(user_id).get("daily_bonus_streak", 0)
        await update.message.reply_text(f"🔥 НАГРАДЫ\n━━━━━━━━━━━━━━━━\n\n📊 Серия: {streak} дн.\n💰 Баланс: {get_tokens(user_id)} 💮\n\nВыберите действие:", reply_markup=earn_keyboard())
        return True
    if text == "📝 Пресеты": await presets_cmd(update, context); return True
    if text == "💸 Перевод": context.user_data["waiting_transfer"] = True; await update.message.reply_text(f"{TRANSFER_INFO}\n\nОтправьте: ID КОЛИЧЕСТВО"); return True
    if text == "🌍 Донат": await update.message.reply_text(DONATE_INFO_TEXT); return True
    if text == "🎟 Промокод": context.user_data["waiting_promo"] = True; await update.message.reply_text("🎟 Отправьте промокод."); return True
    if text == "💮 Курс NBT": await tokenrate_cmd(update, context); return True
    if text == "📚 FAQ": await update.message.reply_text(FAQ_TEXT[:4000]); return True
    if text == "🎫 Скидки":
        discounts = get_discounts(); active = {k: v for k, v in discounts.items() if k not in ["last_update", "generated_at"]}
        txt = f"🎫 СКИДКИ\n━━━━━━━━━━━━━━━━\n\n🔄 Обновление: каждые 2 дня в 9:00 МСК\n\n"
        if not active: txt += "Нет активных скидок."
        else:
            for item_id, disc in sorted(active.items(), key=lambda x: x[1]["percent"], reverse=True):
                item = get_shop_items().get(item_id)
                if item: txt += f"{disc.get('color', '🟢')} {item['icon']} {item['name']}\n   Скидка: -{disc['percent']}% | Тип: {disc.get('type_name', 'Обычная')}\n\n"
        await update.message.reply_text(txt); return True
    return False

async def inline_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer(); user_id = query.from_user.id; data = query.data
    shop_items = get_shop_items(user_id); premium = is_premium(user_id)
    
    if data == "none": return
    if data == "transfer_cancel": await query.edit_message_text("❌ Отменён."); return
    if data == "donate_cancel": await query.edit_message_text("❌ Отменён."); return
    
    if data.startswith("donate_confirm_"):
        amount = int(data.replace("donate_confirm_", ""))
        if get_user(user_id).get("tokens", 0) < amount: await query.edit_message_text("❌ Недостаточно!"); return
        if donate_tokens(user_id, amount):
            donated_total, _, _ = get_donation_stats()
            await query.edit_message_text(f"🌍 ДОНАТ!\n🔥 Сожжено: {amount:,} 💮\n💎 Баланс: {get_tokens(user_id):,} 💮\n🌍 Всего: {donated_total:,} 💮")
        return
    
    if data.startswith("transfer_confirm_"):
        parts = data.split("_")
        if len(parts) >= 4:
            to_id = int(parts[2]); amount = int(parts[3])
            if get_user(user_id).get("tokens", 0) < amount: await query.edit_message_text("❌ Недостаточно!"); return
            tax, tax_percent, _ = get_transfer_tax(amount, premium)
            receiver = get_user(to_id)
            if not receiver: await query.edit_message_text("❌ Не найден!"); return
            final_amount = amount - tax
            users = load_users(); uid_from = str(user_id); uid_to = str(to_id)
            users[uid_from]["tokens"] = users[uid_from].get("tokens", 0) - amount
            users[uid_from]["daily_transfer_total"] = users[uid_from].get("daily_transfer_total", 0) + amount
            users[uid_to]["tokens"] = users[uid_to].get("tokens", 0) + final_amount
            save_users(users); log_transfer(user_id, to_id, amount, tax, final_amount)
            tax_info = f"\n📊 Налог: {tax} 💮 ({tax_percent}%)" if tax > 0 else ""
            await query.edit_message_text(f"✅ ПЕРЕВОД!\n👤 ID {to_id}\n💸 {amount:,} 💮\n💰 Зачислено: {final_amount:,} 💮{tax_info}\n💎 Баланс: {get_tokens(user_id):,} 💮")
        return
    
    # Уведомления
    if data == "notify_menu":
        if not premium: await query.edit_message_text("❌ Только для Premium 💎", reply_markup=back_button()); return
        user = get_user(user_id); current = user.get("notify_interval", DEFAULT_NOTIFY_INTERVAL_PREMIUM)
        await query.edit_message_text(f"🔔 НАСТРОЙКА УВЕДОМЛЕНИЙ\n━━━━━━━━━━━━━━━━\n\nТекущий интервал: каждые {current} ч.\n\nВыберите новый:", reply_markup=notify_keyboard())
        return
    
    if data.startswith("notify_"):
        if not premium: await query.edit_message_text("❌ Только для Premium 💎", reply_markup=back_button()); return
        try:
            interval = int(data.replace("notify_", ""))
            if interval in PREMIUM_NOTIFY_OPTIONS:
                users = load_users(); uid = str(user_id)
                users[uid]["notify_interval"] = interval; save_users(users)
                await query.edit_message_text(f"✅ Интервал: каждые {interval} ч.\nСледующая сводка по расписанию.", reply_markup=back_button())
        except: pass
        return
    
    if data == "premium_shop":
        await query.edit_message_text(f"🛒 ПОКУПКА PREMIUM\n━━━━━━━━━━━━━━━━\n💰 {get_tokens(user_id):,} 💮\n\nВыберите тариф:", reply_markup=shop_keyboard("private", user_id))
        return
    
    if data == "premium_menu":
        await premium_cmd(update, context)
        try: await query.edit_message_text("См. сообщение выше ↑")
        except: pass
        return
    
    if data == "presets_menu":
        if not premium: await query.edit_message_text("❌ Только для Premium 💎", reply_markup=back_button()); return
        await presets_cmd(update, context)
        return
    
    if data.startswith("preset_"):
        if not premium: await query.edit_message_text("❌ Только для Premium 💎", reply_markup=back_button()); return
        preset_id = data.replace("preset_", "")
        if preset_id == "off":
            users = load_users(); users[str(user_id)]["active_preset"] = None; save_users(users)
            await query.edit_message_text("✅ Пресет отключён.", reply_markup=back_button())
            return
        preset = PREMIUM_PRESETS.get(preset_id)
        if preset:
            users = load_users(); users[str(user_id)]["active_preset"] = preset_id; save_users(users)
            await query.edit_message_text(f"✅ {preset['icon']} {preset['name']}\n📝 {preset['description']}\n\nИнструкция добавится к запросу.", reply_markup=back_button())
        return
    
    if data == "menu": await query.edit_message_text(f"🧠 NeBlock AI V{BOT_VERSION}\n━━━━━━━━━━━━━━━━\n\n💰 {get_tokens(user_id):,} 💮\n\nВыберите раздел:", reply_markup=main_menu()); return
    if data == "about": await query.edit_message_text(f"ℹ️ О БОТЕ\n━━━━━━━━━━━━━━━━\n\n📌 Версия: {BOT_VERSION}\n💬 NeBlock AI V2 — текст\n🎨 NeBlock Images V2 — фото\n💎 Premium — безлимит + привилегии\n🔔 Умные уведомления\n🆔 /id — ваш ID\n\n💡 /faq — ответы на вопросы", reply_markup=back_button()); return
    if data == "stats":
        u = get_user(user_id); prem = is_premium(user_id)
        await query.edit_message_text(f"📊 СТАТИСТИКА\n━━━━━━━━━━━━━━━━\n\n💬 Запросов сегодня: {u.get('requests_today', 0)}\n🎨 Генераций: {u.get('image_requests_today', 0)}\n💰 Баланс: {u.get('tokens', 0):,} 💮\n🔥 Серия: {u.get('daily_bonus_streak', 0)} дн.\n🌍 Донатов: {u.get('donated_tokens', 0):,} 💮\n👥 Рефералов: {u.get('referrals', 0)}\n" + (f"🔄 Кэшбек: {u.get('cashback_earned', 0):,} 💮\n" if prem else ""), reply_markup=back_button()); return
    if data == "shop": await query.edit_message_text(f"🛒 МАГАЗИН\n━━━━━━━━━━━━━━━━\n💰 {get_tokens(user_id):,} 💮\n\nВыберите категорию:", reply_markup=shop_keyboard("private", user_id)); return
    if data == "earn": 
        streak = get_user(user_id).get("daily_bonus_streak", 0)
        await query.edit_message_text(f"🔥 НАГРАДЫ\n━━━━━━━━━━━━━━━━\n\n📊 Серия: {streak} дн.\n💰 Баланс: {get_tokens(user_id):,} 💮\n\nВыберите действие:", reply_markup=earn_keyboard()); return
    
    if data == "daily_bonus":
        u = get_user(user_id); today = datetime.now().strftime("%Y-%m-%d")
        if u.get("daily_bonus_claimed") == today: await query.answer("❌ Уже забирали!"); return
        users = load_users(); uid = str(user_id); users[uid]["daily_bonus_claimed"] = today
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        if users[uid].get("last_bonus_date") == yesterday: users[uid]["daily_bonus_streak"] = users[uid].get("daily_bonus_streak", 0) + 1
        elif users[uid].get("last_bonus_date") != today: users[uid]["daily_bonus_streak"] = 1
        users[uid]["last_bonus_date"] = today; streak = users[uid]["daily_bonus_streak"]
        rate = get_token_rate().get("rate", 0.005)
        bonus, icon, day_name, premium_bonus, _ = get_user_bonus(streak, rate)
        if premium_bonus and users[uid].get("streak_30_premium_claimed"): premium_bonus = False
        save_users(users); add_tokens(user_id, bonus)
        premium_text = ""
        if premium_bonus and not users[uid].get("streak_30_premium_claimed"):
            users = load_users()
            existing = users[uid].get("premium_until")
            base = datetime.fromisoformat(existing) if existing and datetime.now() < datetime.fromisoformat(existing) else datetime.now()
            users[uid]["premium_until"] = (base + timedelta(hours=24)).isoformat(); users[uid]["streak_30_premium_claimed"] = True; save_users(users)
            premium_text = "\n🎁 + Premium ЛС 1 день!"
        await query.answer(f"🎉 +{bonus} 💮!")
        await query.edit_message_text(f"🎁 БОНУС!\n━━━━━━━━━━━━━━━━\n\n{icon} {day_name}\n💰 +{bonus} 💮{premium_text}\n💎 Баланс: {get_tokens(user_id):,} 💮\n🔥 Серия: {streak} дн.\n\n⚠️ Заберите завтра до 00:00 МСК!", reply_markup=back_button())
        return
    
    if data == "ref_link":
        user = get_user(user_id); bot_username = (await context.bot.get_me()).username
        bonus_you = PREMIUM_REFERRAL_BONUS if premium else REFERRAL_BONUS
        bonus_friend = PREMIUM_INVITED_BONUS if premium else INVITED_BONUS
        await query.edit_message_text(f"👥 РЕФЕРАЛЫ\n━━━━━━━━━━━━━━━━\n\n🔗 https://t.me/{bot_username}?start=ref_{user.get('referral_code', '')}\n\n💰 Вы: +{bonus_you} 💮 | Друг: +{bonus_friend} 💮\n📊 Рефералов: {user.get('referrals', 0)}\n" + ("💎 Premium бонусы ×3!" if premium else f"\n💡 С Premium: +{PREMIUM_REFERRAL_BONUS}/{PREMIUM_INVITED_BONUS} 💮"), reply_markup=back_button()); return
    
    if data.startswith("confirm_"):
        item_id = data.replace("confirm_", ""); item = shop_items.get(item_id)
        if not item: return
        price, percent, disc = get_discounted_price(item_id, user_id)
        if get_tokens(user_id) < price: await query.answer("❌ Недостаточно!"); return
        
        if item_id == "premium_forever" and is_premium(user_id):
            user = get_user(user_id)
            if user.get("premium_until"):
                if (datetime.fromisoformat(user["premium_until"]) - datetime.now()).days > 36500: await query.answer("❌ Уже Premium НАВСЕГДА!"); return
        
        remove_tokens(user_id, price)
        cashback = process_cashback(user_id, price, item_id)
        users = load_users(); uid = str(user_id)
        
        actions = {"extra5": ("extra_requests", 5), "extra10": ("extra_requests", 10), "extra50": ("extra_requests", 50), "image1": ("extra_image_requests", 1), "image5": ("extra_image_requests", 5), "image20": ("extra_image_requests", 20), "chat_extra10": ("extra_chat_requests", 10), "chat_extra50": ("extra_chat_requests", 50), "chat_image5": ("extra_chat_image_requests", 5), "chat_image20": ("extra_chat_image_requests", 20)}
        time_actions = {"unlimited_1h": ("unlimited_until", 1), "unlimited_24h": ("unlimited_until", 24), "unlimited_7d": ("unlimited_until", 168), "image_unlimited_1h": ("image_unlimited_until", 1), "chat_unlimited_1h": ("chat_unlimited_until", 1), "chat_unlimited_24h": ("chat_unlimited_until", 24)}
        premium_actions = {"premium_day": 1, "premium_week": 7, "premium_30d": 30, "premium_60d": 60, "premium_90d": 90, "premium_year": 365, "premium_forever": 36500}
        
        if item_id in actions: field, amount = actions[item_id]; users[uid][field] = users[uid].get(field, 0) + amount
        elif item_id in time_actions: field, hours = time_actions[item_id]; users[uid][field] = (datetime.now() + timedelta(hours=hours)).isoformat()
        elif item_id in premium_actions:
            days = premium_actions[item_id]
            existing = users[uid].get("premium_until")
            base = datetime.fromisoformat(existing) if existing and datetime.now() < datetime.fromisoformat(existing) else datetime.now()
            users[uid]["premium_until"] = (base + timedelta(days=days)).isoformat()
        
        save_users(users)
        dt = f"\n🎫 Скидка {percent}%" if percent > 0 else ""
        if disc and disc.get("type") == "legendary": dt = "\n🌟 ЛЕГЕНДАРНАЯ!"
        cashback_text = f"\n🔄 Кэшбек: +{cashback} 💮" if cashback > 0 else ""
        await query.answer(f"✅ {item['name']}!")
        await query.edit_message_text(f"✅ ПОКУПКА!\n━━━━━━━━━━━━━━━━\n\n{item['icon']} {item['name']}\n{dt}{cashback_text}\n💰 Потрачено: {price} 💮\n💎 Остаток: {get_tokens(user_id):,} 💮\n⏱ {item.get('duration', 'Н/Д')}", reply_markup=back_button())
        return
    
    if data.startswith("buy_"):
        item_id = data.replace("buy_", ""); item = shop_items.get(item_id)
        if not item: return
        price, percent, disc = get_discounted_price(item_id, user_id)
        tokens = get_tokens(user_id); can = "✅ Хватает" if tokens >= price else "❌ Не хватает"
        
        discount_info = ""
        if premium:
            if item.get("category") == "premium" and item.get("location") == "private": discount_info = f"\n💎 Скидка на продление: {PREMIUM_RENEWAL_DISCOUNT}%"
            elif item.get("location") == "chat": discount_info = f"\n💎 Скидка на чат: {PREMIUM_CHAT_DISCOUNT}%"
        cashback_info = ""
        if premium and item.get("location") == "chat":
            cashback_info = f"\n🔄 Кэшбек: +{int(price * CASHBACK_PERCENT / 100)} 💮"
        
        benefits_text = "\n".join([f"  ✓ {b}" for b in item.get("benefits", [])])
        dt = f"\n\n💵 Цена: {price} 💮"
        if percent > 0 and disc:
            if disc.get("type") == "legendary": dt = "\n\n🌟 ЛЕГЕНДАРНАЯ СКИДКА! 0 💮"
            else: dt = f"\n\n{disc.get('color', '🟢')} СКИДКА {percent}%\n💵 Обычная: {item['price']} 💮\n🔥 Со скидкой: {price} 💮"
        
        premium_comparison = ""
        if item_id.startswith("premium_"):
            premium_comparison = (
                f"\n\n📊 FREE vs PREMIUM:\n"
                f"┌──────────────────────────┬────────────┬────────────┐\n"
                f"│                          │    FREE    │  PREMIUM   │\n"
                f"├──────────────────────────┼────────────┼────────────┤\n"
                f"│ Текст (ЛС)               │  {DAILY_LIMIT}/день     │ Безлимит   │\n"
                f"│ Фото (ЛС)                │  {IMAGE_DAILY_LIMIT}/день     │ Безлимит   │\n"
                f"│ Пресеты                  │     ❌     │  10 ролей  │\n"
                f"│ Кэшбек (чат)             │     0%     │    {CASHBACK_PERCENT}%     │\n"
                f"│ Скидка на продление      │     -      │    {PREMIUM_RENEWAL_DISCOUNT}%     │\n"
                f"│ Скидка на чат            │     -      │    {PREMIUM_CHAT_DISCOUNT}%     │\n"
                f"│ Пассивный доход          │     ❌     │ {PASSIVE_INCOME_HOURLY} 💮/час     │\n"
                f"│ Рефералы                 │ {REFERRAL_BONUS}/{INVITED_BONUS} 💮      │ {PREMIUM_REFERRAL_BONUS}/{PREMIUM_INVITED_BONUS} 💮      │\n"
                f"│ Переводы                 │ до {MAX_TRANSFER:,} │ до {PREMIUM_MAX_TRANSFER:,} │\n"
                f"│ Уведомления              │ каждые 24ч │ 1-24ч     │\n"
                f"│ Настройка уведомлений    │     ❌     │     ✅     │\n"
                f"│ Значок 💎                │     ❌     │     ✅     │\n"
                f"└──────────────────────────┴────────────┴────────────┘"
            )
        
        text = (
            f"🛒 {item['icon']} {item['name']}\n━━━━━━━━━━━━━━━━\n\n"
            f"📝 {item['desc']}\n\n"
            f"✨ ПРЕИМУЩЕСТВА:\n{benefits_text}\n"
            f"{dt}{discount_info}{cashback_info}{premium_comparison}\n\n"
            f"⏱ Длительность: {item.get('duration', 'Н/Д')}\n"
            f"⚠️ {item.get('warning', '')}\n\n"
            f"💎 Баланс: {tokens:,} 💮\n{can}"
        )
        await query.edit_message_text(text, reply_markup=confirm_keyboard(item_id))
        return
    
    if data == "donate_info": await query.edit_message_text(DONATE_INFO_TEXT, reply_markup=back_button()); return
    if data == "models": await query.edit_message_text("🧠 МОДЕЛИ\n━━━━━━━━━━━━━━━━\n\n💬 NeBlock AI V2 — текст\n🎨 NeBlock Images V2 — фото\n📝 /genimage", reply_markup=back_button()); return
    if data == "tokenrate":
        rd = get_token_rate()
        await query.edit_message_text(f"💮 КУРС NBT\n\n💰 1 NBT = ${rd.get('rate', 0.005):.8f}\n💎 Кап: ${rd.get('market_cap', 0):,.2f}", reply_markup=back_button()); return
    if data == "transfer": context.user_data["waiting_transfer"] = True; await query.edit_message_text(f"{TRANSFER_INFO}\n\nОтправьте: ID КОЛИЧЕСТВО", reply_markup=back_button()); return
    if data == "commands": await query.edit_message_text(COMMANDS_LIST, reply_markup=back_button()); return
    if data == "changelog": await query.edit_message_text(CHANGELOG, reply_markup=back_button()); return
    if data == "promo": context.user_data["waiting_promo"] = True; await query.edit_message_text("🎟 Отправьте промокод.", reply_markup=back_button()); return
    if data == "faq": await query.edit_message_text(FAQ_TEXT[:4000], reply_markup=back_button()); return

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤔 Неизвестная команда.\n/start | /commands")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip() if update.message.text else ""
    user_id = update.effective_user.id; chat_type = update.effective_chat.type; chat_id = update.effective_chat.id
    bot_username = context.bot.username
    
    username = update.effective_user.username
    if username: users = load_users(); users[str(user_id)]["username"] = username; save_users(users)
    
    if is_user_muted(user_id): await update.message.reply_text("🚫 Заблокированы."); return
    is_clean, _, reason = moderate_content(text)
    if not is_clean: _, warn = warn_user(user_id); await update.message.reply_text(f"⚠️ {reason}\n{warn}"); return
    
    if context.user_data.get("waiting_transfer"):
        context.user_data["waiting_transfer"] = False
        parts = text.split()
        if len(parts) >= 2:
            try: to_id = int(parts[0]); amount = int(parts[1]); context.args = [str(to_id), str(amount)]; await transfer_cmd(update, context); return
            except: await update.message.reply_text("❌ ID КОЛИЧЕСТВО"); return
    
    if chat_type == "private":
        if await reply_button_handler(update, context): return
    
    is_image_request = False; should_respond = False
    
    if chat_type in ["group", "supergroup"]:
        mention = f"@{bot_username}"; text_lower = text.lower().strip()
        if mention in text:
            clean_text = text.replace(mention, "").strip(); should_respond = True
            if clean_text.lower().startswith("нарисуй"): text = clean_text[7:].strip(); is_image_request = True
            else: text = clean_text
        if not should_respond:
            for kw, is_img in {"нарисуй ": True, "сгенерируй ": True, "создай ": True, "бот ": False}.items():
                if text_lower.startswith(kw): text = text[len(kw):].strip(); should_respond = True
                if is_img: is_image_request = True
                break
        if not should_respond: return
    
    user = get_user(user_id)
    if context.user_data.get("waiting_promo"): 
        context.user_data["waiting_promo"] = False
        success, result = use_promo(user_id, text)
        await update.message.reply_text(f"🎟 +{result} 💮!" if success else f"❌ {result}"); return
    
    active_preset_id = user.get("active_preset")
    if active_preset_id and is_premium(user_id) and chat_type == "private" and not is_image_request:
        preset = PREMIUM_PRESETS.get(active_preset_id)
        if preset: text = f"[Инструкция: {preset['system_prompt']}]\n\nЗапрос: {text}"
    
    if is_image_request or (chat_type == "private" and user.get("current_model") == "image"):
        if chat_type == "private": users = load_users(); users[str(user_id)]["waiting_for_image"] = False; save_users(users)
        if not can_image_request(user_id, chat_type, chat_id): await update.message.reply_text("🚫 Лимит!"); return
        msg = await update.message.reply_text("🎨 Генерирую...")
        try:
            image_bytes, error = await generate_image(text)
            if image_bytes: add_image_request(user_id, chat_type); await msg.delete(); await update.message.reply_photo(photo=image_bytes, caption=f"🎨 NeBlock Images V2\n📝 {text[:200]}")
            else: await msg.edit_text("❌ Ошибка")
        except: await msg.edit_text("❌ Ошибка")
        return
    
    if not can_request(user_id, chat_type, chat_id): await update.message.reply_text("🚫 Лимит!"); return
    
    msg = await update.message.reply_text("💬 Генерирую...")
    try:
        response = client.responses.create(prompt={"id": PROMPT_ID}, input=text); answer = response.output_text
        add_request(user_id, chat_type); await msg.delete()
        if answer:
            rem = remaining(user_id, chat_type, chat_id)
            footer = f"\n\n━━━━━━━━━━━━━━━━\n💬 NeBlock AI V2 | Осталось: {rem}{AI_DISCLAIMER}"
            for i in range(0, len(answer), 4000): await update.message.reply_text(answer[i:i+4000] + (footer if i == 0 else ""))
        else: await update.message.reply_text(f"🤷 Пусто{AI_DISCLAIMER}")
    except: await msg.edit_text(f"❌ Ошибка{AI_DISCLAIMER}")

def main():
    print(f"🧠 NeBlock AI V{BOT_VERSION}")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Основные
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", id_cmd))
    app.add_handler(CommandHandler("profile", profile_cmd))
    app.add_handler(CommandHandler("faq", lambda u, c: u.message.reply_text(FAQ_TEXT[:4000])))
    app.add_handler(CommandHandler("changelog", lambda u, c: u.message.reply_text(CHANGELOG)))
    app.add_handler(CommandHandler("commands", lambda u, c: u.message.reply_text(COMMANDS_LIST)))
    
    # Premium
    app.add_handler(CommandHandler("premium", premium_cmd))
    app.add_handler(CommandHandler("buy_premium", buy_premium_cmd))
    app.add_handler(CommandHandler("notify", notify_cmd))
    
    # Награды
    app.add_handler(CommandHandler("streak", streak_cmd))
    app.add_handler(CommandHandler("streak_info", lambda u, c: u.message.reply_text(STREAK_INFO[:4000])))
    
    # Финансы
    app.add_handler(CommandHandler("tokenrate", tokenrate_cmd))
    app.add_handler(CommandHandler("transfer", transfer_cmd))
    app.add_handler(CommandHandler("transferinfo", lambda u, c: u.message.reply_text(TRANSFER_INFO)))
    app.add_handler(CommandHandler("donate", donate_cmd))
    app.add_handler(CommandHandler("donatetop", donatetop_cmd))
    app.add_handler(CommandHandler("promo", lambda u, c: setattr(c, 'user_data', {**c.user_data, 'waiting_promo': True}) or u.message.reply_text("🎟 Отправьте промокод.")))
    
    # Генерация
    app.add_handler(CommandHandler("genimage", genimage_cmd))
    
    # Пресеты
    app.add_handler(CommandHandler("presets", presets_cmd))
    
    # Магазин
    app.add_handler(CommandHandler("shop", lambda u, c: u.message.reply_text("🛒 Магазин", reply_markup=shop_keyboard("private", u.effective_user.id))))
    app.add_handler(CommandHandler("shopdesc", lambda u, c: u.message.reply_text("📋 /shop — магазин товаров\n/shop — текстовые запросы, фото, Premium\n/chatshop — магазин для чата")))
    app.add_handler(CommandHandler("discounts", lambda u, c: inline_button_handler(u, c)))
    
    # Чаты
    app.add_handler(CommandHandler("chatowner", chatowner_cmd))
    app.add_handler(CommandHandler("chatshop", chatshop_cmd))
    
    # Админ
    app.add_handler(CommandHandler("give", admin_give))
    app.add_handler(CommandHandler("take", admin_take))
    app.add_handler(CommandHandler("resetuser", admin_resetuser))
    app.add_handler(CommandHandler("setpremium", admin_setpremium))
    app.add_handler(CommandHandler("userinfo", admin_userinfo))
    app.add_handler(CommandHandler("top", admin_top))
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CommandHandler("forcediscounts", admin_forcediscounts))
    app.add_handler(CommandHandler("forcerate", admin_force_rate))
    app.add_handler(CommandHandler("broadcast", admin_broadcast))
    app.add_handler(CommandHandler("createpromo", admin_create_promo))
    app.add_handler(CommandHandler("promos", admin_promos))
    app.add_handler(CommandHandler("deletepromo", admin_delete_promo))
    app.add_handler(CommandHandler("cleardiscounts", admin_cleardiscounts))
    
    app.add_handler(CallbackQueryHandler(inline_button_handler))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    print("✅ Бот запущен!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
