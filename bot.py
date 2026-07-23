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
# 🧠 NeBlock AI V6.0 - Конфигурация
# ═══════════════════════════════════════════

TELEGRAM_TOKEN = "8700124191:AAE6qSSouLjlDxPWwoFObJORMbDotsby9co"
YANDEX_API_KEY = "AQVNy7Dm-dvQRzejHvH0383oHTZhhW2fda95I558"
YANDEX_FOLDER = "b1guk4h3j9t48lsjl6sq"
PROMPT_ID = "fvt621uiq1fftiu5qomu"
IMAGE_MODEL = "art://b1guk4h3j9t48lsjl6sq/aliceai-image-art-3.0/latest"

# ═══════════════════════════════════════════
# 📊 БАЛАНСИРОВКА ЭКОНОМИКИ V6.0
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

# Пассивный доход
FREE_PASSIVE_INCOME_HOURLY = 2       # Бесплатный: 2 💮/час
PREMIUM_PASSIVE_INCOME_HOURLY = 20   # Premium: 20 💮/час (раз в 30 минут = 10 💮/30мин)
PASSIVE_INCOME_INTERVAL_MINUTES = 30  # Интервал начисления
PASSIVE_INCOME_MAX_INTERVALS = 24     # Максимум накоплений (12 часов)

PREMIUM_RENEWAL_DISCOUNT = 15
PREMIUM_CHAT_DISCOUNT = 10
BOT_VERSION = "6.0"

NOTIFY_INTERVAL_FREE = 24
DEFAULT_NOTIFY_INTERVAL_PREMIUM = 6
PREMIUM_NOTIFY_OPTIONS = [1, 3, 6, 12, 24]

# Увеличенные Premium лимиты
MIN_TRANSFER = 1
MAX_TRANSFER = 5000
DAILY_TRANSFER_LIMIT = 25000
MIN_DONATION = 1
MAX_DONATION = 50000

PREMIUM_MAX_TRANSFER = 50000          # Увеличено с 25000
PREMIUM_DAILY_TRANSFER_LIMIT = 250000 # Увеличено с 100000
PREMIUM_MAX_DONATION = 500000         # Увеличено с 250000

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
# 📝 СИСТЕМА ПРЕСЕТОВ (КОПИРУЮТСЯ В ЗАПРОС)
# ═══════════════════════════════════════════

PREMIUM_PRESETS = {
    "programmer": {"id": "programmer", "name": "💻 Программист", "icon": "💻", "system_prompt": "Ты — опытный senior-разработчик. Отвечай технически точно, с примерами кода на Python/JavaScript. Объясняй сложное простым языком.", "category": "professional", "description": "Код, архитектура, дебаггинг"},
    "copywriter": {"id": "copywriter", "name": "📝 Копирайтер", "icon": "📝", "system_prompt": "Ты — профессиональный копирайтер. Пиши убедительные тексты по формуле AIDA.", "category": "professional", "description": "Реклама, лендинги, SMM"},
    "business": {"id": "business", "name": "💼 Бизнес-консультант", "icon": "💼", "system_prompt": "Ты — бизнес-консультант. Анализируй рынок, предлагай стратегии с цифрами.", "category": "professional", "description": "Стратегия, стартапы, финансы"},
    "teacher": {"id": "teacher", "name": "📚 Учитель", "icon": "📚", "system_prompt": "Ты — опытный педагог. Объясняй от простого к сложному.", "category": "education", "description": "Обучение, объяснение"},
    "psychologist": {"id": "psychologist", "name": "🧠 Психолог", "icon": "🧠", "system_prompt": "Ты — психолог-консультант. Проявляй эмпатию, задавай открытые вопросы.", "category": "life", "description": "Отношения, стресс"},
    "chef": {"id": "chef", "name": "👨‍🍳 Шеф-повар", "icon": "👨‍🍳", "system_prompt": "Ты — шеф-повар. Давай рецепты с точными граммовками.", "category": "life", "description": "Рецепты, кулинария"},
    "fitness": {"id": "fitness", "name": "💪 Фитнес-тренер", "icon": "💪", "system_prompt": "Ты — фитнес-тренер. Составляй программы тренировок.", "category": "life", "description": "Тренировки, питание"},
    "creative": {"id": "creative", "name": "🎨 Креативный директор", "icon": "🎨", "system_prompt": "Ты — креативный директор. Генерируй нестандартные идеи.", "category": "professional", "description": "Креатив, брендинг"},
    "lawyer": {"id": "lawyer", "name": "⚖️ Юрист", "icon": "⚖️", "system_prompt": "Ты — практикующий юрист. Ссылайся на законы.", "category": "professional", "description": "Право, договоры"},
    "doctor": {"id": "doctor", "name": "🏥 Врач-терапевт", "icon": "🏥", "system_prompt": "Ты — врач-терапевт. Собирай анамнез.", "category": "life", "description": "Здоровье, симптомы"},
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
PREMIUM_TRANSFER_TAX_BRACKETS = [{"min": 0, "max": 999, "tax_percent": 0}, {"min": 1000, "max": 4999, "tax_percent": 2}, {"min": 5000, "max": 14999, "tax_percent": 5}, {"min": 15000, "max": 34999, "tax_percent": 8}, {"min": 35000, "max": 50000, "tax_percent": 10}]

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

Версия 6.0 🔥
• 💎 Premium пассивный доход: 20 💮/30мин
• 🆓 Бесплатный пассивный доход: 2 💮/час
• 🔔 Умные уведомления отправляются автоматически
• 📊 Обновлённая таблица сравнения Free vs Premium
• ⬆️ Увеличены Premium лимиты (переводы ×10, донаты ×10)
• 📝 Пресеты копируются в запрос (не активируются)

Версия 5.9.2
• Отображение Premium-скидки в карточках товаров
• Расширенная информация в карточках чат-товаров
"""

FAQ_TEXT = f"""
📚 ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ
━━━━━━━━━━━━━━━━━━━━

❓ Что такое NeBlock AI?
Платформа с собственными ИИ-моделями в Telegram.

❓ Что даёт Premium? 💎
• Безлимит текста и фото в ЛС
• 10 проф. пресетов (копируются в запрос)
• Кэшбек 15% на чат-покупки
• Пассивный доход 20 💮/30мин (Free: 2 💮/час)
• Рефералы ×3
• Лимиты ×10
• Уведомления каждые 1-24ч
• Значок 💎

❓ Как работают пресеты? 📝
Выберите роль через /presets. Инструкция роли будет СКОПИРОВАНА
в ваш запрос, а не активирована как отдельный режим.

❓ Как работает пассивный доход? 💤
• Free: 2 💮 каждый час
• Premium: 20 💮 каждые 30 минут
• Начисляется автоматически
• Максимум 12 часов накопления

❓ Лимиты?
Free: {DAILY_LIMIT} текст + {IMAGE_DAILY_LIMIT} фото/день
Premium: безлимит в ЛС
Переводы: до {MAX_TRANSFER:,} (Free) / {PREMIUM_MAX_TRANSFER:,} (Premium)
"""

DONATE_INFO_TEXT = f"""
🌍 БЛАГОТВОРИТЕЛЬНОСТЬ
━━━━━━━━━━━━━━━━━━━━
🔥 Сжигание NBT повышает курс.
📊 Free: до {MAX_DONATION:,} 💮 | Premium 💎: до {PREMIUM_MAX_DONATION:,} 💮
"""

TRANSFER_INFO = f"""
💸 ПЕРЕВОДЫ 💮 NBT
━━━━━━━━━━━━━━━━━━━━
/transfer ID КОЛИЧЕСТВО | @username | ответ
📊 FREE: {MAX_TRANSFER:,} 💮/раз | {DAILY_TRANSFER_LIMIT:,} 💮/день | налог 0-15%
💎 PREMIUM: {PREMIUM_MAX_TRANSFER:,} 💮/раз | {PREMIUM_DAILY_TRANSFER_LIMIT:,} 💮/день | налог 0-10%
"""

COMMANDS_LIST = """
📋 КОМАНДЫ NeBlock AI V6.0
━━━━━━━━━━━━━━━━━━━━

💬 ОСНОВНЫЕ:
/start | /faq | /commands | /changelog
🆔 /id | 👤 /profile

💎 PREMIUM:
/premium | /buy_premium | /notify
📝 /presets

🛒 МАГАЗИН:
/shop — магазин ЛС
/chatshop — магазин чата
/tokenrate | /discounts | /promo

🔥 НАГРАДЫ:
/streak | /streak_info

💸 ФИНАНСЫ:
/transfer | /transferinfo | /donate | /donatetop

🎨 ГЕНЕРАЦИЯ:
/genimage

👥 ЧАТЫ:
/chatowner | /shopdesc

🔧 АДМИН (33 команды)
"""

DISCOUNT_TYPES = {"regular": {"name": "Обычная", "min": 5, "max": 25, "color": "🟢", "chance": 40, "icon": "🏷️"}, "super": {"name": "Супер", "min": 30, "max": 50, "color": "🔴", "chance": 20, "icon": "🔥"}, "flash": {"name": "Флеш", "min": 40, "max": 70, "color": "⚡", "chance": 8, "icon": "⏰"}, "bundle": {"name": "Набор", "min": 15, "max": 35, "color": "📦", "chance": 12, "icon": "🎁"}, "premium_discount": {"name": "Premium", "min": 10, "max": 30, "color": "👑", "chance": 5, "icon": "💎"}, "legendary": {"name": "ЛЕГЕНДАРНАЯ", "min": 100, "max": 100, "color": "🌟", "chance": 0.5, "icon": "💫"}}

SHOP_ITEMS_BASE = {
    "extra5": {"name": "+5 запросов", "price": 5, "icon": "📝", "category": "text", "desc": "5 дополнительных текстовых запросов к NeBlock AI V2.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "private", "type": "consumable", "duration": "до 00:00 МСК", "benefits": ["+5 текстовых запросов"]},
    "extra10": {"name": "+10 запросов", "price": 8, "icon": "📝", "category": "text", "desc": "10 дополнительных текстовых запросов.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "private", "type": "consumable", "duration": "до 00:00 МСК", "benefits": ["+10 запросов"]},
    "extra50": {"name": "+50 запросов", "price": 35, "icon": "📝", "category": "text", "desc": "50 дополнительных текстовых запросов.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "private", "type": "consumable", "duration": "до 00:00 МСК", "benefits": ["+50 запросов", "Экономия 30%"]},
    "unlimited_1h": {"name": "Безлимит текста 1ч", "price": 15, "icon": "♾️", "category": "text", "desc": "Безлимит текста на 1 час.", "warning": "⚠️ 1 час.", "location": "private", "type": "unlimited", "duration": "1 час", "benefits": ["Безлимит текста"]},
    "unlimited_24h": {"name": "Безлимит текста 24ч", "price": 50, "icon": "♾️", "category": "text", "desc": "Безлимит текста на 24 часа.", "warning": "⚠️ 24 часа.", "location": "private", "type": "unlimited", "duration": "24 часа", "benefits": ["Безлимит текста"]},
    "unlimited_7d": {"name": "Безлимит текста 7д", "price": 250, "icon": "♾️", "category": "text", "desc": "Безлимит текста на 7 дней.", "warning": "⚠️ 7 дней.", "location": "private", "type": "unlimited", "duration": "7 дней", "benefits": ["Безлимит текста"]},
    "image1": {"name": "1 фото", "price": 8, "icon": "🎨", "category": "image", "desc": "1 генерация изображения. 1024×1024.", "warning": "⚠️ Сгорает в 00:00 МСК.", "location": "private", "type": "consumable", "duration": "до 00:00 МСК", "benefits": ["1 изображение"]},
    "image5": {"name": "5 фото", "price": 30, "icon": "🎨", "category": "image", "desc": "5 генераций изображений.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "private", "type": "consumable", "duration": "до 00:00 МСК", "benefits": ["5 изображений", "Экономия 25%"]},
    "image20": {"name": "20 фото", "price": 100, "icon": "🎨", "category": "image", "desc": "20 генераций изображений.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "private", "type": "consumable", "duration": "до 00:00 МСК", "benefits": ["20 изображений", "Экономия 37%"]},
    "image_unlimited_1h": {"name": "Безлимит фото 1ч", "price": 25, "icon": "♾️", "category": "image", "desc": "Безлимит фото на 1 час.", "warning": "⚠️ 1 час.", "location": "private", "type": "unlimited", "duration": "1 час", "benefits": ["Безлимит фото"]},
    "premium_day": {"name": "Premium 1 день", "price": 100, "icon": "⭐", "category": "premium", "desc": "Все Premium-привилегии на 24 часа.", "warning": "⚠️ 24 часа. Только ЛС.", "location": "private", "type": "premium", "duration": "1 день", "benefits": ["Безлимит текста и фото", "10 проф. пресетов", "Кэшбек 15% на чат", "Пассивный доход 20 💮/30мин", "Рефералы ×3", "Лимиты ×10", "Уведомления", "Значок 💎"]},
    "premium_week": {"name": "Premium 7 дней", "price": 500, "icon": "⭐", "category": "premium", "desc": "Неделя Premium.", "warning": "⚠️ 7 дней. Только ЛС.", "location": "private", "type": "premium", "duration": "7 дней", "benefits": ["Всё из Premium 1 день", "Экономия 28%"]},
    "premium_30d": {"name": "Premium 30 дней 🔥", "price": 1500, "icon": "💎", "category": "premium", "desc": "Месяц Premium.", "warning": "⚠️ 30 дней.", "location": "private", "type": "premium", "duration": "30 дней", "benefits": ["Всё из Premium 1 день", "Экономия 25%"]},
    "premium_60d": {"name": "Premium 60 дней 🚀", "price": 2500, "icon": "💎", "category": "premium", "desc": "2 месяца Premium.", "warning": "⚠️ 60 дней.", "location": "private", "type": "premium", "duration": "60 дней", "benefits": ["Всё из Premium 1 день", "Экономия 37%"]},
    "premium_90d": {"name": "Premium 90 дней 👑", "price": 3500, "icon": "💎", "category": "premium", "desc": "3 месяца Premium.", "warning": "⚠️ 90 дней.", "location": "private", "type": "premium", "duration": "90 дней", "benefits": ["Всё из Premium 1 день", "Экономия 50%"]},
    "premium_year": {"name": "Premium 1 год 💫", "price": 10000, "icon": "👑", "category": "premium", "desc": "Год Premium.", "warning": "⚠️ 365 дней.", "location": "private", "type": "premium", "duration": "1 год", "benefits": ["Всё из Premium 1 день", "Экономия 72%"]},
    "premium_forever": {"name": "Premium НАВСЕГДА ✨", "price": 25000, "icon": "🌟", "category": "premium", "desc": "Пожизненный Premium.", "warning": "⚠️ Только ЛС.", "location": "private", "type": "premium", "duration": "Навсегда", "benefits": ["Всё из Premium 1 день", "Пожизненно"]},
    "chat_extra10": {"name": "+10 запросов (чат)", "price": 8, "icon": "👥", "category": "chat", "desc": "10 дополнительных запросов в групповых чатах.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "chat", "type": "consumable", "duration": "до 00:00 МСК", "benefits": ["+10 запросов в чатах"]},
    "chat_extra50": {"name": "+50 запросов (чат)", "price": 30, "icon": "👥", "category": "chat", "desc": "50 дополнительных запросов в чатах.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "chat", "type": "consumable", "duration": "до 00:00 МСК", "benefits": ["+50 запросов в чатах", "Экономия 25%"]},
    "chat_unlimited_1h": {"name": "Безлимит чат 1ч", "price": 20, "icon": "♾️", "category": "chat", "desc": "Безлимитные запросы в чатах на 1 час.", "warning": "⚠️ 1 час.", "location": "chat", "type": "unlimited", "duration": "1 час", "benefits": ["Безлимит в чатах"]},
    "chat_unlimited_24h": {"name": "Безлимит чат 24ч", "price": 75, "icon": "♾️", "category": "chat", "desc": "Безлимитные запросы в чатах на 24 часа.", "warning": "⚠️ 24 часа.", "location": "chat", "type": "unlimited", "duration": "24 часа", "benefits": ["Безлимит в чатах на сутки"]},
    "chat_image5": {"name": "5 фото (чат)", "price": 25, "icon": "🎨", "category": "chat_image", "desc": "5 генераций изображений в чатах.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "chat", "type": "consumable", "duration": "до 00:00 МСК", "benefits": ["5 фото в чатах"]},
    "chat_image20": {"name": "20 фото (чат)", "price": 90, "icon": "🎨", "category": "chat_image", "desc": "20 генераций изображений в чатах.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "chat", "type": "consumable", "duration": "до 00:00 МСК", "benefits": ["20 фото в чатах", "Экономия 28%"]},
    "chat_premium_day": {"name": "Premium чат 1д", "price": 150, "icon": "⭐", "category": "chat_premium", "desc": "Полный безлимит в чате на 1 день.", "warning": "⚠️ 24 часа.", "location": "chat", "type": "premium", "duration": "1 день", "benefits": ["Безлимит в чате"]},
    "chat_premium_week": {"name": "Premium чат 7д", "price": 750, "icon": "⭐", "category": "chat_premium", "desc": "Неделя безлимита в чате.", "warning": "⚠️ 7 дней.", "location": "chat", "type": "premium", "duration": "7 дней", "benefits": ["Безлимит в чате на неделю"]},
    "chat_premium_30d": {"name": "Premium чат 30д", "price": 2500, "icon": "💎", "category": "chat_premium", "desc": "Месяц безлимита в чате.", "warning": "⚠️ 30 дней.", "location": "chat", "type": "premium", "duration": "30 дней", "benefits": ["Безлимит в чате на месяц"]},
    "chat_premium_60d": {"name": "Premium чат 60д", "price": 4000, "icon": "💎", "category": "chat_premium", "desc": "2 месяца безлимита в чате.", "warning": "⚠️ 60 дней.", "location": "chat", "type": "premium", "duration": "60 дней", "benefits": ["Безлимит в чате на 2 месяца"]},
    "chat_premium_90d": {"name": "Premium чат 90д", "price": 5500, "icon": "💎", "category": "chat_premium", "desc": "3 месяца безлимита в чате.", "warning": "⚠️ 90 дней.", "location": "chat", "type": "premium", "duration": "90 дней", "benefits": ["Безлимит в чате на 3 месяца"]},
    "chat_premium_year": {"name": "Premium чат 1 год", "price": 15000, "icon": "👑", "category": "chat_premium", "desc": "Год безлимита в чате.", "warning": "⚠️ 365 дней.", "location": "chat", "type": "premium", "duration": "1 год", "benefits": ["Безлимит в чате на год"]},
    "chat_premium_forever": {"name": "Premium чат НАВСЕГДА", "price": 35000, "icon": "🌟", "category": "chat_premium", "desc": "Пожизненный безлимит в чате.", "warning": "⚠️ Только для чатов.", "location": "chat", "type": "premium", "duration": "Навсегда", "benefits": ["Пожизненный безлимит"]},
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
    """Начисляет пассивный доход. Premium: 20 💮/30мин, Free: 2 💮/час"""
    users = load_users(); uid = str(user_id)
    if uid not in users: return 0
    
    premium = is_premium(user_id)
    hourly_rate = PREMIUM_PASSIVE_INCOME_HOURLY if premium else FREE_PASSIVE_INCOME_HOURLY
    interval_minutes = PASSIVE_INCOME_INTERVAL_MINUTES
    max_intervals = PASSIVE_INCOME_MAX_INTERVALS
    
    now = datetime.now()
    last_income = users[uid].get("last_passive_income")
    
    if last_income:
        last_time = datetime.fromisoformat(last_income)
        minutes_passed = (now - last_time).total_seconds() / 60
        intervals_passed = min(int(minutes_passed / interval_minutes), max_intervals)
        income = int(intervals_passed * (hourly_rate * interval_minutes / 60))
    else:
        income = int(hourly_rate * interval_minutes / 60)
    
    if income > 0:
        users[uid]["tokens"] = users[uid].get("tokens", 0) + income
        users[uid]["earned_tokens"] = users[uid].get("earned_tokens", 0) + income
        users[uid]["last_passive_income"] = now.isoformat()
        save_users(users)
    
    return income

# ═══════════════════════════════════════════
# 🔔 АВТОМАТИЧЕСКИЕ УМНЫЕ УВЕДОМЛЕНИЯ
# ═══════════════════════════════════════════

async def auto_notification_task(context: ContextTypes.DEFAULT_TYPE):
    """Фоновая задача: рассылает умные уведомления всем пользователям"""
    users = load_users()
    now = datetime.now()
    sent_count = 0
    
    for uid in users:
        try:
            user_id = int(uid)
            user = get_user(user_id)
            premium = is_premium(user_id)
            interval = user.get("notify_interval", DEFAULT_NOTIFY_INTERVAL_PREMIUM) if premium else NOTIFY_INTERVAL_FREE
            
            last_notify = user.get("last_notification")
            if last_notify:
                last_time = datetime.fromisoformat(last_notify)
                hours_passed = (now - last_time).total_seconds() / 3600
                if hours_passed < interval:
                    continue
            
            # Начисляем пассивный доход
            passive = process_passive_income(user_id)
            
            # Отправляем уведомление
            rate_data = get_token_rate()
            rate = rate_data.get("rate", 0.005)
            tokens = user.get("tokens", 0)
            usd = tokens * rate
            streak = user.get("daily_bonus_streak", 0)
            donated_total, _, _ = get_donation_stats()
            
            premium_icon = "💎" if premium else ""
            
            text = (
                f"🔔 СВОДКА {premium_icon}\n━━━━━━━━━━━━━━━━\n\n"
                f"💰 Баланс: {tokens:,} 💮 (~${usd:.2f})\n"
                f"💮 Курс: 1 NBT = ${rate:.8f}\n"
                f"🔥 Серия: {streak} дн.\n"
                f"💤 Пассивный доход: +{passive} 💮\n"
                f"🌍 Сожжено: {donated_total:,} 💮\n"
            )
            
            if premium:
                text += f"💎 Premium активно\n🔔 Интервал: {interval} ч.\n"
            else:
                text += f"\n💡 Premium: 20 💮/30мин, пресеты, безлимит\n💎 /premium\n"
            
            text += f"\n🕐 Следующая: через {interval} ч."
            
            await context.bot.send_message(user_id, text)
            
            # Обновляем время уведомления
            users[uid]["last_notification"] = now.isoformat()
            sent_count += 1
            
        except:
            pass
    
    if sent_count > 0:
        save_users(users)
        logger.info(f"🔔 Отправлено {sent_count} умных уведомлений")

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

def private_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("ℹ️ О боте", callback_data="about"), InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🧠 Модели", callback_data="models"), InlineKeyboardButton("💎 Premium", callback_data="premium_menu")],
        [InlineKeyboardButton("🔥 Награды", callback_data="earn"), InlineKeyboardButton("💮 Курс NBT", callback_data="tokenrate")],
        [InlineKeyboardButton("💸 Перевод", callback_data="transfer"), InlineKeyboardButton("🌍 Донат", callback_data="donate_info")],
        [InlineKeyboardButton("📝 Пресеты", callback_data="presets_menu"), InlineKeyboardButton("🎫 Скидки", callback_data="show_discounts")],
        [InlineKeyboardButton("🛒 Магазин ЛС", callback_data="shop"), InlineKeyboardButton("👥 Магазин чата", callback_data="chat_shop_info")],
    ])

def chat_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("ℹ️ О боте", callback_data="about"), InlineKeyboardButton("💎 Premium", callback_data="premium_menu")],
        [InlineKeyboardButton("💮 Курс NBT", callback_data="tokenrate"), InlineKeyboardButton("👥 Магазин чата", callback_data="chat_shop_info")],
        [InlineKeyboardButton("💸 Перевод", callback_data="transfer"), InlineKeyboardButton("👤 Профиль", callback_data="profile_chat")],
        [InlineKeyboardButton("🎫 Скидки", callback_data="show_discounts")],
    ])

def back_button(): return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="menu")]])

def shop_keyboard(location="private", user_id=None):
    keyboard = []
    discounts = get_discounts(); shop_items = get_shop_items(user_id)
    active = {k: v for k, v in discounts.items() if k not in ["last_update", "generated_at"]}
    if active:
        legendary = any(d.get("type") == "legendary" for d in active.values())
        keyboard.append([InlineKeyboardButton("🌟 ЛЕГЕНДАРНАЯ СКИДКА! 🌟" if legendary else "🎫 Скидки", callback_data="show_discounts")])
    
    if location == "private":
        cats = [("📝 Текстовые запросы", "text"), ("🎨 Генерация фото", "image"), ("⭐ Premium подписка", "premium")]
    else:
        cats = [("👥 Запросы в чатах", "chat"), ("🖼️ Фото в чатах", "chat_image"), ("⭐ Premium для чата", "chat_premium")]
    
    for label, cat in cats:
        items_in_cat = False
        for item_id, item in shop_items.items():
            if item.get("category") == cat and item.get("location") == location:
                if not items_in_cat:
                    keyboard.append([InlineKeyboardButton(f"── {label} ──", callback_data="none")])
                    items_in_cat = True
                price, percent, disc = get_discounted_price(item_id, user_id)
                
                premium_mark = ""
                if user_id and is_premium(user_id):
                    if item.get("location") == "chat":
                        premium_mark = " 💎"
                    elif item.get("category") == "premium" and item.get("location") == "private":
                        premium_mark = " 💎"
                
                if percent > 0 and disc:
                    if disc.get("type") == "legendary": price_text = "🌟 БЕСПЛАТНО!"
                    else: price_text = f"{disc.get('color', '🟢')} {price} 💮 -{percent}%"
                else: price_text = f"{price} 💮"
                keyboard.append([InlineKeyboardButton(f"{item['icon']} {item['name']}{premium_mark} — {price_text}", callback_data=f"buy_{item_id}")])
    
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
    keyboard = []
    for interval in PREMIUM_NOTIFY_OPTIONS:
        keyboard.append([InlineKeyboardButton(f"Каждые {interval} ч.", callback_data=f"notify_{interval}")])
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
        await update.message.reply_text(
            f"🧠 NeBlock AI V{BOT_VERSION} в чате!\n━━━━━━━━━━━━━━━━\n\n"
            f"💬 @{context.bot.username} вопрос — задать вопрос боту\n"
            f"🎨 /genimage — генерация изображений\n"
            f"💸 /transfer — перевод токенов\n"
            f"💎 /premium — Premium подписка\n"
            f"👤 /profile — профиль участника\n"
            f"🆔 /id — узнать свой ID\n\n"
            f"📊 Лимиты чата: {CHAT_DAILY_LIMIT} текст + {CHAT_IMAGE_LIMIT} фото/день\n"
            f"🛒 /chatshop — магазин для чата",
            reply_markup=chat_menu()
        )
        return
    premium = "💎 Активен" if is_premium(user_id) else "Не активен"
    rate_data = get_token_rate(); rate = rate_data.get("rate", 0.005)
    passive_text = f"\n💤 Пассивный доход: +{passive_income} 💮" if passive_income > 0 else ""
    await update.message.reply_text(
        f"🧠 NeBlock AI V{BOT_VERSION}\n━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💎 Premium: {premium}\n"
        f"💰 Баланс: {user.get('tokens', 0):,} 💮 (~${user.get('tokens', 0) * rate:.2f})\n"
        f"💮 Курс: 1 NBT = ${rate:.8f}\n"
        f"🔥 Серия: {user.get('daily_bonus_streak', 0)} дн.\n"
        f"📊 Лимиты ЛС: {DAILY_LIMIT} текст + {IMAGE_DAILY_LIMIT} фото/день\n"
        f"📊 Лимиты чатов: {CHAT_DAILY_LIMIT} текст + {CHAT_IMAGE_LIMIT} фото/день{passive_text}\n\n"
        f"👇 Выберите раздел:",
        reply_markup=private_menu()
    )

async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if context.args:
        try: user_id = int(context.args[0])
        except: pass
    await update.message.reply_text(f"🆔 ID: `{user_id}`\n\n💡 Используйте /profile {user_id} для просмотра профиля.", parse_mode="Markdown")

async def notify_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_premium(user_id): await update.message.reply_text("❌ Только для Premium 💎\n\nFree: уведомления раз в 24 часа\nPremium: настраиваемый интервал (1/3/6/12/24 ч.)"); return
    if context.args:
        try:
            interval = int(context.args[0])
            if interval in PREMIUM_NOTIFY_OPTIONS:
                users = load_users(); uid = str(user_id); users[uid]["notify_interval"] = interval; save_users(users)
                await update.message.reply_text(f"✅ Интервал: каждые {interval} ч.\n\nУведомления приходят автоматически!"); return
        except: pass
    user = get_user(user_id); current = user.get("notify_interval", DEFAULT_NOTIFY_INTERVAL_PREMIUM)
    await update.message.reply_text(f"🔔 НАСТРОЙКА УВЕДОМЛЕНИЙ\n━━━━━━━━━━━━━━━━\n\nТекущий интервал: каждые {current} ч.\nДоступные: {', '.join(map(str, PREMIUM_NOTIFY_OPTIONS))} ч.\n\nУведомления приходят автоматически!\nВыберите новый интервал:", reply_markup=notify_keyboard())

async def premium_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id; premium = is_premium(user_id); shop_items = get_shop_items(user_id)
    if premium:
        user = get_user(user_id); prem_until = user.get("premium_until")
        remaining_text = ""
        if prem_until:
            remaining = datetime.fromisoformat(prem_until) - datetime.now()
            if remaining.total_seconds() > 0: remaining_text = f"⏳ Осталось: {remaining.days} дн. {remaining.seconds // 3600} ч.\n"
        text = (
            f"💎 PREMIUM АКТИВЕН\n━━━━━━━━━━━━━━━━\n\n{remaining_text}"
            f"📊 ВАШИ ПРИВИЛЕГИИ:\n"
            f"• Безлимит текста и фото в ЛС\n"
            f"• 10 профессиональных пресетов\n"
            f"• Кэшбек {CASHBACK_PERCENT}% на чат-покупки\n"
            f"• Скидка {PREMIUM_RENEWAL_DISCOUNT}% на продление\n"
            f"• Скидка {PREMIUM_CHAT_DISCOUNT}% на чат-товары\n"
            f"• Пассивный доход {PREMIUM_PASSIVE_INCOME_HOURLY} 💮/час (каждые 30 мин)\n"
            f"• Рефералы ×3 ({PREMIUM_REFERRAL_BONUS}/{PREMIUM_INVITED_BONUS} 💮)\n"
            f"• Лимит перевода {PREMIUM_MAX_TRANSFER:,} 💮 (налог 0-10%)\n"
            f"• Умные уведомления с настройкой интервала\n"
            f"• Значок 💎 в профиле и топах\n\n"
            f"🛒 /buy_premium — продлить | 📝 /presets | 🔔 /notify"
        )
    else:
        text = (
            f"💎 NeBlock Premium\n━━━━━━━━━━━━━━━━\n\n"
            f"📊 СРАВНЕНИЕ FREE vs PREMIUM:\n\n"
            f"┌────────────────────────────┬──────────────┬──────────────┐\n"
            f"│ Возможность                │     FREE     │   PREMIUM    │\n"
            f"├────────────────────────────┼──────────────┼──────────────┤\n"
            f"│ Текстовые запросы (ЛС)     │   {DAILY_LIMIT}/день      │  Безлимит    │\n"
            f"│ Генерация фото (ЛС)        │   {IMAGE_DAILY_LIMIT}/день      │  Безлимит    │\n"
            f"│ Профессиональные пресеты   │      ❌      │   10 ролей   │\n"
            f"│ Пассивный доход            │  2 💮/час    │ 20 💮/30мин  │\n"
            f"│ Кэшбек с чат-покупок       │      0%      │     {CASHBACK_PERCENT}%      │\n"
            f"│ Скидка на продление        │      -       │     {PREMIUM_RENEWAL_DISCOUNT}%      │\n"
            f"│ Скидка на чат-товары       │      -       │     {PREMIUM_CHAT_DISCOUNT}%      │\n"
            f"│ Реферальный бонус          │  {REFERRAL_BONUS}/{INVITED_BONUS} 💮      │  {PREMIUM_REFERRAL_BONUS}/{PREMIUM_INVITED_BONUS} 💮       │\n"
            f"│ Максимальный перевод       │  {MAX_TRANSFER:,} 💮   │ {PREMIUM_MAX_TRANSFER:,} 💮  │\n"
            f"│ Налог на перевод           │    0-15%     │    0-10%     │\n"
            f"│ Максимальный донат         │  {MAX_DONATION:,} 💮  │ {PREMIUM_MAX_DONATION:,} 💮 │\n"
            f"│ Умные уведомления          │  каждые 24ч  │   1-24ч      │\n"
            f"│ Настройка уведомлений      │      ❌      │      ✅      │\n"
            f"│ Значок 💎                  │      ❌      │      ✅      │\n"
            f"└────────────────────────────┴──────────────┴──────────────┘\n\n"
            f"🛒 ТАРИФЫ (цены с учётом скидок):\n"
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
    keyboard = [[InlineKeyboardButton("🛒 Купить/Продлить Premium", callback_data="premium_shop")]]
    if premium: keyboard.append([InlineKeyboardButton("📝 Пресеты", callback_data="presets_menu"), InlineKeyboardButton("🔔 Уведомления", callback_data="notify_menu")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="menu")])
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def buy_premium_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🛒 ПОКУПКА PREMIUM\n━━━━━━━━━━━━━━━━\n💰 Баланс: {get_tokens(update.effective_user.id):,} 💮\n\nВыберите тариф:", reply_markup=shop_keyboard("private", update.effective_user.id))

async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_id = update.effective_user.id
    if context.args:
        try: target_id = int(context.args[0])
        except: pass
    u = get_user(target_id)
    if not u.get("joined"): await update.message.reply_text("❌ Пользователь не найден.\n\nВозможно, он ещё не запускал бота."); return
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
        f"💮 Курс: 1 NBT = ${rate_data.get('rate', 0.005):.8f}\n"
        f"🔥 Серия бонусов: {u.get('daily_bonus_streak', 0)} дн.\n"
        f"💎 Заработано всего: {u.get('earned_tokens', 0):,} 💮\n"
        f"💸 Потрачено всего: {u.get('spent_tokens', 0):,} 💮\n"
        f"🌍 Пожертвовано: {u.get('donated_tokens', 0):,} 💮\n"
        f"👥 Рефералов: {u.get('referrals', 0)}\n"
        f"📈 Всего запросов: {u.get('total_requests', 0):,}\n"
        f"🎨 Всего генераций: {u.get('total_images', 0):,}\n"
        f"🛡 Предупреждения: {u.get('warnings', 0)}/5\n"
        f"🆔 ID: `{target_id}`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def streak_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    streak = get_user(update.effective_user.id).get("daily_bonus_streak", 0)
    rate = get_token_rate().get("rate", 0.005)
    text = f"🔥 ВАША СЕРИЯ: {streak} дн.\n━━━━━━━━━━━━━━━━\n\n"
    if streak == 0: text += "🌱 Вы ещё не начали серию!\nНачните сегодня — заберите первый бонус!\n\n"
    elif streak >= MAX_STREAK_DAY: text += f"👑 Максимальная серия ({MAX_STREAK_DAY} дней)!\n⚠️ Забирайте бонус каждый день до 00:00 МСК!\n\n"
    else:
        nr = STREAK_BASE_REWARDS.get(streak + 1, STREAK_BASE_REWARDS[MAX_STREAK_DAY])
        rm = max(0.5, min(1.5, 1.0 + (rate * 10 - 0.1)))
        text += f"➡️ Завтра: {nr['icon']} {nr['name']}\n   ~{max(1, int(nr['base_min']*rm))}-{max(1, int(nr['base_max']*rm))} 💮\n\n"
    text += f"📐 Формула: базовая награда × множитель курса\n💮 Текущий курс: ${rate:.8f}\n⚠️ Не забрали до 00:00 МСК — серия СГОРИТ!\n📋 /streak_info — все 30 дней"
    await update.message.reply_text(text)

async def tokenrate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rd = get_token_rate(); history = load_json(TOKEN_HISTORY_FILE)
    text = (
        f"💮 КУРС NBT ТОКЕНА\n━━━━━━━━━━━━━━━━\n\n"
        f"💰 1 NBT = ${rd.get('rate', 0.005):.8f}\n"
        f"💎 Капитализация: ${rd.get('market_cap', 0):,.2f}\n"
        f"{rd.get('trend', '📊')} Изменение 24ч: {rd.get('change_24h', 0):+.2f}%\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🪙 В обороте: {rd.get('total_supply', 0):,} NBT\n"
        f"🔥 Сожжено всего: {rd.get('total_burned', 0):,} 💮\n"
        f"🌍 Пожертвовано: {rd.get('total_donated', 0):,} 💮\n"
        f"📅 День недели: {rd.get('day_icon', '📊')} {rd.get('day_name', '')}\n"
        f"🕐 Обновление: {rd.get('next_update', '')}\n\n"
        f"📊 ФАКТОРЫ КУРСА:\n"
        f"• Предложение: ×{rd.get('supply_factor', 1):.2f}\n"
        f"• Активность: ×{rd.get('activity_factor', 1):.2f}\n"
        f"• Сжигание: ×{rd.get('burn_factor', 1):.2f}\n"
        f"• День недели: ×{rd.get('day_factor', 1):.2f}\n"
        f"• Волатильность: ×{rd.get('volatility_index', 1):.2f}\n\n"
        f"💡 Курс влияет на размер ежедневных наград!\n"
        f"💡 Донаты повышают курс через сжигание!\n\n"
        f"📈 ИСТОРИЯ ЗА 7 ДНЕЙ:\n"
    )
    for date, h in sorted(history.items())[-7:]: text += f"• {date}: ${h.get('rate', 0):.8f}\n"
    await update.message.reply_text(text)

async def donate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id; max_don = PREMIUM_MAX_DONATION if is_premium(user_id) else MAX_DONATION
    if not context.args: await update.message.reply_text(f"{DONATE_INFO_TEXT}\n\nИспользование: /donate СУММА\nВаш лимит: до {max_don:,} 💮"); return
    try: amount = int(context.args[0])
    except: await update.message.reply_text("❌ /donate СУММА (целое число)"); return
    if amount < MIN_DONATION or amount > max_don: await update.message.reply_text(f"❌ Лимит: {MIN_DONATION} – {max_don:,} 💮"); return
    if get_user(user_id).get("tokens", 0) < amount: await update.message.reply_text(f"❌ Недостаточно токенов!\n💰 Ваш баланс: {get_tokens(user_id):,} 💮"); return
    await update.message.reply_text(
        f"🌍 ПОДТВЕРЖДЕНИЕ ДОНАТА\n━━━━━━━━━━━━━━━━\n\n"
        f"💰 Сумма: {amount:,} 💮\n"
        f"🔥 Токены сгорят НАВСЕГДА\n"
        f"📈 Это уменьшит предложение и может повысить курс!\n"
        f"💎 Ваш баланс: {get_tokens(user_id):,} → {get_tokens(user_id) - amount:,} 💮\n\n"
        f"Подтвердите сжигание:",
        reply_markup=donate_confirm_keyboard(amount)
    )

async def donatetop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total, count, top_donors = get_donation_stats()
    if not top_donors: await update.message.reply_text("🌍 ТОП БЛАГОТВОРИТЕЛЕЙ\n━━━━━━━━━━━━━━━━\n\nПока никто не делал донатов.\nБудьте первым! /donate СУММА"); return
    text = f"🌍 ТОП БЛАГОТВОРИТЕЛЕЙ\n━━━━━━━━━━━━━━━━\n\n🔥 Всего сожжено: {total:,} 💮\n📊 Количество донатов: {count}\n\n🏆 ТОП-10:\n"
    users = load_users(); medals = ["🥇", "🥈", "🥉"]
    for i, (uid, donated) in enumerate(top_donors):
        name = f"@{users.get(uid, {}).get('username', '?')}" if uid in users else f"ID:{uid}"
        mark = " 💎" if is_premium(int(uid)) else ""
        medal = medals[i] if i < 3 else f"{i+1}."
        text += f"{medal} {name}{mark}: {donated:,} 💮\n"
    text += "\n💡 /donate СУММА — сделать вклад в развитие"
    await update.message.reply_text(text)

async def genimage_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id; chat_type = update.effective_chat.type
    if not context.args: await update.message.reply_text("🎨 NeBlock Images V2\n━━━━━━━━━━━━━━━━\n\nИспользование: /genimage ОПИСАНИЕ\nПример: /genimage красивый закат на море\n\n💡 Генерирует изображение 1024×1024"); return
    text = " ".join(context.args)
    if not can_image_request(user_id, chat_type): await update.message.reply_text("🚫 Лимит генераций исчерпан!\n\n💡 Купите дополнительные генерации в /shop\n💎 Или активируйте Premium для безлимита"); return
    msg = await update.message.reply_text("🎨 Генерирую изображение...")
    try:
        image_bytes, error = await generate_image(text)
        if image_bytes: add_image_request(user_id, chat_type); await msg.delete(); await update.message.reply_photo(photo=image_bytes, caption=f"🎨 NeBlock Images V2\n📝 {text[:200]}")
        else: await msg.edit_text("❌ Ошибка генерации. Попробуйте другой запрос.")
    except: await msg.edit_text("❌ Ошибка генерации. Попробуйте позже.")

async def transfer_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id; premium = is_premium(user_id)
    max_t = PREMIUM_MAX_TRANSFER if premium else MAX_TRANSFER
    daily_limit = PREMIUM_DAILY_TRANSFER_LIMIT if premium else DAILY_TRANSFER_LIMIT
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(f"{TRANSFER_INFO}\n\nИспользование: /transfer ID КОЛИЧЕСТВО\nПример: /transfer 1671403667 100"); return
    try: to_id = int(context.args[0]); amount = int(context.args[1])
    except: await update.message.reply_text("❌ Неверный формат. /transfer ID КОЛИЧЕСТВО"); return
    if amount < MIN_TRANSFER or amount > max_t: await update.message.reply_text(f"❌ Лимит: {MIN_TRANSFER} – {max_t:,} 💮 за раз"); return
    sender = get_user(user_id)
    if sender.get("daily_transfer_total", 0) + amount > daily_limit: await update.message.reply_text(f"❌ Дневной лимит: {daily_limit:,} 💮"); return
    if sender.get("tokens", 0) < amount: await update.message.reply_text(f"❌ Недостаточно токенов!\n💰 Баланс: {sender.get('tokens', 0):,} 💮"); return
    tax, tax_percent, _ = get_transfer_tax(amount, premium)
    receiver = get_user(to_id)
    if not receiver: await update.message.reply_text("❌ Получатель не найден в боте."); return
    final_amount = amount - tax
    tax_info = f"Налог: {tax} 💮 ({tax_percent}%)" if tax > 0 else "Без налога"
    await update.message.reply_text(
        f"⚠️ ПРОВЕРЬТЕ ДАННЫЕ\n━━━━━━━━━━━━━━━━\n\n"
        f"👤 Получатель: ID {to_id}\n"
        f"💸 Сумма: {amount:,} 💮\n"
        f"📊 {tax_info}\n"
        f"💰 Зачислено: {final_amount:,} 💮\n\n"
        f"Подтвердите перевод:",
        reply_markup=transfer_confirm_keyboard(to_id, amount)
    )

async def presets_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_premium(update.effective_user.id):
        await update.message.reply_text(
            "❌ ПРЕСЕТЫ — ТОЛЬКО PREMIUM 💎\n━━━━━━━━━━━━━━━━\n\n"
            "10 профессиональных ролей для ИИ доступны только Premium пользователям.\n\n"
            "📝 КАК РАБОТАЮТ ПРЕСЕТЫ:\n"
            "• Выберите роль через /presets\n"
            "• Инструкция роли будет СКОПИРОВАНА в ваш запрос\n"
            "• Пресет не активируется как режим, а добавляется к тексту\n"
            "• Работает только в личных сообщениях\n\n"
            "📝 ДОСТУПНЫЕ РОЛИ:\n"
            "• 💻 Программист — код, архитектура, дебаггинг\n"
            "• 📝 Копирайтер — реклама, лендинги, SMM\n"
            "• 💼 Бизнес-консультант — стратегия, стартапы\n"
            "• 📚 Учитель — обучение, объяснение\n"
            "• 🧠 Психолог — отношения, стресс\n"
            "• 👨‍🍳 Шеф-повар — рецепты, кулинария\n"
            "• 💪 Фитнес-тренер — тренировки, питание\n"
            "• 🎨 Креативный директор — идеи, брендинг\n"
            "• ⚖️ Юрист — право, договоры\n"
            "• 🏥 Врач-терапевт — здоровье, симптомы\n\n"
            "💎 /premium — купить Premium\n"
            "🛒 /buy_premium — быстрая покупка"
        ); return
    user = get_user(update.effective_user.id); active = user.get("active_preset")
    text = "📝 ПРЕСЕТЫ (Premium 💎)\n━━━━━━━━━━━━━━━━\n\n"
    text += "📋 ВАЖНО: Пресеты КОПИРУЮТСЯ в запрос, а не активируются как режим.\n"
    text += "Инструкция роли будет добавлена перед вашим сообщением.\n\n"
    if active:
        p = PREMIUM_PRESETS.get(active)
        if p: text += f"🎯 Выбран: {p['icon']} {p['name']}\n\n"
    text += "Выберите роль для ИИ:"
    await update.message.reply_text(text, reply_markup=presets_keyboard())

async def chatowner_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]: await update.message.reply_text("❌ Команда только для групповых чатов!"); return
    chat_id = update.effective_chat.id; user_id = update.effective_user.id; add_chat_owner(chat_id, user_id)
    c = load_chats().get(str(chat_id), {}); owners = c.get("owners", []) if isinstance(c, dict) else c
    text = "👑 ВЛАДЕЛЬЦЫ ЧАТА\n━━━━━━━━━━━━━━━━\n\n"
    for i, oid in enumerate(owners, 1): text += f"{i}. ID: {oid}\n"
    text += "\n💡 Владельцы могут использовать /chatshop для покупки товаров для чата."
    await update.message.reply_text(text)

async def chatshop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]: await update.message.reply_text("❌ Команда только для чатов!"); return
    user_id = update.effective_user.id; chat_id = update.effective_chat.id
    add_chat_owner(chat_id, user_id)
    if not is_chat_owner(chat_id, user_id): await update.message.reply_text("❌ Только владельцы чата могут использовать магазин!\n\nИспользуйте /chatowner чтобы стать владельцем."); return
    premium = is_premium(user_id)
    discount_info = ""
    if premium:
        discount_info = (
            f"\n💎 PREMIUM СКИДКИ ДЛЯ ЧАТА:\n"
            f"• Скидка на все чат-товары: {PREMIUM_CHAT_DISCOUNT}%\n"
            f"• Кэшбек с чат-покупок: {CASHBACK_PERCENT}%\n"
            f"• Цены ниже уже с учётом вашей скидки!"
        )
    await update.message.reply_text(
        f"🛒 МАГАЗИН ЧАТА\n━━━━━━━━━━━━━━━━\n\n"
        f"💰 Ваш баланс: {get_tokens(user_id):,} 💮{discount_info}\n\n"
        f"Выберите категорию товаров для чата:",
        reply_markup=shop_keyboard("chat", user_id)
    )

async def shop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.effective_chat.type
    if chat_type in ["group", "supergroup"]:
        await update.message.reply_text(
            "❌ Команда /shop доступна только в личных сообщениях.\n\n"
            "Для чата используйте:\n"
            "🛒 /chatshop — магазин для чата\n\n"
            "📋 Другие команды для чата:\n"
            "💬 @bot вопрос — задать вопрос\n"
            "🎨 /genimage — генерация фото\n"
            "💸 /transfer — перевод токенов\n"
            "💎 /premium — Premium подписка\n"
            "👤 /profile — профиль участника\n"
            "🆔 /id — узнать ID\n"
            "📊 /tokenrate — курс NBT\n"
            "🌍 /donate — донат\n"
            "👑 /chatowner — владельцы чата"
        )
        return
    await update.message.reply_text("🛒 МАГАЗИН (ЛС)\n\nВыберите категорию:", reply_markup=shop_keyboard("private", update.effective_user.id))

# Админ-команды
async def admin_give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args or len(context.args) < 2: await update.message.reply_text("❌ /give ID СУММА"); return
    try: add_tokens(int(context.args[0]), int(context.args[1])); await update.message.reply_text(f"✅ +{context.args[1]} 💮 пользователю {context.args[0]}")
    except: pass

async def admin_take(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args or len(context.args) < 2: await update.message.reply_text("❌ /take ID СУММА"); return
    try:
        uid = str(int(context.args[0])); amount = int(context.args[1])
        users = load_users(); users[uid]["tokens"] = max(0, users[uid].get("tokens", 0) - amount); users[uid]["spent_tokens"] = users[uid].get("spent_tokens", 0) + amount; save_users(users)
        await update.message.reply_text(f"✅ -{amount} 💮 у {context.args[0]}")
    except: pass

async def admin_resetuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args: await update.message.reply_text("❌ /resetuser ID"); return
    try:
        uid = str(int(context.args[0])); users = load_users()
        if uid in users:
            for f in ["requests_today", "extra_requests", "image_requests_today", "extra_image_requests", "warnings"]: users[uid][f] = 0
            users[uid]["muted_until"] = None; users[uid]["banned"] = False; save_users(users)
        await update.message.reply_text(f"✅ Пользователь {context.args[0]} сброшен")
    except: pass

async def admin_setpremium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args or len(context.args) < 2: await update.message.reply_text("❌ /setpremium ID ДНИ"); return
    try:
        uid = str(int(context.args[0])); days = int(context.args[1]); users = load_users()
        existing = users[uid].get("premium_until")
        base = datetime.fromisoformat(existing) if existing and datetime.now() < datetime.fromisoformat(existing) else datetime.now()
        users[uid]["premium_until"] = (base + timedelta(days=days)).isoformat(); save_users(users)
        await update.message.reply_text(f"✅ Premium {context.args[0]}: +{days} дн.")
    except: pass

async def admin_removepremium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args: await update.message.reply_text("❌ /removepremium ID"); return
    try:
        uid = str(int(context.args[0])); users = load_users()
        if uid in users: users[uid]["premium_until"] = None; save_users(users)
        await update.message.reply_text(f"✅ Premium снят с {context.args[0]}")
    except: pass

async def admin_userinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args: await update.message.reply_text("❌ /userinfo ID"); return
    try:
        u = get_user(int(context.args[0])); un = u.get("username") or "Не указан"
        prem = "💎 Активен" if is_premium(int(context.args[0])) else "Нет"
        prem_until = u.get("premium_until", "Нет")
        banned = "Да" if u.get("banned") else "Нет"
        muted = u.get("muted_until")
        muted_text = f"До {muted[:16]}" if muted and datetime.now() < datetime.fromisoformat(muted) else "Нет"
        await update.message.reply_text(
            f"👤 ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ\n━━━━━━━━━━━━━━━━\n\n"
            f"🆔 ID: {context.args[0]}\n👤 Username: @{un}\n"
            f"💰 Баланс: {u.get('tokens', 0):,} 💮\n💎 Premium: {prem}\n"
            f"⏳ Premium до: {prem_until}\n"
            f"🔥 Серия бонусов: {u.get('daily_bonus_streak', 0)} дн.\n"
            f"💬 Всего запросов: {u.get('total_requests', 0):,}\n"
            f"🎨 Всего генераций: {u.get('total_images', 0):,}\n"
            f"👥 Рефералов: {u.get('referrals', 0)}\n"
            f"💎 Заработано: {u.get('earned_tokens', 0):,} 💮\n"
            f"💸 Потрачено: {u.get('spent_tokens', 0):,} 💮\n"
            f"🌍 Донатов: {u.get('donated_tokens', 0):,} 💮\n"
            f"🔄 Кэшбек: {u.get('cashback_earned', 0):,} 💮\n"
            f"🛡 Предупреждений: {u.get('warnings', 0)}/5\n"
            f"🚫 Забанен: {banned}\n🔇 Мут: {muted_text}\n"
            f"📅 В боте с: {u.get('joined', '?')[:10]}"
        )
    except: pass

async def admin_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    users = load_users()
    top = sorted(users.items(), key=lambda x: x[1].get("tokens", 0), reverse=True)[:15]
    text = "🏆 ТОП-15 ПО ТОКЕНАМ\n━━━━━━━━━━━━━━━━\n\n"
    for i, (uid, data) in enumerate(top, 1):
        name = f"@{data['username']}" if data.get("username") else f"ID:{uid}"
        mark = " 💎" if is_premium(int(uid)) else ""
        text += f"{i}. {name}{mark} — {data.get('tokens', 0):,} 💮\n"
    await update.message.reply_text(text)

async def admin_topreferrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    users = load_users(); top = sorted(users.items(), key=lambda x: x[1].get("referrals", 0), reverse=True)[:15]
    text = "👥 ТОП-15 ПО РЕФЕРАЛАМ\n\n" + "\n".join([f"{i}. @{d.get('username', '?')} — {d.get('referrals', 0)} реф." for i, (_, d) in enumerate(top, 1)])
    await update.message.reply_text(text)

async def admin_topdonators(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    total, count, top_donors = get_donation_stats()
    if not top_donors: await update.message.reply_text("Нет донатов."); return
    text = f"🌍 ТОП-15 ДОНАТОРОВ\n\n🔥 {total:,} 💮\n\n"
    users = load_users()
    for i, (uid, donated) in enumerate(top_donors, 1):
        name = f"@{users.get(uid, {}).get('username', '?')}" if uid in users else f"ID:{uid}"
        text += f"{i}. {name} — {donated:,} 💮\n"
    await update.message.reply_text(text)

async def admin_topactive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    users = load_users(); top = sorted(users.items(), key=lambda x: x[1].get("total_requests", 0), reverse=True)[:15]
    text = "📊 ТОП-15 ПО АКТИВНОСТИ\n\n" + "\n".join([f"{i}. @{d.get('username', '?')} — {d.get('total_requests', 0):,} запр." for i, (_, d) in enumerate(top, 1)])
    await update.message.reply_text(text)

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    users = load_users(); rate_data = get_token_rate()
    donated_total, donated_count, _ = get_donation_stats()
    premium_count = sum(1 for u in users.values() if u.get("premium_until") and datetime.now() < datetime.fromisoformat(u["premium_until"]))
    total_requests = sum(u.get("total_requests", 0) for u in users.values())
    total_images = sum(u.get("total_images", 0) for u in users.values())
    active_today = sum(1 for u in users.values() if u.get("requests_today", 0) > 0)
    await update.message.reply_text(
        f"📊 СТАТИСТИКА БОТА\n━━━━━━━━━━━━━━━━\n\n"
        f"👥 Пользователей: {len(users)}\n💎 Premium: {premium_count}\n"
        f"📊 Активных сегодня: {active_today}\n"
        f"💮 Токенов в обороте: {rate_data.get('total_supply', 0):,} NBT\n"
        f"💰 Капитализация: ${rate_data.get('market_cap', 0):,.2f}\n"
        f"🔥 Донатов: {donated_total:,} 💮 ({donated_count})\n"
        f"💬 Запросов всего: {total_requests:,}\n"
        f"🎨 Генераций всего: {total_images:,}"
    )

async def admin_fullstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    users = load_users(); rate_data = get_token_rate()
    total_tokens = sum(u.get("tokens", 0) for u in users.values())
    total_earned = sum(u.get("earned_tokens", 0) for u in users.values())
    total_spent = sum(u.get("spent_tokens", 0) for u in users.values())
    total_donated = sum(u.get("donated_tokens", 0) for u in users.values())
    total_cashback = sum(u.get("cashback_earned", 0) for u in users.values())
    premium_count = sum(1 for u in users.values() if u.get("premium_until") and datetime.now() < datetime.fromisoformat(u["premium_until"]))
    banned_count = sum(1 for u in users.values() if u.get("banned"))
    await update.message.reply_text(
        f"📊 ПОЛНАЯ СТАТИСТИКА\n━━━━━━━━━━━━━━━━\n\n"
        f"👥 Всего: {len(users)}\n💎 Premium: {premium_count}\n🚫 Забанено: {banned_count}\n\n"
        f"💮 ЭКОНОМИКА:\nВ обороте: {total_tokens:,} NBT\nЗаработано: {total_earned:,} 💮\n"
        f"Потрачено: {total_spent:,} 💮\nПожертвовано: {total_donated:,} 💮\n"
        f"Кэшбек: {total_cashback:,} 💮\nКурс: ${rate_data.get('rate', 0.005):.8f}\n"
        f"Кап: ${rate_data.get('market_cap', 0):,.2f}"
    )

async def admin_economy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    rate_data = get_token_rate()
    await update.message.reply_text(
        f"💮 ЭКОНОМИКА\n━━━━━━━━━━━━━━━━\n\n"
        f"💰 Курс: ${rate_data.get('rate', 0.005):.8f}\n"
        f"💎 Кап: ${rate_data.get('market_cap', 0):,.2f}\n"
        f"🪙 В обороте: {rate_data.get('total_supply', 0):,} NBT\n"
        f"🔥 Сожжено: {rate_data.get('total_burned', 0):,} 💮\n"
        f"🌍 Пожертвовано: {rate_data.get('total_donated', 0):,} 💮\n"
        f"📊 Supply: ×{rate_data.get('supply_factor', 1):.2f}\n"
        f"📊 Activity: ×{rate_data.get('activity_factor', 1):.2f}\n"
        f"📊 Burn: ×{rate_data.get('burn_factor', 1):.2f}\n"
        f"📅 День: {rate_data.get('day_name', '?')} (×{rate_data.get('day_factor', 1):.2f})\n"
        f"📈 Волатильность: ×{rate_data.get('volatility_index', 1):.2f}\n"
        f"🔄 Обновление: {rate_data.get('next_update', '?')}"
    )

async def admin_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args: return
    try: uid = str(int(context.args[0])); users = load_users(); users[uid]["banned"] = True; save_users(users); await update.message.reply_text(f"✅ {context.args[0]} забанен")
    except: pass

async def admin_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args: return
    try: uid = str(int(context.args[0])); users = load_users(); users[uid]["banned"] = False; users[uid]["warnings"] = 0; save_users(users); await update.message.reply_text(f"✅ {context.args[0]} разбанен")
    except: pass

async def admin_mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args or len(context.args) < 2: return
    try: uid = str(int(context.args[0])); hours = int(context.args[1]); users = load_users(); users[uid]["muted_until"] = (datetime.now() + timedelta(hours=hours)).isoformat(); save_users(users); await update.message.reply_text(f"✅ {context.args[0]} замучен на {hours} ч.")
    except: pass

async def admin_unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args: return
    try: uid = str(int(context.args[0])); users = load_users(); users[uid]["muted_until"] = None; save_users(users); await update.message.reply_text(f"✅ Мут снят")
    except: pass

async def admin_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args: return
    try:
        uid = str(int(context.args[0]))
        users = load_users()
        users[uid]["warnings"] = users[uid].get("warnings", 0) + 1
        if users[uid]["warnings"] >= 5:
            users[uid]["banned"] = True
        save_users(users)
        await update.message.reply_text(f"⚠️ Предупреждение {users[uid]['warnings']}/5")
    except:
        pass

async def admin_resetwarns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args: return
    try: uid = str(int(context.args[0])); users = load_users(); users[uid]["warnings"] = 0; save_users(users); await update.message.reply_text(f"✅ Предупреждения сброшены")
    except: pass

async def admin_create_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args or len(context.args) < 2: return
    create_promo(context.args[0].upper(), int(context.args[1]), int(context.args[2]) if len(context.args) > 2 else 0)
    await update.message.reply_text(f"✅ Промокод {context.args[0].upper()} создан")

async def admin_promos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    promos = load_promos()
    if not promos: await update.message.reply_text("🎟 Нет активных промокодов."); return
    text = "🎟 ПРОМОКОДЫ\n\n" + "\n".join([f"{c}: {d['amount']} 💮 ({len(d['used_by'])}/{d['max_uses'] or '∞'})" for c, d in promos.items()])
    await update.message.reply_text(text)

async def admin_delete_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args: return
    promos = load_promos(); code = context.args[0].upper()
    if code in promos: del promos[code]; save_promos(promos)

async def admin_promoinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args: return
    promos = load_promos(); code = context.args[0].upper()
    if code not in promos: await update.message.reply_text("❌ Не найден"); return
    p = promos[code]; users = load_users()
    used_list = "\n".join([f"• {u_id} (@{users.get(u_id, {}).get('username', '?')})" for u_id in p["used_by"]]) or "Никто"
    await update.message.reply_text(f"🎟 {code}\n💰 {p['amount']} 💮\n👥 {len(p['used_by'])}/{p['max_uses'] or '∞'}\n📅 {p.get('created', '?')[:10]}\n\nИспользовали:\n{used_list}")

async def admin_forcediscounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    save_discounts(generate_discounts()); await update.message.reply_text("✅ Скидки обновлены")

async def admin_force_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    d = load_json(TOKEN_RATE_FILE); d["rate_block"] = ""; save_json(TOKEN_RATE_FILE, d)
    await update.message.reply_text(f"💮 Курс обновлён: ${get_token_rate().get('rate', 0.005):.8f}")

async def admin_cleardiscounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    save_discounts({"last_update": datetime.now().strftime("%Y-%m-%d")})

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args: return
    text = " ".join(context.args); users = load_users(); sent = 0
    for uid in users:
        try: await context.bot.send_message(int(uid), f"📢 {text}"); sent += 1; await asyncio.sleep(0.05)
        except: pass
    await update.message.reply_text(f"✅ Отправлено: {sent}")

async def admin_broadcastpremium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args: return
    text = " ".join(context.args); users = load_users(); sent = 0
    for uid in users:
        if is_premium(int(uid)):
            try: await context.bot.send_message(int(uid), f"💎 {text}"); sent += 1; await asyncio.sleep(0.05)
            except: pass
    await update.message.reply_text(f"✅ Premium: {sent}")

async def admin_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    mode = "ВКЛЮЧЕН" if context.args and context.args[0].lower() == "on" else "ВЫКЛЮЧЕН"
    await update.message.reply_text(f"🔧 Режим обслуживания: {mode}")

async def admin_resetalllimits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    users = load_users(); today = datetime.now().strftime("%Y-%m-%d")
    for uid in users:
        for f in ["requests_today", "extra_requests", "image_requests_today", "extra_image_requests", "chat_requests_today", "extra_chat_requests", "chat_image_requests_today", "extra_chat_image_requests"]: users[uid][f] = 0
        users[uid]["reset_date"] = today; users[uid]["daily_transfer_total"] = 0; users[uid]["transfer_reset_date"] = today
    save_users(users); await update.message.reply_text(f"✅ Лимиты сброшены для {len(users)} пользователей")

async def admin_resetuserlimits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args: return
    try:
        uid = str(int(context.args[0])); users = load_users(); today = datetime.now().strftime("%Y-%m-%d")
        if uid in users:
            for f in ["requests_today", "extra_requests", "image_requests_today", "extra_image_requests", "chat_requests_today", "extra_chat_requests", "chat_image_requests_today", "extra_chat_image_requests"]: users[uid][f] = 0
            users[uid]["reset_date"] = today; users[uid]["daily_transfer_total"] = 0; users[uid]["transfer_reset_date"] = today; save_users(users)
        await update.message.reply_text(f"✅ Лимиты {context.args[0]} сброшены")
    except: pass

async def admin_addtokensall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args: return
    try:
        amount = int(context.args[0]); users = load_users()
        for uid in users: users[uid]["tokens"] = users[uid].get("tokens", 0) + amount; users[uid]["earned_tokens"] = users[uid].get("earned_tokens", 0) + amount
        save_users(users)
        await update.message.reply_text(f"✅ +{amount} 💮 для {len(users)} пользователей")
    except: pass

async def reply_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text; user_id = update.effective_user.id
    username = update.effective_user.username
    if username: users = load_users(); users[str(user_id)]["username"] = username; save_users(users)
    
    if text == "💬 NeBlock AI V2":
        users = load_users(); users[str(user_id)]["current_model"] = "text"; users[str(user_id)]["waiting_for_image"] = False; save_users(users)
        await update.message.reply_text(f"💬 NeBlock AI V2\n━━━━━━━━━━━━━━━━\n📊 Осталось запросов: {remaining(user_id)}\n📝 Отправьте ваш вопрос.")
        return True
    if text == "🎨 NeBlock Images V2":
        users = load_users(); users[str(user_id)]["current_model"] = "image"; users[str(user_id)]["waiting_for_image"] = True; save_users(users)
        await update.message.reply_text(f"🎨 NeBlock Images V2\n━━━━━━━━━━━━━━━━\n📊 Осталось генераций: {image_remaining(user_id)}\n📝 Опишите изображение.")
        return True
    if text == "👤 Профиль": await profile_cmd(update, context); return True
    if text == "🛒 Магазин":
        if update.effective_chat.type in ["group", "supergroup"]:
            await update.message.reply_text(
                "❌ Команда /shop доступна только в личных сообщениях.\n\n"
                "Для чата используйте:\n"
                "🛒 /chatshop — магазин для чата\n\n"
                "📋 Другие команды для чата:\n"
                "💬 @bot вопрос — задать вопрос\n"
                "🎨 /genimage — генерация фото\n"
                "💸 /transfer — перевод токенов\n"
                "💎 /premium — Premium подписка\n"
                "👤 /profile — профиль участника\n"
                "🆔 /id — узнать ID\n"
                "📊 /tokenrate — курс NBT\n"
                "🌍 /donate — донат\n"
                "👑 /chatowner — владельцы чата"
            )
            return True
        await update.message.reply_text(f"🛒 МАГАЗИН (ЛС)\n━━━━━━━━━━━━━━━━\n💰 Баланс: {get_tokens(user_id)} 💮\n\nВыберите категорию:", reply_markup=shop_keyboard("private", user_id)); return True
    if text == "💎 Premium": await premium_cmd(update, context); return True
    if text == "🔥 Награды": 
        streak = get_user(user_id).get("daily_bonus_streak", 0)
        await update.message.reply_text(f"🔥 НАГРАДЫ\n━━━━━━━━━━━━━━━━\n\n📊 Серия: {streak} дн.\n💰 Баланс: {get_tokens(user_id)} 💮\n\nВыберите действие:", reply_markup=earn_keyboard()); return True
    if text == "📝 Пресеты": await presets_cmd(update, context); return True
    if text == "💸 Перевод": context.user_data["waiting_transfer"] = True; await update.message.reply_text(f"{TRANSFER_INFO}\n\nОтправьте ID и сумму:\nID КОЛИЧЕСТВО"); return True
    if text == "🌍 Донат": await update.message.reply_text(DONATE_INFO_TEXT); return True
    if text == "🎟 Промокод": context.user_data["waiting_promo"] = True; await update.message.reply_text("🎟 Отправьте промокод."); return True
    if text == "💮 Курс NBT": await tokenrate_cmd(update, context); return True
    if text == "📚 FAQ": await update.message.reply_text(FAQ_TEXT[:4000]); return True
    if text == "🎫 Скидки":
        discounts = get_discounts(); active = {k: v for k, v in discounts.items() if k not in ["last_update", "generated_at"]}
        shop_items = get_shop_items(user_id)
        txt = f"🎫 АКТИВНЫЕ СКИДКИ\n━━━━━━━━━━━━━━━━\n\n🔄 Обновление: каждые 2 дня в 9:00 МСК\n\n"
        if not active: txt += "Сейчас нет активных скидок.\nНовые появятся при следующем обновлении!"
        else:
            for item_id, disc in sorted(active.items(), key=lambda x: x[1]["percent"], reverse=True):
                item = shop_items.get(item_id)
                if item:
                    current_price = item["price"]
                    discounted_price = max(1, int(current_price * (1 - disc["percent"] / 100)))
                    txt += f"{disc.get('color', '🟢')} {disc.get('icon', '🏷️')} {item['icon']} {item['name']}\n"
                    txt += f"   Скидка: -{disc['percent']}%\n"
                    txt += f"   Тип: {disc.get('type_name', 'Обычная')}\n"
                    txt += f"   Цена: {discounted_price} 💮 (было {current_price} 💮)\n\n"
        await update.message.reply_text(txt); return True
    return False

async def inline_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    chat_type = update.effective_chat.type
    shop_items = get_shop_items(user_id)
    premium = is_premium(user_id)
    
    if data == "none": return
    if data == "transfer_cancel": await query.edit_message_text("❌ Перевод отменён."); return
    if data == "donate_cancel": await query.edit_message_text("❌ Донат отменён."); return
    
    if data.startswith("donate_confirm_"):
        amount = int(data.replace("donate_confirm_", ""))
        if get_user(user_id).get("tokens", 0) < amount: await query.edit_message_text("❌ Недостаточно!"); return
        if donate_tokens(user_id, amount):
            donated_total, _, _ = get_donation_stats()
            await query.edit_message_text(f"🌍 ДОНАТ ВЫПОЛНЕН!\n━━━━━━━━━━━━━━━━\n\n🔥 Сожжено: {amount:,} 💮\n💎 Баланс: {get_tokens(user_id):,} 💮\n🌍 Всего сожжено: {donated_total:,} 💮")
        return
    
    if data.startswith("transfer_confirm_"):
        parts = data.split("_")
        if len(parts) >= 4:
            to_id = int(parts[2]); amount = int(parts[3])
            if get_user(user_id).get("tokens", 0) < amount: await query.edit_message_text("❌ Недостаточно!"); return
            tax, tax_percent, _ = get_transfer_tax(amount, premium)
            receiver = get_user(to_id)
            if not receiver: await query.edit_message_text("❌ Получатель не найден!"); return
            final_amount = amount - tax
            users = load_users(); uid_from = str(user_id); uid_to = str(to_id)
            users[uid_from]["tokens"] = users[uid_from].get("tokens", 0) - amount
            users[uid_from]["daily_transfer_total"] = users[uid_from].get("daily_transfer_total", 0) + amount
            users[uid_to]["tokens"] = users[uid_to].get("tokens", 0) + final_amount
            save_users(users); log_transfer(user_id, to_id, amount, tax, final_amount)
            tax_info = f"\n📊 Налог: {tax} 💮 ({tax_percent}%)" if tax > 0 else "\n📊 Без налога"
            await query.edit_message_text(f"✅ ПЕРЕВОД ВЫПОЛНЕН!\n━━━━━━━━━━━━━━━━\n\n👤 ID {to_id}\n💸 {amount:,} 💮\n💰 Зачислено: {final_amount:,} 💮{tax_info}\n💎 Баланс: {get_tokens(user_id):,} 💮")
        return
    
    if data == "show_discounts":
        discounts = get_discounts(); active = {k: v for k, v in discounts.items() if k not in ["last_update", "generated_at"]}
        text = "🎫 АКТИВНЫЕ СКИДКИ\n━━━━━━━━━━━━━━━━\n\n"
        if not active: text += "Сейчас нет активных скидок.\nНовые появятся при обновлении (каждые 2 дня в 9:00 МСК)."
        else:
            text += "🔄 Обновление: каждые 2 дня в 9:00 МСК\n\n"
            for item_id, disc in sorted(active.items(), key=lambda x: x[1]["percent"], reverse=True):
                item = shop_items.get(item_id)
                if item:
                    current_price = item["price"]
                    discounted_price = max(1, int(current_price * (1 - disc["percent"] / 100)))
                    text += f"{disc.get('color', '🟢')} {disc.get('icon', '🏷️')} {item['icon']} {item['name']}\n"
                    text += f"   Скидка: -{disc['percent']}%\n"
                    text += f"   Тип: {disc.get('type_name', 'Обычная')}\n"
                    text += f"   Цена: {discounted_price} 💮 (было {current_price} 💮)\n\n"
        await query.edit_message_text(text, reply_markup=back_button())
        return
    
    if data == "chat_shop_info":
        premium_info = ""
        if premium:
            premium_info = (
                f"\n\n💎 PREMIUM СКИДКИ:\n"
                f"• Скидка на чат-товары: {PREMIUM_CHAT_DISCOUNT}%\n"
                f"• Кэшбек с чат-покупок: {CASHBACK_PERCENT}%\n"
                f"• Цены в /chatshop уже с учётом скидки!"
            )
        text = (
            f"👥 МАГАЗИН ЧАТА\n━━━━━━━━━━━━━━━━\n\n"
            f"Товары для чата покупаются владельцем чата и действуют на всех участников.\n\n"
            f"📊 ДОСТУПНЫЕ КАТЕГОРИИ:\n"
            f"• Запросы в чатах (10/50/безлимит)\n"
            f"• Генерация фото в чатах (5/20/безлимит)\n"
            f"• Premium для чата (день/неделя/месяц/год/навсегда)\n\n"
            f"💡 Используйте /chatshop в групповом чате для покупки.{premium_info}"
        )
        await query.edit_message_text(text, reply_markup=back_button())
        return
    
    if data == "profile_chat":
        await profile_cmd(update, context)
        await query.edit_message_text("👤 Профиль отправлен в чат.")
        return
    
    if data == "notify_menu":
        if not premium: await query.edit_message_text("❌ Только для Premium 💎", reply_markup=back_button()); return
        user = get_user(user_id); current = user.get("notify_interval", DEFAULT_NOTIFY_INTERVAL_PREMIUM)
        await query.edit_message_text(f"🔔 НАСТРОЙКА УВЕДОМЛЕНИЙ\n━━━━━━━━━━━━━━━━\n\nТекущий интервал: каждые {current} ч.\nДоступные: {', '.join(map(str, PREMIUM_NOTIFY_OPTIONS))} ч.\n\nУведомления приходят автоматически!\nВыберите новый интервал:", reply_markup=notify_keyboard())
        return
    
    if data.startswith("notify_"):
        if not premium: await query.edit_message_text("❌ Только для Premium 💎", reply_markup=back_button()); return
        try:
            interval = int(data.replace("notify_", ""))
            if interval in PREMIUM_NOTIFY_OPTIONS:
                users = load_users(); uid = str(user_id); users[uid]["notify_interval"] = interval; save_users(users)
                await query.edit_message_text(f"✅ Установлен интервал: каждые {interval} ч.\n\nУведомления приходят автоматически!", reply_markup=back_button())
        except: pass
        return
    
    if data == "premium_shop": await query.edit_message_text(f"🛒 ПОКУПКА PREMIUM\n━━━━━━━━━━━━━━━━\n💰 Баланс: {get_tokens(user_id):,} 💮\n\nВыберите тариф:", reply_markup=shop_keyboard("private", user_id)); return
    if data == "premium_menu": await premium_cmd(update, context); return
    
    if data == "presets_menu":
        if not premium: await query.edit_message_text("❌ Пресеты только для Premium 💎\n\n📋 Пресеты КОПИРУЮТСЯ в запрос, а не активируются.\n💎 /premium — купить Premium", reply_markup=back_button()); return
        await presets_cmd(update, context); return
    
    if data.startswith("preset_"):
        if not premium: await query.edit_message_text("❌ Только для Premium 💎", reply_markup=back_button()); return
        preset_id = data.replace("preset_", "")
        if preset_id == "off":
            users = load_users(); users[str(user_id)]["active_preset"] = None; save_users(users)
            await query.edit_message_text("✅ Пресет отключён.", reply_markup=back_button()); return
        preset = PREMIUM_PRESETS.get(preset_id)
        if preset:
            users = load_users(); users[str(user_id)]["active_preset"] = preset_id; save_users(users)
            await query.edit_message_text(
                f"✅ ВЫБРАН ПРЕСЕТ\n\n{preset['icon']} {preset['name']}\n📝 {preset['description']}\n\n"
                f"📋 Инструкция роли будет СКОПИРОВАНА в ваш запрос.\n"
                f"Работает только в личных сообщениях.",
                reply_markup=back_button()
            )
        return
    
    if data == "menu":
        if chat_type in ["group", "supergroup"]:
            await query.edit_message_text(f"🧠 NeBlock AI V{BOT_VERSION} в чате\n\n💰 Баланс: {get_tokens(user_id):,} 💮\n\nВыберите раздел:", reply_markup=chat_menu())
        else:
            await query.edit_message_text(f"🧠 NeBlock AI V{BOT_VERSION}\n\n💰 Баланс: {get_tokens(user_id):,} 💮\n\nВыберите раздел:", reply_markup=private_menu())
        return
    
    if data == "about":
        await query.edit_message_text(
            f"ℹ️ О БОТЕ NeBlock AI\n━━━━━━━━━━━━━━━━\n\n"
            f"📌 Версия: {BOT_VERSION}\n\n"
            f"💬 NeBlock AI V2 — текстовая модель\n"
            f"🎨 NeBlock Images V2 — генерация изображений\n"
            f"💸 Переводы токенов между пользователями\n"
            f"🌍 Благотворительность — сжигание токенов\n"
            f"🔥 Ежедневные награды — серия до 30 дней\n"
            f"💮 Внутренняя валюта NBT с рыночным курсом\n"
            f"💎 Premium — безлимит и привилегии\n"
            f"💤 Пассивный доход для всех пользователей\n\n"
            f"📊 Лимиты ЛС: {DAILY_LIMIT} текст + {IMAGE_DAILY_LIMIT} фото/день\n"
            f"📊 Лимиты чатов: {CHAT_DAILY_LIMIT} текст + {CHAT_IMAGE_LIMIT} фото/день\n\n"
            f"💡 /faq — ответы на частые вопросы",
            reply_markup=back_button()
        )
        return
    
    if data == "stats":
        u = get_user(user_id); prem = is_premium(user_id)
        await query.edit_message_text(
            f"📊 СТАТИСТИКА\n━━━━━━━━━━━━━━━━\n\n"
            f"💬 Запросов сегодня: {u.get('requests_today', 0)}\n"
            f"🎨 Генераций сегодня: {u.get('image_requests_today', 0)}\n"
            f"💰 Баланс: {u.get('tokens', 0):,} 💮\n"
            f"🔥 Серия: {u.get('daily_bonus_streak', 0)} дн.\n"
            f"🌍 Донатов: {u.get('donated_tokens', 0):,} 💮\n"
            f"👥 Рефералов: {u.get('referrals', 0)}\n"
            + (f"🔄 Кэшбек: {u.get('cashback_earned', 0):,} 💮\n" if prem else ""),
            reply_markup=back_button()
        )
        return
    
    if data == "shop":
        if chat_type in ["group", "supergroup"]:
            await query.edit_message_text(
                "❌ Магазин ЛС доступен только в личных сообщениях.\n\n"
                "Для чата используйте:\n"
                "🛒 /chatshop — магазин для чата",
                reply_markup=back_button()
            )
            return
        await query.edit_message_text(f"🛒 МАГАЗИН (ЛС)\n━━━━━━━━━━━━━━━━\n💰 Баланс: {get_tokens(user_id):,} 💮\n\nВыберите категорию:", reply_markup=shop_keyboard("private", user_id)); return
    
    if data == "earn":
        if chat_type in ["group", "supergroup"]:
            await query.edit_message_text("❌ Награды доступны только в личных сообщениях.", reply_markup=back_button())
            return
        streak = get_user(user_id).get("daily_bonus_streak", 0)
        await query.edit_message_text(f"🔥 НАГРАДЫ И БОНУСЫ\n━━━━━━━━━━━━━━━━\n\n📊 Серия: {streak} дн.\n💰 Баланс: {get_tokens(user_id):,} 💮\n\nВыберите действие:", reply_markup=earn_keyboard()); return
    
    if data == "daily_bonus":
        if chat_type in ["group", "supergroup"]:
            await query.answer("❌ Ежедневный бонус доступен только в ЛС!", show_alert=True)
            return
        u = get_user(user_id); today = datetime.now().strftime("%Y-%m-%d")
        if u.get("daily_bonus_claimed") == today: await query.answer("❌ Вы уже забирали бонус сегодня! Приходите завтра.", show_alert=True); return
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
            premium_text = "\n🎁 + Premium ЛС на 1 день!"
        await query.answer(f"🎉 +{bonus} 💮!")
        await query.edit_message_text(
            f"🎁 ЕЖЕДНЕВНЫЙ БОНУС ПОЛУЧЕН!\n━━━━━━━━━━━━━━━━\n\n"
            f"{icon} {day_name}\n"
            f"💰 Получено: +{bonus} 💮{premium_text}\n"
            f"💎 Баланс: {get_tokens(user_id):,} 💮\n"
            f"🔥 Серия: {streak} дн.\n\n"
            f"⚠️ Заберите завтрашний бонус до 00:00 МСК!\n"
            f"🔄 Пропуск дня сбросит серию.",
            reply_markup=back_button()
        )
        return
    
    if data == "ref_link":
        if chat_type in ["group", "supergroup"]:
            await query.edit_message_text("❌ Реферальная ссылка доступна только в ЛС.", reply_markup=back_button())
            return
        user = get_user(user_id); bot_username = (await context.bot.get_me()).username
        bonus_you = PREMIUM_REFERRAL_BONUS if premium else REFERRAL_BONUS
        bonus_friend = PREMIUM_INVITED_BONUS if premium else INVITED_BONUS
        await query.edit_message_text(
            f"👥 РЕФЕРАЛЬНАЯ ПРОГРАММА\n━━━━━━━━━━━━━━━━\n\n"
            f"🔗 Ваша ссылка:\nhttps://t.me/{bot_username}?start=ref_{user.get('referral_code', '')}\n\n"
            f"💰 Вы получаете: +{bonus_you} 💮 за каждого друга\n"
            f"🎁 Друг получает: +{bonus_friend} 💮 при регистрации\n"
            f"📊 Ваши рефералы: {user.get('referrals', 0)}\n"
            + (f"\n💎 Premium бонусы ×3 активированы!" if premium else f"\n💡 С Premium: +{PREMIUM_REFERRAL_BONUS}/{PREMIUM_INVITED_BONUS} 💮"),
            reply_markup=back_button()
        )
        return
    
    if data == "streak_info": await query.edit_message_text(STREAK_INFO[:4000], reply_markup=back_button()); return
    if data == "donate_info": await query.edit_message_text(DONATE_INFO_TEXT, reply_markup=back_button()); return
    if data == "models": await query.edit_message_text("🧠 МОДЕЛИ NeBlock AI\n━━━━━━━━━━━━━━━━\n\n💬 NeBlock AI V2 — текстовая модель\n🎨 NeBlock Images V2 — генерация изображений\n📝 /genimage — создать изображение", reply_markup=back_button()); return
    if data == "tokenrate":
        rd = get_token_rate()
        await query.edit_message_text(
            f"💮 КУРС NBT\n━━━━━━━━━━━━━━━━\n\n"
            f"💰 1 NBT = ${rd.get('rate', 0.005):.8f}\n"
            f"💎 Капитализация: ${rd.get('market_cap', 0):,.2f}\n"
            f"🪙 В обороте: {rd.get('total_supply', 0):,} NBT\n"
            f"🔥 Сожжено: {rd.get('total_donated', 0):,} 💮\n"
            f"{rd.get('day_icon', '📊')} {rd.get('day_name', '')} | 🔄 {rd.get('next_update', '')}\n\n"
            f"💡 Курс влияет на размер ежедневных наград!",
            reply_markup=back_button()
        ); return
    if data == "transfer": context.user_data["waiting_transfer"] = True; await query.edit_message_text(f"{TRANSFER_INFO}\n\n💸 Отправьте ID и сумму:\nID КОЛИЧЕСТВО\nПример: 1671403667 100", reply_markup=back_button()); return
    if data == "commands": await query.edit_message_text(COMMANDS_LIST, reply_markup=back_button()); return
    if data == "changelog": await query.edit_message_text(CHANGELOG, reply_markup=back_button()); return
    if data == "promo": context.user_data["waiting_promo"] = True; await query.edit_message_text("🎟 АКТИВАЦИЯ ПРОМОКОДА\n\nОтправьте промокод для получения бонуса.", reply_markup=back_button()); return
    if data == "faq": await query.edit_message_text(FAQ_TEXT[:4000], reply_markup=back_button()); return
    
    if data.startswith("confirm_"):
        item_id = data.replace("confirm_", ""); item = shop_items.get(item_id)
        if not item: return
        if item.get("location") == "private" and chat_type in ["group", "supergroup"]:
            await query.answer("❌ Покупка товаров ЛС доступна только в личных сообщениях!", show_alert=True)
            return
        price, percent, disc = get_discounted_price(item_id, user_id)
        if get_tokens(user_id) < price: await query.answer("❌ Недостаточно токенов!", show_alert=True); return
        if item_id == "premium_forever" and is_premium(user_id):
            user = get_user(user_id)
            if user.get("premium_until") and (datetime.fromisoformat(user["premium_until"]) - datetime.now()).days > 36500:
                await query.answer("❌ У вас уже куплен Premium НАВСЕГДА!", show_alert=True); return
        remove_tokens(user_id, price); cashback = process_cashback(user_id, price, item_id)
        users = load_users(); uid = str(user_id)
        actions = {"extra5": ("extra_requests", 5), "extra10": ("extra_requests", 10), "extra50": ("extra_requests", 50), "image1": ("extra_image_requests", 1), "image5": ("extra_image_requests", 5), "image20": ("extra_image_requests", 20), "chat_extra10": ("extra_chat_requests", 10), "chat_extra50": ("extra_chat_requests", 50), "chat_image5": ("extra_chat_image_requests", 5), "chat_image20": ("extra_chat_image_requests", 20)}
        time_actions = {"unlimited_1h": ("unlimited_until", 1), "unlimited_24h": ("unlimited_until", 24), "unlimited_7d": ("unlimited_until", 168), "image_unlimited_1h": ("image_unlimited_until", 1), "chat_unlimited_1h": ("chat_unlimited_until", 1), "chat_unlimited_24h": ("chat_unlimited_until", 24)}
        premium_actions = {"premium_day": 1, "premium_week": 7, "premium_30d": 30, "premium_60d": 60, "premium_90d": 90, "premium_year": 365, "premium_forever": 36500, "chat_premium_day": 1, "chat_premium_week": 7, "chat_premium_30d": 30, "chat_premium_60d": 60, "chat_premium_90d": 90, "chat_premium_year": 365, "chat_premium_forever": 36500}
        if item_id in actions: field, amount = actions[item_id]; users[uid][field] = users[uid].get(field, 0) + amount
        elif item_id in time_actions: field, hours = time_actions[item_id]; users[uid][field] = (datetime.now() + timedelta(hours=hours)).isoformat()
        elif item_id in premium_actions:
            days = premium_actions[item_id]
            if item_id.startswith("chat_"):
                existing = users[uid].get("chat_premium_until")
                base = datetime.fromisoformat(existing) if existing and datetime.now() < datetime.fromisoformat(existing) else datetime.now()
                users[uid]["chat_premium_until"] = (base + timedelta(days=days)).isoformat()
            else:
                existing = users[uid].get("premium_until")
                base = datetime.fromisoformat(existing) if existing and datetime.now() < datetime.fromisoformat(existing) else datetime.now()
                users[uid]["premium_until"] = (base + timedelta(days=days)).isoformat()
        save_users(users)
        dt = f"\n🎫 Скидка: -{percent}%" if percent > 0 else ""
        if disc and disc.get("type") == "legendary": dt = "\n🌟 ЛЕГЕНДАРНАЯ СКИДКА! Товар бесплатно!"
        cashback_text = f"\n🔄 Кэшбек: +{cashback} 💮" if cashback > 0 else ""
        await query.answer(f"✅ {item['name']} куплен!", show_alert=True)
        await query.edit_message_text(f"✅ ПОКУПКА ВЫПОЛНЕНА!\n━━━━━━━━━━━━━━━━\n\n{item['icon']} {item['name']}\n{dt}{cashback_text}\n💰 Потрачено: {price} 💮\n💎 Остаток: {get_tokens(user_id):,} 💮\n⏱ Действует: {item.get('duration', 'Н/Д')}", reply_markup=back_button())
        return
    
    if data.startswith("buy_"):
        item_id = data.replace("buy_", ""); item = shop_items.get(item_id)
        if not item: return
        if item.get("location") == "private" and chat_type in ["group", "supergroup"]:
            await query.answer("❌ Карточка товара ЛС недоступна в чате. Используйте личные сообщения.", show_alert=True)
            return
        price, percent, disc = get_discounted_price(item_id, user_id)
        tokens = get_tokens(user_id); can = "✅ Хватает" if tokens >= price else "❌ Не хватает"
        
        premium_discount_info = ""
        if premium:
            if item.get("category") == "premium" and item.get("location") == "private":
                regular_price = get_item_price(item_id)
                saved = regular_price - price
                premium_discount_info = f"\n💎 СКИДКА PREMIUM НА ПРОДЛЕНИЕ: {PREMIUM_RENEWAL_DISCOUNT}%\n💵 Цена без скидки: {regular_price} 💮\n💰 Ваша экономия: {saved} 💮"
            elif item.get("location") == "chat":
                regular_price = get_item_price(item_id)
                saved = regular_price - price
                premium_discount_info = f"\n💎 СКИДКА PREMIUM НА ЧАТ: {PREMIUM_CHAT_DISCOUNT}%\n💵 Цена без скидки: {regular_price} 💮\n💰 Ваша экономия: {saved} 💮"
        
        cashback_info = ""
        if premium and item.get("location") == "chat":
            cashback_info = f"\n🔄 КЭШБЕК С ПОКУПКИ: +{int(price * CASHBACK_PERCENT / 100)} 💮 ({CASHBACK_PERCENT}%)"
        
        benefits_text = "\n".join([f"  ✓ {b}" for b in item.get("benefits", [])])
        dt = f"\n\n💵 Цена: {price} 💮"
        if percent > 0 and disc:
            if disc.get("type") == "legendary": dt = "\n\n🌟 ЛЕГЕНДАРНАЯ СКИДКА 100%!\n💰 Цена: 0 💮 (БЕСПЛАТНО!)"
            else: dt = f"\n\n{disc.get('color', '🟢')} СКИДКА {disc.get('icon', '🏷️')} {percent}%\n💵 Обычная цена: {item['price']} 💮\n🔥 Цена со скидкой: {price} 💮\n💰 Ваша экономия: {item['price'] - price} 💮"
        
        premium_comparison = ""
        if item_id.startswith("premium_"):
            premium_comparison = (
                f"\n\n📊 ЧТО ВЫ ПОЛУЧАЕТЕ С PREMIUM:\n"
                f"┌────────────────────────────┬──────────────┬──────────────┐\n"
                f"│ Возможность                │     FREE     │   PREMIUM    │\n"
                f"├────────────────────────────┼──────────────┼──────────────┤\n"
                f"│ Текстовые запросы (ЛС)     │   {DAILY_LIMIT}/день      │  Безлимит    │\n"
                f"│ Генерация фото (ЛС)        │   {IMAGE_DAILY_LIMIT}/день      │  Безлимит    │\n"
                f"│ Профессиональные пресеты   │      ❌      │   10 ролей   │\n"
                f"│ Пассивный доход            │  2 💮/час    │ 20 💮/30мин  │\n"
                f"│ Кэшбек с чат-покупок       │      0%      │     {CASHBACK_PERCENT}%      │\n"
                f"│ Рефералы                   │  {REFERRAL_BONUS}/{INVITED_BONUS} 💮      │  {PREMIUM_REFERRAL_BONUS}/{PREMIUM_INVITED_BONUS} 💮       │\n"
                f"│ Лимит перевода             │  {MAX_TRANSFER:,} 💮   │ {PREMIUM_MAX_TRANSFER:,} 💮  │\n"
                f"│ Умные уведомления          │  каждые 24ч  │   1-24ч      │\n"
                f"│ Значок 💎                  │      ❌      │      ✅      │\n"
                f"└────────────────────────────┴──────────────┴──────────────┘"
            )
        
        text = (
            f"🛒 {item['icon']} {item['name']}\n━━━━━━━━━━━━━━━━\n\n"
            f"📝 ОПИСАНИЕ:\n{item['desc']}\n\n"
            f"✨ ПРЕИМУЩЕСТВА:\n{benefits_text}\n"
            f"{dt}{premium_discount_info}{cashback_info}{premium_comparison}\n\n"
            f"⏱ Длительность: {item.get('duration', 'Н/Д')}\n"
            f"📦 Тип товара: {item.get('type', 'Н/Д')}\n"
            f"⚠️ {item.get('warning', '')}\n\n"
            f"💎 Ваш баланс: {tokens:,} 💮\n{can}"
        )
        await query.edit_message_text(text, reply_markup=confirm_keyboard(item_id))
        return

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤔 Неизвестная команда.\n\nИспользуйте /start для главного меню или /commands для списка всех команд.")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip() if update.message.text else ""
    user_id = update.effective_user.id; chat_type = update.effective_chat.type; chat_id = update.effective_chat.id
    bot_username = context.bot.username
    username = update.effective_user.username
    if username: users = load_users(); users[str(user_id)]["username"] = username; save_users(users)
    if is_user_muted(user_id): await update.message.reply_text("🚫 Вы заблокированы или замучены."); return
    is_clean, _, reason = moderate_content(text)
    if not is_clean: _, warn = warn_user(user_id); await update.message.reply_text(f"⚠️ {reason}\n{warn}"); return
    if context.user_data.get("waiting_transfer"):
        context.user_data["waiting_transfer"] = False
        parts = text.split()
        if len(parts) >= 2:
            try: to_id = int(parts[0]); amount = int(parts[1]); context.args = [str(to_id), str(amount)]; await transfer_cmd(update, context); return
            except: await update.message.reply_text("❌ Неверный формат. Используйте: ID КОЛИЧЕСТВО"); return
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
        if not text:
            await update.message.reply_text(
                f"🧠 NeBlock AI V2 готов помочь!\n\n"
                f"💬 @{bot_username} ваш вопрос — задать вопрос\n"
                f"🎨 @{bot_username} нарисуй описание — генерация фото\n"
                f"💸 /transfer — перевод токенов\n"
                f"👤 /profile — профиль участника",
                reply_to_message_id=update.message.message_id
            )
            return
    user = get_user(user_id)
    if context.user_data.get("waiting_promo"): context.user_data["waiting_promo"] = False; success, result = use_promo(user_id, text); await update.message.reply_text(f"🎟 Промокод активирован! +{result} 💮" if success else f"❌ {result}"); return
    active_preset_id = user.get("active_preset")
    if active_preset_id and is_premium(user_id) and chat_type == "private" and not is_image_request:
        preset = PREMIUM_PRESETS.get(active_preset_id)
        if preset: text = f"[Инструкция: {preset['system_prompt']}]\n\nЗапрос: {text}"
    if is_image_request or (chat_type == "private" and user.get("current_model") == "image"):
        if chat_type == "private": users = load_users(); users[str(user_id)]["waiting_for_image"] = False; save_users(users)
        if not can_image_request(user_id, chat_type, chat_id): await update.message.reply_text("🚫 Лимит генераций исчерпан!\n\n💡 Купите генерации в /shop или активируйте Premium.", reply_markup=limit_reached_keyboard() if chat_type == "private" else None); return
        msg = await update.message.reply_text("🎨 Генерирую изображение...", reply_to_message_id=update.message.message_id if chat_type != "private" else None)
        try:
            image_bytes, error = await generate_image(text)
            if image_bytes: add_image_request(user_id, chat_type); await msg.delete(); await update.message.reply_photo(photo=image_bytes, caption=f"🎨 NeBlock Images V2\n📝 {text[:200]}", reply_to_message_id=update.message.message_id if chat_type != "private" else None)
            else: await msg.edit_text("❌ Ошибка генерации.")
        except: await msg.edit_text("❌ Ошибка генерации.")
        return
    if not can_request(user_id, chat_type, chat_id): await update.message.reply_text("🚫 Лимит запросов исчерпан!\n\n💡 Купите запросы в /shop или активируйте Premium.", reply_markup=limit_reached_keyboard() if chat_type == "private" else None); return
    msg = await update.message.reply_text("💬 Генерирую ответ...", reply_to_message_id=update.message.message_id if chat_type != "private" else None)
    try:
        response = client.responses.create(prompt={"id": PROMPT_ID}, input=text); answer = response.output_text
        add_request(user_id, chat_type); await msg.delete()
        if answer:
            rem = remaining(user_id, chat_type, chat_id)
            footer = f"\n\n━━━━━━━━━━━━━━━━\n💬 NeBlock AI V2 | Осталось: {rem}{AI_DISCLAIMER}"
            for i in range(0, len(answer), 4000): await update.message.reply_text(answer[i:i+4000] + (footer if i == 0 else ""), reply_to_message_id=update.message.message_id if chat_type != "private" else None)
        else: await update.message.reply_text(f"🤷 Пустой ответ{AI_DISCLAIMER}")
    except: await msg.edit_text(f"❌ Ошибка генерации{AI_DISCLAIMER}")

def main():
    print(f"🧠 NeBlock AI V{BOT_VERSION}")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Автоматические уведомления (каждые 5 минут)
    job_queue = app.job_queue
    job_queue.run_repeating(auto_notification_task, interval=300, first=10)
    
    for cmd, handler in [
        ("start", start), ("id", id_cmd), ("profile", profile_cmd),
        ("faq", lambda u, c: u.message.reply_text(FAQ_TEXT[:4000])),
        ("changelog", lambda u, c: u.message.reply_text(CHANGELOG)),
        ("commands", lambda u, c: u.message.reply_text(COMMANDS_LIST)),
    ]: app.add_handler(CommandHandler(cmd, handler))
    
    for cmd, handler in [
        ("premium", premium_cmd), ("buy_premium", buy_premium_cmd), ("notify", notify_cmd),
    ]: app.add_handler(CommandHandler(cmd, handler))
    
    for cmd, handler in [
        ("streak", streak_cmd), ("streak_info", lambda u, c: u.message.reply_text(STREAK_INFO[:4000])),
        ("tokenrate", tokenrate_cmd), ("transfer", transfer_cmd),
        ("transferinfo", lambda u, c: u.message.reply_text(TRANSFER_INFO)),
        ("donate", donate_cmd), ("donatetop", donatetop_cmd),
        ("promo", lambda u, c: setattr(c, 'user_data', {**c.user_data, 'waiting_promo': True}) or u.message.reply_text("🎟 Отправьте промокод.")),
    ]: app.add_handler(CommandHandler(cmd, handler))
    
    app.add_handler(CommandHandler("genimage", genimage_cmd))
    app.add_handler(CommandHandler("presets", presets_cmd))
    app.add_handler(CommandHandler("shop", shop_cmd))
    app.add_handler(CommandHandler("shopdesc", lambda u, c: u.message.reply_text("📋 МАГАЗИН\n\n/shop — магазин для личных сообщений\n/chatshop — магазин для групповых чатов")))
    app.add_handler(CommandHandler("discounts", lambda u, c: inline_button_handler(u, c)))
    app.add_handler(CommandHandler("chatowner", chatowner_cmd))
    app.add_handler(CommandHandler("chatshop", chatshop_cmd))
    
    admin_handlers = [
        ("give", admin_give), ("take", admin_take), ("addtokensall", admin_addtokensall),
        ("resetuser", admin_resetuser), ("setpremium", admin_setpremium), ("removepremium", admin_removepremium),
        ("userinfo", admin_userinfo), ("top", admin_top), ("topreferrals", admin_topreferrals),
        ("topdonators", admin_topdonators), ("topactive", admin_topactive),
        ("stats", admin_stats), ("fullstats", admin_fullstats), ("economy", admin_economy),
        ("ban", admin_ban), ("unban", admin_unban), ("mute", admin_mute),
        ("unmute", admin_unmute), ("warn", admin_warn), ("resetwarns", admin_resetwarns),
        ("createpromo", admin_create_promo), ("promos", admin_promos),
        ("deletepromo", admin_delete_promo), ("promoinfo", admin_promoinfo),
        ("forcediscounts", admin_forcediscounts), ("forcerate", admin_force_rate),
        ("cleardiscounts", admin_cleardiscounts), ("broadcast", admin_broadcast),
        ("broadcastpremium", admin_broadcastpremium), ("maintenance", admin_maintenance),
        ("resetalllimits", admin_resetalllimits), ("resetuserlimits", admin_resetuserlimits),
    ]
    for cmd, handler in admin_handlers:
        app.add_handler(CommandHandler(cmd, handler))
    
    app.add_handler(CallbackQueryHandler(inline_button_handler))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    print("✅ Бот запущен!")
    print("🔔 Авто-уведомления: каждые 5 минут")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
