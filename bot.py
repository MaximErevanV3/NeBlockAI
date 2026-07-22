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
# 🧠 NeBlock AI V5.3 - Конфигурация
# ═══════════════════════════════════════════

TELEGRAM_TOKEN = "8700124191:AAE6qSSouLjlDxPWwoFObJORMbDotsby9co"
YANDEX_API_KEY = "AQVNy7Dm-dvQRzejHvH0383oHTZhhW2fda95I558"
YANDEX_FOLDER = "b1guk4h3j9t48lsjl6sq"
PROMPT_ID = "fvt621uiq1fftiu5qomu"
IMAGE_MODEL = "art://b1guk4h3j9t48lsjl6sq/aliceai-image-art-3.0/latest"

# ═══════════════════════════════════════════
# 📊 БАЛАНСИРОВКА ЭКОНОМИКИ V5.3
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
PRESETS_FILE = "presets.json"
ADMIN_IDS = [1671403667]

START_BONUS = 25
REFERRAL_BONUS = 15
INVITED_BONUS = 5
PREMIUM_REFERRAL_BONUS = 35
PREMIUM_INVITED_BONUS = 12
CASHBACK_PERCENT = 15
PASSIVE_INCOME_HOURLY = 2
PASSIVE_INCOME_MAX_HOURS = 12

# Скидки для Premium пользователей
PREMIUM_RENEWAL_DISCOUNT = 15      # Скидка на продление Premium
PREMIUM_CHAT_DISCOUNT = 10         # Скидка на чат-товары

BOT_VERSION = "5.3"

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
    2: {"name": "День 2", "base_min": 2, "base_max": 4, "icon": "🌿", "desc": "Второй день подряд."},
    3: {"name": "День 3", "base_min": 2, "base_max": 5, "icon": "🌳", "desc": "Третий день!"},
    4: {"name": "День 4", "base_min": 3, "base_max": 6, "icon": "🍀", "desc": "Четвёртый день."},
    5: {"name": "День 5", "base_min": 3, "base_max": 7, "icon": "⭐", "desc": "Пятый день."},
    6: {"name": "День 6", "base_min": 4, "base_max": 8, "icon": "🌟", "desc": "Шестой день."},
    7: {"name": "НЕДЕЛЯ! 🎉", "base_min": 5, "base_max": 10, "icon": "🔥", "desc": "Целая неделя!"},
    8: {"name": "День 8", "base_min": 5, "base_max": 11, "icon": "💫", "desc": "Вторая неделя!"},
    9: {"name": "День 9", "base_min": 6, "base_max": 12, "icon": "✨", "desc": "Девятый день."},
    10: {"name": "День 10 🎊", "base_min": 6, "base_max": 13, "icon": "🎯", "desc": "Юбилейный 10-й день!"},
    11: {"name": "День 11", "base_min": 7, "base_max": 14, "icon": "🔮", "desc": "Одиннадцатый день."},
    12: {"name": "День 12", "base_min": 7, "base_max": 15, "icon": "💎", "desc": "Двенадцатый день."},
    13: {"name": "День 13", "base_min": 8, "base_max": 16, "icon": "🌈", "desc": "Тринадцатый день."},
    14: {"name": "2 НЕДЕЛИ! 🏆", "base_min": 8, "base_max": 18, "icon": "👑", "desc": "Две недели!"},
    15: {"name": "День 15", "base_min": 9, "base_max": 19, "icon": "🎪", "desc": "Пятнадцатый день."},
    16: {"name": "День 16", "base_min": 9, "base_max": 20, "icon": "🎭", "desc": "Шестнадцатый день."},
    17: {"name": "День 17", "base_min": 10, "base_max": 21, "icon": "🎪", "desc": "Семнадцатый день."},
    18: {"name": "День 18", "base_min": 10, "base_max": 22, "icon": "🏰", "desc": "Восемнадцатый день."},
    19: {"name": "День 19", "base_min": 11, "base_max": 23, "icon": "🌋", "desc": "Девятнадцатый день."},
    20: {"name": "День 20 🎖️", "base_min": 11, "base_max": 25, "icon": "🏅", "desc": "Двадцатый день!"},
    21: {"name": "3 НЕДЕЛИ! 🌟", "base_min": 12, "base_max": 27, "icon": "💫", "desc": "Три недели!"},
    22: {"name": "День 22", "base_min": 13, "base_max": 28, "icon": "🎯", "desc": "Двадцать второй день."},
    23: {"name": "День 23", "base_min": 13, "base_max": 29, "icon": "🔱", "desc": "Двадцать третий день."},
    24: {"name": "День 24", "base_min": 14, "base_max": 30, "icon": "⚡", "desc": "Двадцать четвёртый день."},
    25: {"name": "День 25 🎂", "base_min": 14, "base_max": 32, "icon": "🎂", "desc": "Серебряный юбилей!"},
    26: {"name": "День 26", "base_min": 15, "base_max": 33, "icon": "🚀", "desc": "Двадцать шестой день."},
    27: {"name": "День 27", "base_min": 15, "base_max": 34, "icon": "🌌", "desc": "Двадцать седьмой день."},
    28: {"name": "4 НЕДЕЛИ! 🌍", "base_min": 16, "base_max": 36, "icon": "🌍", "desc": "Целый месяц!"},
    29: {"name": "День 29", "base_min": 17, "base_max": 38, "icon": "🔮", "desc": "Предпоследний день!"},
    30: {"name": "ДЕНЬ 30! 👑✨", "base_min": 18, "base_max": 40, "icon": "👑", "desc": "МЕГА-ДЕНЬ! + Premium ЛС 1 день!", "premium_bonus": True},
}

MAX_STREAK_DAY = 30

# ═══════════════════════════════════════════
# 📝 СИСТЕМА ПРЕСЕТОВ
# ═══════════════════════════════════════════

DEFAULT_PRESETS = {
    "programmer": {"id": "programmer", "name": "💻 Программист", "icon": "💻", "prompt": "Ты опытный программист. Отвечай технически точно, с примерами кода.", "category": "professional", "is_default": True},
    "copywriter": {"id": "copywriter", "name": "📝 Копирайтер", "icon": "📝", "prompt": "Ты профессиональный копирайтер. Пиши убедительные тексты.", "category": "professional", "is_default": True},
    "teacher": {"id": "teacher", "name": "📚 Учитель", "icon": "📚", "prompt": "Ты терпеливый учитель. Объясняй от простого к сложному.", "category": "education", "is_default": True},
    "psychologist": {"id": "psychologist", "name": "🧠 Психолог", "icon": "🧠", "prompt": "Ты дипломированный психолог. Проявляй эмпатию.", "category": "life", "is_default": True},
    "chef": {"id": "chef", "name": "👨‍🍳 Шеф-повар", "icon": "👨‍🍳", "prompt": "Ты шеф-повар. Давай подробные рецепты.", "category": "life", "is_default": True},
    "fitness": {"id": "fitness", "name": "💪 Фитнес-тренер", "icon": "💪", "prompt": "Ты фитнес-тренер. Составляй программы тренировок.", "category": "life", "is_default": True},
    "business": {"id": "business", "name": "💼 Бизнес-консультант", "icon": "💼", "prompt": "Ты бизнес-консультант. Анализируй рынки.", "category": "professional", "is_default": True},
    "creative": {"id": "creative", "name": "🎨 Креативщик", "icon": "🎨", "prompt": "Ты креативный директор. Генерируй идеи.", "category": "professional", "is_default": True},
}

def get_daily_bonus_info():
    text = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔥 ЕЖЕДНЕВНЫЕ НАГРАДЫ (СЕРИЯ ДО 30 ДНЕЙ)\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📐 КАК РАБОТАЕТ СИСТЕМА:\n"
        "• Заходите каждый день и забирайте бонус\n"
        "• Чем дольше серия — тем выше базовая награда\n"
        "• Размер награды зависит от дня серии и курса NBT\n"
        "• Формула: базовая награда дня × множитель курса\n\n"
        "⚠️ ВАЖНО: Не забрали до 00:00 МСК — серия СГОРИТ!\n"
        "👑 30-й день: Premium ЛС 1 день (единоразово)!\n\n"
        "📅 ВСЕ НАГРАДЫ ПО ДНЯМ (БАЗОВЫЕ):\n\n"
    )
    for day in range(1, 31):
        reward = STREAK_BASE_REWARDS[day]
        text += f"{reward['icon']} {reward['name']}: {reward['base_min']}-{reward['base_max']} 💮"
        if reward.get("premium_bonus"): text += " + 🎁 Premium 1 день!"
        text += f"\n   {reward['desc']}\n\n"
    text += "🎁 Кнопка «🔥 Награды» → «🎁 Забрать ежедневный бонус»\n"
    return text

def get_user_bonus(streak, rate=0.01):
    if streak >= MAX_STREAK_DAY:
        reward = STREAK_BASE_REWARDS[MAX_STREAK_DAY]; is_max = True
    elif streak >= 1:
        reward = STREAK_BASE_REWARDS.get(streak, STREAK_BASE_REWARDS[1]); is_max = False
    else:
        reward = STREAK_BASE_REWARDS[1]; is_max = False
    rate_multiplier = 1.0 + (rate * 10 - 0.1)
    rate_multiplier = max(0.5, min(1.5, rate_multiplier))
    base_bonus = random.randint(reward["base_min"], reward["base_max"])
    bonus = max(1, int(base_bonus * rate_multiplier))
    premium_bonus = reward.get("premium_bonus", False)
    if is_max and streak > MAX_STREAK_DAY: premium_bonus = False
    return bonus, reward["icon"], reward["name"], premium_bonus, rate_multiplier

STREAK_INFO = get_daily_bonus_info()

TRANSFER_TAX_BRACKETS = [
    {"min": 0, "max": 99, "tax_percent": 0, "name": "Без налога"},
    {"min": 100, "max": 249, "tax_percent": 3, "name": "Малый перевод"},
    {"min": 250, "max": 499, "tax_percent": 5, "name": "Средний перевод"},
    {"min": 500, "max": 999, "tax_percent": 8, "name": "Крупный перевод"},
    {"min": 1000, "max": 2499, "tax_percent": 12, "name": "Очень крупный перевод"},
    {"min": 2500, "max": 5000, "tax_percent": 15, "name": "Максимальный перевод"},
]

PREMIUM_TRANSFER_TAX_BRACKETS = [
    {"min": 0, "max": 499, "tax_percent": 0, "name": "Без налога"},
    {"min": 500, "max": 999, "tax_percent": 2, "name": "Льготный перевод"},
    {"min": 1000, "max": 4999, "tax_percent": 5, "name": "Средний перевод"},
    {"min": 5000, "max": 14999, "tax_percent": 8, "name": "Крупный перевод"},
    {"min": 15000, "max": 25000, "tax_percent": 10, "name": "Максимальный перевод"},
]

DAY_FACTORS = {
    0: {"name": "Понедельник", "factor": 1.05, "icon": "📈"},
    1: {"name": "Вторник", "factor": 1.02, "icon": "📊"},
    2: {"name": "Среда", "factor": 1.03, "icon": "📊"},
    3: {"name": "Четверг", "factor": 1.04, "icon": "📈"},
    4: {"name": "Пятница", "factor": 1.10, "icon": "🚀"},
    5: {"name": "Суббота", "factor": 0.95, "icon": "📉"},
    6: {"name": "Воскресенье", "factor": 0.95, "icon": "📉"},
}

BASE_PRICES_USD = {
    "extra5": 5, "extra10": 8, "extra50": 35,
    "unlimited_1h": 15, "unlimited_24h": 50, "unlimited_7d": 250,
    "image1": 8, "image5": 30, "image20": 100,
    "image_unlimited_1h": 25,
    "premium_day": 100, "premium_week": 500,
    "premium_30d": 1500, "premium_60d": 2500,
    "premium_90d": 3500, "premium_year": 10000,
    "premium_forever": 25000,
    "chat_extra10": 8, "chat_extra50": 30,
    "chat_unlimited_1h": 20, "chat_unlimited_24h": 75,
    "chat_image5": 25, "chat_image20": 90,
    "chat_premium_day": 150, "chat_premium_week": 750,
    "chat_premium_30d": 2500, "chat_premium_60d": 4000,
    "chat_premium_90d": 5500, "chat_premium_year": 15000,
    "chat_premium_forever": 35000,
}

AI_DISCLAIMER = "\n\n━━━━━━━━━━━━━━━━\n⚠️ NeBlock AI V2 • Только для справки"

CHANGELOG = """
📋 ЛОГ ОБНОВЛЕНИЙ NeBlock AI
━━━━━━━━━━━━━━━━━━━━

Версия 5.3 (22.07.2026) 💎
• 🔄 Продление Premium со скидкой 15%
• 🛒 Скидка 10% на чат-товары для Premium
• 📊 Обновлённая карточка Premium
• 📋 Расширенное сравнение Free vs Premium
• 💎 Улучшенная таблица преимуществ

Версия 5.2 (22.07.2026)
• Premium: кэшбек 15%, пассивный доход
• Premium: рефералы ×2, лимиты переводов
• Система пресетов

Версия 5.1 (22.07.2026)
• Улучшенные карточки товаров
• Скидки обновляются с курсом

Версия 5.0 (22.07.2026) 🔥
• Полная балансировка экономики
• Premium 30/60/90 дней и на год
"""

FAQ_TEXT = f"""
📚 ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ
━━━━━━━━━━━━━━━━━━━━

❓ Что даёт Premium? 💎
• Безлимит текста и фото в ЛС
• Кэшбек 15% с покупок
• Скидка 15% на продление Premium
• Скидка 10% на чат-товары
• Пассивный доход 2 💮/час
• Рефералы ×2 (35/12 💮)
• Кастомные пресеты
• Лимит перевода 25 000 💮
• Сниженные налоги на переводы
• Значок 💎 в профиле

❓ Как работает продление Premium?
Если у вас активен Premium, при покупке любого Premium-тарифа
вы получаете скидку 15%! Дни суммируются с текущим сроком.

❓ Как работают скидки для Premium?
• Продление Premium: -15%
• Чат-товары: -10%
• Кэшбек с любых покупок: 15%

❓ Лимиты?
• Free: {DAILY_LIMIT} текст + {IMAGE_DAILY_LIMIT} фото/день
• Premium: безлимит всего
• Free перевод: до {MAX_TRANSFER:,} 💮
• Premium перевод: до {PREMIUM_MAX_TRANSFER:,} 💮
"""

DONATE_INFO_TEXT = f"""
🌍 БЛАГОТВОРИТЕЛЬНОСТЬ
━━━━━━━━━━━━━━━━━━━━

🔥 Сжигание токенов NBT уменьшает предложение и повышает курс.
📊 Лимиты: Free до {MAX_DONATION:,} 💮 | Premium до {PREMIUM_MAX_DONATION:,} 💮
🏆 /donatetop — топ благотворителей
"""

TRANSFER_INFO = f"""
💸 ПЕРЕВОДЫ 💮 NBT
━━━━━━━━━━━━━━━━━━━━

📤 /transfer ID КОЛИЧЕСТВО | @username | ответ на сообщение
📊 FREE: {MAX_TRANSFER:,} 💮/раз | {DAILY_TRANSFER_LIMIT:,} 💮/день | налог 0-15%
💎 PREMIUM: {PREMIUM_MAX_TRANSFER:,} 💮/раз | {PREMIUM_DAILY_TRANSFER_LIMIT:,} 💮/день | налог 0-10%
"""

COMMANDS_LIST = """
📋 КОМАНДЫ NeBlock AI V5.3
━━━━━━━━━━━━━━━━━━━━

💬 /start | /faq | /commands | /changelog
🛒 /shop | /tokenrate | /discounts | /promo
🔥 /streak | /streak_info
💸 /transfer | /donate | /donatetop
🎨 /genimage
📝 /presets | /my_presets | /add_preset
👥 /chatowner | /chatshop
"""

DISCOUNT_TYPES = {
    "regular": {"name": "Обычная", "min": 5, "max": 25, "color": "🟢", "chance": 40, "icon": "🏷️"},
    "super": {"name": "Супер", "min": 30, "max": 50, "color": "🔴", "chance": 20, "icon": "🔥"},
    "flash": {"name": "Флеш", "min": 40, "max": 70, "color": "⚡", "chance": 8, "icon": "⏰"},
    "bundle": {"name": "Набор", "min": 15, "max": 35, "color": "📦", "chance": 12, "icon": "🎁"},
    "premium_discount": {"name": "Premium", "min": 10, "max": 30, "color": "👑", "chance": 5, "icon": "💎"},
    "legendary": {"name": "ЛЕГЕНДАРНАЯ", "min": 100, "max": 100, "color": "🌟", "chance": 0.5, "icon": "💫"},
}

SHOP_ITEMS_BASE = {
    "extra5": {"name": "+5 запросов", "price": 5, "icon": "📝", "category": "text", "desc": "5 дополнительных текстовых запросов.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "private", "type": "consumable", "duration": "до 00:00 МСК", "benefits": ["+5 текстовых запросов"]},
    "extra10": {"name": "+10 запросов", "price": 8, "icon": "📝", "category": "text", "desc": "10 дополнительных текстовых запросов.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "private", "type": "consumable", "duration": "до 00:00 МСК", "benefits": ["+10 текстовых запросов", "Выгоднее чем +5"]},
    "extra50": {"name": "+50 запросов", "price": 35, "icon": "📝", "category": "text", "desc": "50 дополнительных текстовых запросов. Экономия 30%!", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "private", "type": "consumable", "duration": "до 00:00 МСК", "benefits": ["+50 текстовых запросов", "Экономия 30%"]},
    "unlimited_1h": {"name": "Безлимит текста 1ч", "price": 15, "icon": "♾️", "category": "text", "desc": "Безлимитные текстовые запросы на 1 час.", "warning": "⚠️ 1 час с покупки.", "location": "private", "type": "unlimited", "duration": "1 час", "benefits": ["Безлимит текста"]},
    "unlimited_24h": {"name": "Безлимит текста 24ч", "price": 50, "icon": "♾️", "category": "text", "desc": "Безлимитные текстовые запросы на 24 часа.", "warning": "⚠️ 24 часа с покупки.", "location": "private", "type": "unlimited", "duration": "24 часа", "benefits": ["Безлимит текста на сутки", "Экономия 17%"]},
    "unlimited_7d": {"name": "Безлимит текста 7д", "price": 250, "icon": "♾️", "category": "text", "desc": "Безлимитные текстовые запросы на 7 дней.", "warning": "⚠️ 7 дней с покупки.", "location": "private", "type": "unlimited", "duration": "7 дней", "benefits": ["Безлимит текста на неделю", "Экономия 40%"]},
    "image1": {"name": "1 фото", "price": 8, "icon": "🎨", "category": "image", "desc": "1 генерация изображения. 1024×1024.", "warning": "⚠️ Сгорает в 00:00 МСК.", "location": "private", "type": "consumable", "duration": "до 00:00 МСК", "benefits": ["1 изображение", "1024×1024"]},
    "image5": {"name": "5 фото", "price": 30, "icon": "🎨", "category": "image", "desc": "5 генераций изображений. Экономия 25%!", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "private", "type": "consumable", "duration": "до 00:00 МСК", "benefits": ["5 изображений", "Экономия 25%"]},
    "image20": {"name": "20 фото", "price": 100, "icon": "🎨", "category": "image", "desc": "20 генераций изображений. Экономия 37%!", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "private", "type": "consumable", "duration": "до 00:00 МСК", "benefits": ["20 изображений", "Экономия 37%"]},
    "image_unlimited_1h": {"name": "Безлимит фото 1ч", "price": 25, "icon": "♾️", "category": "image", "desc": "Безлимитные генерации на 1 час.", "warning": "⚠️ 1 час с покупки.", "location": "private", "type": "unlimited", "duration": "1 час", "benefits": ["Безлимит генераций"]},
    "premium_day": {"name": "Premium 1 день", "price": 100, "icon": "⭐", "category": "premium", "desc": "Полный безлимит в ЛС на 24 часа + все Premium-привилегии.", "warning": "⚠️ 24 часа с покупки. Только ЛС.", "location": "private", "type": "premium", "duration": "1 день", "benefits": ["Безлимит текста и фото", "Кэшбек 15%", "Пассивный доход 2 💮/час", "Рефералы ×2", "Кастомные пресеты", "Лимит перевода 25 000 💮", "Скидка на продление 15%", "Скидка на чат-товары 10%"]},
    "premium_week": {"name": "Premium 7 дней", "price": 500, "icon": "⭐", "category": "premium", "desc": "Неделя безлимита и всех Premium-привилегий.", "warning": "⚠️ 7 дней с покупки. Только ЛС.", "location": "private", "type": "premium", "duration": "7 дней", "benefits": ["Всё из Premium 1 день", "Экономия 28% vs 7×1 день"]},
    "premium_30d": {"name": "Premium 30 дней 🔥", "price": 1500, "icon": "💎", "category": "premium", "desc": "Месяц безлимита и Premium-привилегий. Экономия 25%!", "warning": "⚠️ 30 дней с покупки. Только ЛС.", "location": "private", "type": "premium", "duration": "30 дней", "benefits": ["Всё из Premium 1 день", "Экономия 25% vs 30×1 день", "VIP-статус"]},
    "premium_60d": {"name": "Premium 60 дней 🚀", "price": 2500, "icon": "💎", "category": "premium", "desc": "2 месяца безлимита и Premium-привилегий. Экономия 37%!", "warning": "⚠️ 60 дней с покупки. Только ЛС.", "location": "private", "type": "premium", "duration": "60 дней", "benefits": ["Всё из Premium 1 день", "Экономия 37% vs 60×1 день", "VIP-статус"]},
    "premium_90d": {"name": "Premium 90 дней 👑", "price": 3500, "icon": "💎", "category": "premium", "desc": "3 месяца безлимита и Premium-привилегий. Экономия 50%!", "warning": "⚠️ 90 дней с покупки. Только ЛС.", "location": "private", "type": "premium", "duration": "90 дней", "benefits": ["Всё из Premium 1 день", "Экономия 50% vs 90×1 день", "VIP-статус"]},
    "premium_year": {"name": "Premium 1 год 💫", "price": 10000, "icon": "👑", "category": "premium", "desc": "Год безлимита и Premium-привилегий. Экономия 72%!", "warning": "⚠️ 365 дней с покупки. Только ЛС.", "location": "private", "type": "premium", "duration": "1 год", "benefits": ["Всё из Premium 1 день", "Экономия 72% vs 365×1 день", "VIP-статус"]},
    "premium_forever": {"name": "Premium НАВСЕГДА ✨", "price": 25000, "icon": "🌟", "category": "premium", "desc": "Пожизненный безлимит и Premium-привилегии. Максимальная выгода!", "warning": "⚠️ Только ЛС.", "location": "private", "type": "premium", "duration": "Навсегда", "benefits": ["Всё из Premium 1 день", "Пожизненный доступ", "Максимальная экономия", "Легендарный значок"]},
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("NeBlockAI")

client = openai.OpenAI(
    api_key=YANDEX_API_KEY, base_url="https://ai.api.cloud.yandex.net/v1",
    project=YANDEX_FOLDER, timeout=60.0,
)

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f: return json.load(f)
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
def load_presets(): 
    data = load_json(PRESETS_FILE)
    if not data: data = {"user_presets": {}, "initialized": True}; save_json(PRESETS_FILE, data)
    return data
def save_presets(data): save_json(PRESETS_FILE, data)

def get_donation_stats():
    donations = load_donations()
    total = sum(d.get("amount", 0) for d in donations.get("donations", []))
    count = len(donations.get("donations", []))
    users = {}
    for d in donations.get("donations", []):
        uid = str(d.get("user_id", ""))
        users[uid] = users.get(uid, 0) + d.get("amount", 0)
    top_donors = sorted(users.items(), key=lambda x: x[1], reverse=True)[:10]
    return total, count, top_donors

def get_day_factor():
    today = datetime.now().weekday()
    day_info = DAY_FACTORS.get(today, {"factor": 1.0, "name": "Неизвестно", "icon": "❓"})
    return day_info["factor"], day_info["name"], day_info["icon"]

def get_current_rate_block():
    now = datetime.now(); hour = now.hour; block_hour = (hour // 4) * 4
    return f"{now.strftime('%Y-%m-%d')}-{block_hour:02d}", block_hour

def get_next_rate_update():
    now = datetime.now(); hour = now.hour; block_hour = (hour // 4) * 4
    next_block = block_hour + 4
    if next_block >= 24: return (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return now.replace(hour=next_block, minute=0, second=0, microsecond=0)

def get_transfer_tax(amount, is_premium_user=False):
    brackets = PREMIUM_TRANSFER_TAX_BRACKETS if is_premium_user else TRANSFER_TAX_BRACKETS
    for bracket in brackets:
        if bracket["min"] <= amount <= bracket["max"]:
            return int(amount * bracket["tax_percent"] / 100), bracket["tax_percent"], bracket["name"]
    return 0, 0, "Без налога"

def log_transfer(from_id, to_id, amount, tax, final_amount, chat_type="private", chat_id=None):
    log = load_json(TRANSFER_LOG_FILE)
    if "transfers" not in log: log["transfers"] = []
    log["transfers"].append({"date": datetime.now().strftime("%Y-%m-%d"), "timestamp": datetime.now().isoformat(), "from_id": from_id, "to_id": to_id, "amount": amount, "tax": tax, "final_amount": final_amount, "chat_type": chat_type, "chat_id": str(chat_id) if chat_id else None})
    if len(log["transfers"]) > 1000: log["transfers"] = log["transfers"][-1000:]
    save_json(TRANSFER_LOG_FILE, log)

def log_donation(user_id, amount):
    donations = load_donations()
    if "donations" not in donations: donations["donations"] = []
    donations["donations"].append({"date": datetime.now().strftime("%Y-%m-%d"), "timestamp": datetime.now().isoformat(), "user_id": user_id, "amount": amount})
    if len(donations["donations"]) > 1000: donations["donations"] = donations["donations"][-1000:]
    save_donations(donations)

def get_token_rate():
    rate_data = load_json(TOKEN_RATE_FILE); history = load_json(TOKEN_HISTORY_FILE)
    now = datetime.now(); current_block, block_hour = get_current_rate_block()
    last_update = rate_data.get("rate_block", "")
    if last_update != current_block:
        users = load_users()
        total_tokens = sum(u.get("tokens", 0) for u in users.values())
        total_earned = sum(u.get("earned_tokens", 0) for u in users.values())
        total_spent = sum(u.get("spent_tokens", 0) for u in users.values())
        donated_total, _, _ = get_donation_stats()
        total_burned = total_spent + donated_total
        active_users = sum(1 for u in users.values() if u.get("requests_today", 0) > 0)
        total_users = len(users)
        base_rate = 0.005
        ideal_supply = 5000
        supply_factor = (ideal_supply / max(total_tokens, 1)) ** 0.6 if total_tokens > 0 else 1.0
        supply_factor = max(0.1, min(50.0, supply_factor))
        activity_factor = 0.5 + ((active_users / max(total_users, 1)) * 1.5) if total_users > 0 else 1.0
        total_supply = total_earned + donated_total
        burn_factor = 0.7 + ((total_burned / max(total_supply, 1)) * 3.0) if total_supply > 0 else 1.0
        day_factor, day_name, day_icon = get_day_factor()
        volatility = 1.0
        if history:
            rates = [h.get("rate", base_rate) for h in history.values() if h.get("rate")]
            if len(rates) > 1:
                avg_rate = sum(rates) / len(rates)
                std_dev = math.sqrt(sum((r - avg_rate) ** 2 for r in rates) / len(rates))
                volatility = 1.0 + (std_dev / max(avg_rate, 0.0001)) * 0.8
                volatility = max(0.5, min(3.0, volatility))
        market_noise = random.uniform(0.92, 1.08)
        rate = base_rate * supply_factor * activity_factor * burn_factor * day_factor * volatility * market_noise
        rate = max(0.00001, rate)
        market_cap = round(total_tokens * rate, 2)
        yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_rate = history.get(yesterday, {}).get("rate", rate)
        change_24h = round(((rate - yesterday_rate) / max(yesterday_rate, 0.0001)) * 100, 2)
        trend = "📈" if change_24h > 0.5 else "📉" if change_24h < -0.5 else "📊"
        next_update = get_next_rate_update()
        rate_data = {"rate_block": current_block, "block_hour": block_hour, "date": now.strftime("%Y-%m-%d"), "rate": rate, "total_supply": total_tokens, "total_burned": total_burned, "total_donated": donated_total, "day_factor": day_factor, "day_name": day_name, "day_icon": day_icon, "supply_factor": round(supply_factor, 4), "activity_factor": round(activity_factor, 4), "burn_factor": round(burn_factor, 4), "volatility_index": round(volatility, 4), "market_cap": market_cap, "change_24h": change_24h, "trend": trend, "next_update": next_update.strftime("%H:%M МСК"), "updated_at": now.isoformat()}
        save_json(TOKEN_RATE_FILE, rate_data)
        today = now.strftime("%Y-%m-%d")
        history[today] = {"rate": rate, "supply": total_tokens, "market_cap": market_cap}
        if len(history) > 30: history = dict(sorted(history.items())[-30:])
        save_json(TOKEN_HISTORY_FILE, history)
        logger.info(f"💮 Курс: ${rate:.8f} | Блок: {block_hour}:00 | {day_name} {day_icon}")
    return rate_data

def get_item_price(item_id, user_id=None):
    rate_data = get_token_rate()
    base_price = max(1, int(BASE_PRICES_USD.get(item_id, 10) / 100 / rate_data.get("rate", 0.005)))
    
    # Применяем Premium-скидки
    if user_id and is_premium(user_id):
        item = SHOP_ITEMS_BASE.get(item_id, {})
        # Скидка 15% на продление Premium
        if item.get("category") == "premium" and item.get("location") == "private":
            base_price = max(1, int(base_price * 0.85))
        # Скидка 10% на чат-товары
        elif item.get("location") == "chat":
            base_price = max(1, int(base_price * 0.90))
    
    return base_price

def get_shop_items(user_id=None):
    return {item_id: {**item, "price": get_item_price(item_id, user_id)} for item_id, item in SHOP_ITEMS_BASE.items()}

def generate_discounts():
    all_items = list(SHOP_ITEMS_BASE.keys())
    discounts = {"generated_at": datetime.now().isoformat()}
    used_items = set()
    if random.uniform(0, 100) < DISCOUNT_TYPES["legendary"]["chance"]:
        item_id = random.choice(all_items)
        discounts[item_id] = {"percent": 100, "type": "legendary", "type_name": "ЛЕГЕНДАРНАЯ", "color": "🌟", "icon": "💫", "expires": (datetime.now() + timedelta(hours=3)).isoformat(), "special": True}
        used_items.add(item_id)
    available_types = [d for d, c in DISCOUNT_TYPES.items() if d != "legendary" and random.randint(1, 100) <= c["chance"]] or ["regular"]
    for _ in range(random.randint(3, 5)):
        if len(used_items) >= len(all_items): break
        disc_type = random.choice(available_types)
        dconfig = DISCOUNT_TYPES[disc_type]
        available = [i for i in all_items if i not in used_items]
        if not available: break
        item_id = random.choice(available)
        used_items.add(item_id)
        percent = random.randint(dconfig["min"], dconfig["max"])
        expires = (datetime.now() + timedelta(hours=24)).isoformat() if disc_type == "flash" else None
        discounts[item_id] = {"percent": percent, "type": disc_type, "type_name": dconfig["name"], "color": dconfig["color"], "icon": dconfig["icon"], "expires": expires}
    return discounts

def get_discounts():
    discounts = load_discounts()
    last_update = discounts.get("last_update", "")
    now = datetime.now()
    if discounts:
        to_delete = [i for i, d in discounts.items() if i not in ["last_update", "generated_at"] and d.get("expires") and now > datetime.fromisoformat(d["expires"])]
        for i in to_delete: del discounts[i]
        if to_delete: save_discounts(discounts)
    if last_update:
        last_date = datetime.fromisoformat(last_update)
        if now >= last_date.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=2):
            new_d = generate_discounts(); new_d["last_update"] = now.strftime("%Y-%m-%d"); save_discounts(new_d); return new_d
    else:
        new_d = generate_discounts(); new_d["last_update"] = now.strftime("%Y-%m-%d"); save_discounts(new_d); return new_d
    if not discounts or "last_update" not in discounts:
        discounts = generate_discounts(); discounts["last_update"] = now.strftime("%Y-%m-%d"); save_discounts(discounts)
    return discounts

def get_next_update_time():
    now = datetime.now()
    last_update = load_discounts().get("last_update", "")
    if last_update: return datetime.fromisoformat(last_update).replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=2)
    n = now.replace(hour=9, minute=0, second=0, microsecond=0)
    return n if now < n else n + timedelta(days=2)

def get_discounted_price(item_id, user_id=None):
    discounts = get_discounts()
    shop_items = get_shop_items(user_id)
    if item_id not in shop_items: return 0, 0, None
    current_price = shop_items[item_id]["price"]
    if item_id in discounts and item_id not in ["last_update", "generated_at"]:
        d = discounts[item_id]
        if not d.get("expires") or datetime.now() <= datetime.fromisoformat(d["expires"]):
            percent = d["percent"]
            new_price = max(1, int(current_price * (1 - percent / 100)))
            return new_price, percent, d
    return current_price, 0, None

def get_user(user_id):
    users = load_users(); uid = str(user_id)
    defaults = {
        "joined": datetime.now().isoformat(), "username": None,
        "requests_today": 0, "extra_requests": 0, "image_requests_today": 0, "extra_image_requests": 0,
        "chat_requests_today": 0, "extra_chat_requests": 0, "chat_image_requests_today": 0, "extra_chat_image_requests": 0,
        "unlimited_until": None, "image_unlimited_until": None, "chat_unlimited_until": None, "chat_image_unlimited_until": None,
        "premium_until": None, "chat_premium_until": None,
        "last_request": None, "total_requests": 0, "total_images": 0,
        "reset_date": datetime.now().strftime("%Y-%m-%d"),
        "tokens": START_BONUS, "daily_bonus_claimed": None, "daily_bonus_streak": 0, "last_bonus_date": None,
        "streak_30_premium_claimed": False,
        "referral_code": "".join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(8)),
        "referred_by": None, "referrals": 0, "earned_tokens": 0, "spent_tokens": 0,
        "donated_tokens": 0, "cashback_earned": 0,
        "used_promos": [], "waiting_for_image": False, "current_model": "text",
        "active_preset": None, "custom_presets": {},
        "warnings": 0, "muted_until": None, "banned": False,
        "daily_transfer_total": 0, "transfer_reset_date": datetime.now().strftime("%Y-%m-%d"),
        "last_passive_income": None,
    }
    if uid not in users: users[uid] = defaults.copy(); save_users(users)
    else:
        for k, v in defaults.items():
            if k not in users[uid]: users[uid][k] = v
        save_users(users)
    today = datetime.now().strftime("%Y-%m-%d")
    if users[uid].get("reset_date") != today:
        for f in ["requests_today", "extra_requests", "image_requests_today", "extra_image_requests", "chat_requests_today", "extra_chat_requests", "chat_image_requests_today", "extra_chat_image_requests"]:
            users[uid][f] = 0
        users[uid]["reset_date"] = today; save_users(users)
    if users[uid].get("transfer_reset_date") != today:
        users[uid]["daily_transfer_total"] = 0
        users[uid]["transfer_reset_date"] = today; save_users(users)
    return users[uid]

def process_passive_income(user_id):
    users = load_users(); uid = str(user_id)
    if uid not in users: return 0
    user = users[uid]
    if not is_premium(user_id): return 0
    now = datetime.now()
    last_income = user.get("last_passive_income")
    if last_income:
        last_time = datetime.fromisoformat(last_income)
        hours_passed = min((now - last_time).total_seconds() / 3600, PASSIVE_INCOME_MAX_HOURS)
        income = int(hours_passed * PASSIVE_INCOME_HOURLY)
    else:
        income = PASSIVE_INCOME_HOURLY
    if income > 0:
        users[uid]["tokens"] = users[uid].get("tokens", 0) + income
        users[uid]["earned_tokens"] = users[uid].get("earned_tokens", 0) + income
        users[uid]["last_passive_income"] = now.isoformat()
        save_users(users)
    return income

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
        users[uid]["total_requests"] = users[uid].get("total_requests", 0) + 1
        users[uid]["last_request"] = datetime.now().isoformat(); save_users(users)

def add_image_request(user_id, chat_type="private"):
    users = load_users(); uid = str(user_id)
    if uid in users:
        if chat_type in ["group", "supergroup"]: users[uid]["chat_image_requests_today"] = users[uid].get("chat_image_requests_today", 0) + 1
        else: users[uid]["image_requests_today"] = users[uid].get("image_requests_today", 0) + 1
        users[uid]["total_images"] = users[uid].get("total_images", 0) + 1
        users[uid]["last_request"] = datetime.now().isoformat(); save_users(users)

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
    users[uid]["tokens"] = users[uid].get("tokens", 0) + amount
    users[uid]["earned_tokens"] = users[uid].get("earned_tokens", 0) + amount; save_users(users)

def remove_tokens(user_id, amount):
    users = load_users()
    if str(user_id) in users:
        users[str(user_id)]["tokens"] = users[str(user_id)].get("tokens", 0) - amount
        users[str(user_id)]["spent_tokens"] = users[str(user_id)].get("spent_tokens", 0) + amount; save_users(users)

def process_cashback(user_id, amount):
    if is_premium(user_id):
        cashback = int(amount * CASHBACK_PERCENT / 100)
        if cashback > 0:
            users = load_users(); uid = str(user_id)
            if uid in users:
                users[uid]["tokens"] = users[uid].get("tokens", 0) + cashback
                users[uid]["earned_tokens"] = users[uid].get("earned_tokens", 0) + cashback
                users[uid]["cashback_earned"] = users[uid].get("cashback_earned", 0) + cashback
                save_users(users)
            return cashback
    return 0

def donate_tokens(user_id, amount):
    users = load_users(); uid = str(user_id)
    premium = is_premium(user_id)
    max_donation = PREMIUM_MAX_DONATION if premium else MAX_DONATION
    if amount > max_donation: return False
    if uid in users:
        users[uid]["tokens"] = users[uid].get("tokens", 0) - amount
        users[uid]["spent_tokens"] = users[uid].get("spent_tokens", 0) + amount
        users[uid]["donated_tokens"] = users[uid].get("donated_tokens", 0) + amount
        save_users(users); log_donation(user_id, amount)
        return True
    return False

def get_tokens(user_id): return get_user(user_id).get("tokens", 0)

def create_promo(code, amount, max_uses=0):
    promos = load_promos(); promos[code.upper()] = {"amount": amount, "max_uses": max_uses, "used_by": [], "created": datetime.now().isoformat()}
    save_promos(promos)

def use_promo(user_id, code):
    promos = load_promos(); code = code.upper()
    if code not in promos: return False, "Промокод не найден"
    p = promos[code]
    if p["max_uses"] > 0 and len(p["used_by"]) >= p["max_uses"]: return False, "Лимит"
    if str(user_id) in p["used_by"]: return False, "Уже использован"
    add_tokens(user_id, p["amount"]); p["used_by"].append(str(user_id)); save_promos(promos)
    return True, p["amount"]

def moderate_content(text):
    for pat in COMPILED_SEVERE:
        if pat.search(text): return False, "severe", "Запрещённый контент"
    for pat in COMPILED_BLOCKED:
        if pat.search(text): return False, "normal", "Запрещённый контент"
    return True, None, None

COMPILED_BLOCKED = [re.compile(w, re.IGNORECASE) for w in [r'\b(?:взлом|хак(?:ер|нуть)?|hack|crack|warez|кряк|keygen)\b', r'\b(?:наркотик|drugs|наркота|спайс|героин|кокаин)\b', r'\b(?:оружие|weapon|gun|бомба|bomb|взрывчатка|пистолет|автомат)\b', r'\b(?:дет[иь] порно|child porn|педофил|pedo|инцест)\b', r'\b(?:уби[йт]|убью|kill|murder|зака[зж]|hitman|киллер)\b', r'\b(?:террор|terror|теракт|ИГИЛ|ISIS|джихад)\b', r'\b(?:суицид|suicide|самоубий|повес[иь])\b']]
COMPILED_SEVERE = [re.compile(w, re.IGNORECASE) for w in [r'\b(?:дет[иь] порно|child porn|педофил|pedo|террор|terror|ИГИЛ|ISIS|уби[йт]|kill|суицид|suicide)\b']]

def is_user_muted(user_id):
    u = get_user(user_id)
    if u.get("banned"): return True
    m = u.get("muted_until")
    return m and datetime.now() < datetime.fromisoformat(m) if m else False

def warn_user(user_id, severity="normal"):
    users = load_users(); uid = str(user_id)
    if severity == "severe":
        users[uid]["banned"] = True; users[uid]["muted_until"] = (datetime.now() + timedelta(days=7)).isoformat()
        save_users(users); return True, "Заблокирован на 7 дней"
    users[uid]["warnings"] = users[uid].get("warnings", 0) + 1
    if users[uid]["warnings"] >= 5:
        users[uid]["banned"] = True; users[uid]["muted_until"] = (datetime.now() + timedelta(days=3)).isoformat()
        save_users(users); return True, "Заблокирован на 3 дня"
    elif users[uid]["warnings"] >= 3:
        users[uid]["muted_until"] = (datetime.now() + timedelta(hours=6)).isoformat()
        save_users(users); return True, "Заблокирован на 6 часов"
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
        [KeyboardButton("📝 Пресеты")]
    ], resize_keyboard=True)

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("ℹ️ О боте", callback_data="about"), InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🧠 Модели", callback_data="models"), InlineKeyboardButton("💎 Premium", callback_data="premium_info")],
        [InlineKeyboardButton("🔥 Награды", callback_data="earn"), InlineKeyboardButton("💮 Курс NBT", callback_data="tokenrate")],
        [InlineKeyboardButton("💸 Перевод", callback_data="transfer"), InlineKeyboardButton("🌍 Донат", callback_data="donate_info")],
        [InlineKeyboardButton("📝 Пресеты", callback_data="presets_menu")],
    ])

def back_button(): return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="menu")]])

def shop_keyboard(location="private", user_id=None):
    keyboard = []
    discounts = get_discounts()
    shop_items = get_shop_items(user_id)
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
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 Забрать ежедневный бонус", callback_data="daily_bonus")],
        [InlineKeyboardButton("👥 Реферальная ссылка", callback_data="ref_link")],
        [InlineKeyboardButton("📅 Подробно о наградах", callback_data="streak_info")],
        [InlineKeyboardButton("🔙 Назад", callback_data="menu")],
    ])

def limit_reached_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Купить запросы", callback_data="shop"), InlineKeyboardButton("🔥 Награды", callback_data="earn")],
        [InlineKeyboardButton("💎 Premium", callback_data="premium_info")]
    ])

def presets_keyboard():
    keyboard = []
    for preset_id, preset in DEFAULT_PRESETS.items():
        keyboard.append([InlineKeyboardButton(f"{preset['icon']} {preset['name']}", callback_data=f"preset_{preset_id}")])
    keyboard.append([InlineKeyboardButton("❌ Отключить пресет", callback_data="preset_off")])
    keyboard.append([InlineKeyboardButton("➕ Создать свой (Premium)", callback_data="preset_create")])
    keyboard.append([InlineKeyboardButton("📋 Мои пресеты", callback_data="preset_my")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="menu")])
    return InlineKeyboardMarkup(keyboard)

# ═══════════════════════════════════════════
# ОБРАБОТЧИКИ КОМАНД
# ═══════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id; user = get_user(user_id); chat_type = update.effective_chat.type
    username = update.effective_user.username
    if username:
        users = load_users(); uid = str(user_id)
        if uid in users: users[uid]["username"] = username; save_users(users)
    passive_income = process_passive_income(user_id)
    if context.args and context.args[0].startswith("ref_"):
        ref_code = context.args[0].replace("ref_", ""); users = load_users(); uid = str(user_id)
        for u_id, u_data in users.items():
            if u_data.get("referral_code") == ref_code and u_id != uid and not users[uid].get("referred_by"):
                users[uid]["referred_by"] = u_id
                referrer_bonus = PREMIUM_REFERRAL_BONUS if is_premium(int(u_id)) else REFERRAL_BONUS
                invited_bonus = PREMIUM_INVITED_BONUS if is_premium(int(u_id)) else INVITED_BONUS
                add_tokens(int(u_id), referrer_bonus); add_tokens(user_id, invited_bonus)
                users[u_id]["referrals"] = users[u_id].get("referrals", 0) + 1; save_users(users)
                try: await context.bot.send_message(int(u_id), f"🎉 Реферал!\n💰 +{referrer_bonus} 💮")
                except: pass
                break
    if chat_type in ["group", "supergroup"]:
        await update.message.reply_text(f"🧠 NeBlock AI V{BOT_VERSION} в чате!\n\n💬 @{context.bot.username} вопрос\n🎨 /genimage | 💸 /transfer | 🔥 /streak")
        return
    premium = "💎 Активен" if is_premium(user_id) else "Не активен"
    rate_data = get_token_rate(); rate = rate_data.get("rate", 0.005)
    day_icon = rate_data.get("day_icon", "📊"); day_name = rate_data.get("day_name", "")
    next_update = rate_data.get("next_update", "")
    streak = user.get("daily_bonus_streak", 0)
    donated_total, _, _ = get_donation_stats()
    passive_text = f"\n💤 Пассивный доход: +{passive_income} 💮" if passive_income > 0 else ""
    await update.message.reply_text(
        f"🧠 NeBlock AI V{BOT_VERSION}\n━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💬 Текст | 🎨 Фото | 💸 Переводы | 🌍 Донаты\n━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💎 Premium: {premium}\n"
        f"💰 Баланс: {user.get('tokens', 0):,} 💮 (~${user.get('tokens', 0) * rate:.2f})\n"
        f"💮 Курс NBT: 1 NBT = ${rate:.8f}\n"
        f"📅 {day_icon} {day_name} | 🕐 Обновление: {next_update}\n"
        f"🔥 Серия бонусов: {streak} дн. | Сожжено: {donated_total:,} 💮\n"
        f"📊 Лимиты: {DAILY_LIMIT} текст + {IMAGE_DAILY_LIMIT} фото/день{passive_text}\n\n👇 Выберите модель:",
        reply_markup=main_reply_keyboard()
    )

async def streak_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id; user = get_user(user_id)
    streak = user.get("daily_bonus_streak", 0)
    rate_data = get_token_rate(); rate = rate_data.get("rate", 0.005)
    text = f"🔥 ВАША СЕРИЯ: {streak} дн.\n━━━━━━━━━━━━━━━━\n\n"
    if streak == 0: text += "🌱 Вы ещё не начали серию!\nНачните сегодня!\n\n"
    elif streak >= MAX_STREAK_DAY: text += f"👑 Максимальная серия ({MAX_STREAK_DAY} дней)!\n⚠️ Забирайте бонус каждый день!\n\n"
    else:
        next_day = streak + 1
        if next_day <= MAX_STREAK_DAY:
            next_reward = STREAK_BASE_REWARDS[next_day]
            rate_multiplier = 1.0 + (rate * 10 - 0.1); rate_multiplier = max(0.5, min(1.5, rate_multiplier))
            est_min = max(1, int(next_reward["base_min"] * rate_multiplier))
            est_max = max(1, int(next_reward["base_max"] * rate_multiplier))
            text += f"➡️ Завтра день {next_day}: {next_reward['icon']} {next_reward['name']}\n   База: {next_reward['base_min']}-{next_reward['base_max']} 💮\n   С курсом: ~{est_min}-{est_max} 💮\n\n"
    text += f"📐 Формула: база × множитель курса | Курс: ${rate:.8f}\n⚠️ Не забрали до 00:00 МСК — серия СГОРИТ!\n📋 /streak_info — все 30 дней"
    await update.message.reply_text(text)

async def streak_info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(STREAK_INFO) > 4000:
        await update.message.reply_text(STREAK_INFO[:4000])
        await update.message.reply_text(STREAK_INFO[4000:])
    else: await update.message.reply_text(STREAK_INFO)

async def tokenrate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rate_data = get_token_rate(); history = load_json(TOKEN_HISTORY_FILE)
    rate = rate_data.get("rate", 0.005); supply = rate_data.get("total_supply", 0)
    market_cap = rate_data.get("market_cap", 0); donated = rate_data.get("total_donated", 0)
    burned = rate_data.get("total_burned", 0)
    day_icon = rate_data.get("day_icon", "📊"); day_name = rate_data.get("day_name", "")
    updated = rate_data.get("updated_at", "")
    updated_time = datetime.fromisoformat(updated).strftime("%d.%m.%Y %H:%M") if updated else "Нет"
    change_24h = rate_data.get("change_24h", 0); trend = rate_data.get("trend", "📊")
    text = f"💮 КУРС NBT\n━━━━━━━━━━━━━━━━\n\n💰 1 NBT = ${rate:.8f}\n💎 Кап: ${market_cap:,.2f}\n{trend} 24ч: {change_24h:+.2f}%\n━━━━━━━━━━━━━━━━\n🪙 В обороте: {supply:,} NBT\n🔥 Сожжено: {burned:,} 💮\n📅 {day_icon} {day_name} | 🕐 {updated_time}\n\n📈 История за 7 дней:\n"
    for date, h in sorted(history.items())[-7:]: text += f"• {date}: ${h.get('rate', 0):.8f}\n"
    await update.message.reply_text(text)

async def donate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id; premium = is_premium(user_id)
    max_don = PREMIUM_MAX_DONATION if premium else MAX_DONATION
    if not context.args:
        await update.message.reply_text(f"{DONATE_INFO_TEXT}\n\nЛимит: до {max_don:,} 💮\n/donate СУММА"); return
    try: amount = int(context.args[0])
    except: await update.message.reply_text("❌ /donate СУММА"); return
    if amount < MIN_DONATION or amount > max_don: await update.message.reply_text(f"❌ Лимит: {MIN_DONATION} – {max_don:,} 💮"); return
    user = get_user(user_id)
    if user.get("tokens", 0) < amount: await update.message.reply_text("❌ Недостаточно!"); return
    await update.message.reply_text(f"🌍 ПОДТВЕРЖДЕНИЕ ДОНАТА\n━━━━━━━━━━━━━━━━\n\n💰 Сумма: {amount:,} 💮\n🔥 Токены сгорят НАВСЕГДА\n💎 Баланс: {user.get('tokens', 0):,} → {user.get('tokens', 0) - amount:,} 💮\n\nПодтвердите:", reply_markup=donate_confirm_keyboard(amount))

async def donatetop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total, count, top_donors = get_donation_stats()
    if not top_donors: await update.message.reply_text("🌍 ТОП БЛАГОТВОРИТЕЛЕЙ\n\nПока никто не делал донатов.\n/donate СУММА"); return
    text = f"🌍 ТОП БЛАГОТВОРИТЕЛЕЙ\n━━━━━━━━━━━━━━━━\n\n🔥 Сожжено: {total:,} 💮 | Донатов: {count}\n\n🏆 ТОП-10:\n"
    users = load_users(); medals = ["🥇", "🥈", "🥉"]
    for i, (uid, donated) in enumerate(top_donors):
        name = f"@{users.get(uid, {}).get('username', 'Неизвестный')}" if uid in users else f"ID:{uid}"
        medal = medals[i] if i < 3 else f"{i+1}."
        text += f"{medal} {name}: {donated:,} 💮\n"
    await update.message.reply_text(text)

async def donate_info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(DONATE_INFO_TEXT)

async def genimage_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id; chat_type = update.effective_chat.type; chat_id = update.effective_chat.id if chat_type != "private" else None
    if not context.args: await update.message.reply_text("🎨 NeBlock Images V2\n/genimage ОПИСАНИЕ"); return
    text = " ".join(context.args)
    if not can_image_request(user_id, chat_type, chat_id): await update.message.reply_text("🚫 Лимит генераций!\n💡 /shop или 💎 Premium"); return
    msg = await update.message.reply_text("🎨 Генерирую...")
    try:
        image_bytes, error = await generate_image(text)
        if image_bytes: add_image_request(user_id, chat_type); await msg.delete(); await update.message.reply_photo(photo=image_bytes, caption=f"🎨 NeBlock Images V2\n📝 {text[:200]}")
        else: await msg.edit_text("❌ Ошибка")
    except:
        try: await msg.delete()
        except: pass
        await update.message.reply_text("❌ Ошибка")

async def transfer_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id; chat_type = update.effective_chat.type; to_id = None; amount = None
    premium = is_premium(user_id)
    max_transfer = PREMIUM_MAX_TRANSFER if premium else MAX_TRANSFER
    daily_limit = PREMIUM_DAILY_TRANSFER_LIMIT if premium else DAILY_TRANSFER_LIMIT
    if chat_type in ["group", "supergroup"]:
        if update.message.reply_to_message:
            to_id = update.message.reply_to_message.from_user.id
            if context.args and len(context.args) >= 1:
                try: amount = int(context.args[0])
                except: return
        elif context.args and len(context.args) >= 2 and context.args[0].startswith("@"):
            username = context.args[0].replace("@", "")
            try: amount = int(context.args[1])
            except: return
            users = load_users()
            for uid, data in users.items():
                if data.get("username", "").lower() == username.lower(): to_id = int(uid); break
            if not to_id: await update.message.reply_text(f"❌ @{username} не найден"); return
        else: return
    else:
        if not context.args or len(context.args) < 2: await update.message.reply_text(f"{TRANSFER_INFO}\n\n/transfer ID КОЛИЧЕСТВО"); return
        try: to_id = int(context.args[0]); amount = int(context.args[1])
        except: return
    if not to_id or not amount: return
    if amount < MIN_TRANSFER or amount > max_transfer: await update.message.reply_text(f"❌ Лимит: {MIN_TRANSFER} – {max_transfer:,} 💮"); return
    if to_id == user_id: await update.message.reply_text("❌ Нельзя себе!"); return
    sender = get_user(user_id)
    if sender.get("daily_transfer_total", 0) + amount > daily_limit: await update.message.reply_text(f"❌ Дневной лимит: {daily_limit:,} 💮"); return
    if sender.get("tokens", 0) < amount: await update.message.reply_text("❌ Недостаточно!"); return
    tax, tax_percent, tax_name = get_transfer_tax(amount, premium)
    receiver = get_user(to_id)
    if not receiver: await update.message.reply_text("❌ Не найден!"); return
    final_amount = amount - tax
    receiver_name = receiver.get("username") or f"ID:{to_id}"
    tax_info = f"Налог: {tax} 💮 ({tax_percent}%)" if tax > 0 else "Без налога"
    await update.message.reply_text(f"⚠️ ПРОВЕРЬТЕ ПЕРЕВОД\n━━━━━━━━━━━━━━━━\n\n👤 @{receiver_name} | 🆔 {to_id}\n💸 {amount:,} 💮 | 📊 {tax_info}\n💰 Получит: {final_amount:,} 💮\n\nПодтвердите:", reply_markup=transfer_confirm_keyboard(to_id, amount))

async def transfer_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["waiting_transfer"] = True
    await update.message.reply_text(f"{TRANSFER_INFO}\n\nОтправьте: ID КОЛИЧЕСТВО")

async def transfer_info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(TRANSFER_INFO)

async def discounts_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    discounts = get_discounts(); active = {k: v for k, v in discounts.items() if k not in ["last_update", "generated_at"]}
    shop_items = get_shop_items()
    text = f"🎫 СКИДКИ\n━━━━━━━━━━━━━━━━\n\n🔄 {get_next_update_time().strftime('%d.%m.%Y 9:00 МСК')}\n\n"
    if not active: text += "Нет активных скидок."
    else:
        for item_id, disc in sorted(active.items(), key=lambda x: x[1]["percent"], reverse=True):
            item = shop_items.get(item_id)
            if item:
                current_price = item["price"]
                discounted_price = max(1, int(current_price * (1 - disc["percent"] / 100)))
                text += f"{disc.get('color', '🟢')} {item['icon']} {item['name']}\n   -{disc['percent']}% = {discounted_price} 💮 (было {current_price})\n\n"
    await update.message.reply_text(text)

async def promo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["waiting_promo"] = True
    await update.message.reply_text("🎟 Отправьте промокод.")

async def changelog_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text(CHANGELOG)
async def commands_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text(COMMANDS_LIST)
async def shopdesc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("📋 /shop — магазин")

async def presets_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    active = user.get("active_preset")
    text = "📝 ПРЕСЕТЫ (РОЛИ ИИ)\n━━━━━━━━━━━━━━━━\n\n"
    if active:
        preset = DEFAULT_PRESETS.get(active) or user.get("custom_presets", {}).get(active)
        if preset: text += f"🎯 Активный: {preset['icon']} {preset['name']}\n\n"
    text += "Выберите роль для ИИ:"
    await update.message.reply_text(text, reply_markup=presets_keyboard())

async def my_presets_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id; user = get_user(user_id)
    custom = user.get("custom_presets", {})
    if not custom:
        await update.message.reply_text("📝 МОИ ПРЕСЕТЫ\n━━━━━━━━━━━━━━━━\n\nУ вас пока нет своих пресетов.\n💎 Premium пользователи могут создавать кастомные пресеты!\nИспользуйте /add_preset для создания."); return
    text = "📝 МОИ ПРЕСЕТЫ\n━━━━━━━━━━━━━━━━\n\n"
    for pid, preset in custom.items(): text += f"{preset.get('icon', '📝')} {preset['name']}\n   {preset['prompt'][:100]}...\n\n"
    await update.message.reply_text(text)

async def add_preset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_premium(user_id): await update.message.reply_text("❌ Создание кастомных пресетов доступно только Premium пользователям!\n💎 /shop — купить Premium"); return
    if not context.args or len(context.args) < 2: await update.message.reply_text("📝 СОЗДАНИЕ ПРЕСЕТА\n━━━━━━━━━━━━━━━━\n\nФормат: /add_preset НАЗВАНИЕ | ТЕКСТ_РОЛИ\n\nПример:\n/add_preset Юрист | Ты опытный юрист. Отвечай ссылаясь на законы..."); return
    args_text = " ".join(context.args)
    if "|" not in args_text: await update.message.reply_text("❌ Используйте | для разделения названия и текста роли"); return
    parts = args_text.split("|", 1)
    name = parts[0].strip()[:30]
    prompt = parts[1].strip()
    preset_id = f"custom_{user_id}_{int(datetime.now().timestamp())}"
    users = load_users(); uid = str(user_id)
    if "custom_presets" not in users[uid]: users[uid]["custom_presets"] = {}
    users[uid]["custom_presets"][preset_id] = {"id": preset_id, "name": name, "icon": "✏️", "prompt": prompt, "category": "custom", "is_default": False}
    save_users(users)
    await update.message.reply_text(f"✅ Пресет «{name}» создан!\nИспользуйте /presets для выбора.")

async def chatowner_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]: return
    chat_id = update.effective_chat.id; user_id = update.effective_user.id; add_chat_owner(chat_id, user_id)
    chats = load_chats(); c = chats.get(str(chat_id), {})
    owners = c.get("owners", []) if isinstance(c, dict) else c
    text = "👑 ВЛАДЕЛЬЦЫ ЧАТА\n\n"
    for i, oid in enumerate(owners, 1): text += f"{i}. ID: {oid}\n"
    await update.message.reply_text(text)

async def chatshop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]: return
    chat_id = update.effective_chat.id; user_id = update.effective_user.id; add_chat_owner(chat_id, user_id)
    if not is_chat_owner(chat_id, user_id): return
    await update.message.reply_text(f"🛒 МАГАЗИН ЧАТА\n💰 {get_tokens(user_id)} 💮", reply_markup=shop_keyboard("chat", user_id))

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
        users = load_users(); users[uid]["tokens"] = users[uid].get("tokens", 0) - amount
        users[uid]["spent_tokens"] = users[uid].get("spent_tokens", 0) + amount; save_users(users)
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
        text += f"{i}. {name} — {data.get('tokens', 0):,} 💮\n"
    await update.message.reply_text(text)

async def admin_cleardiscounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    save_discounts({"last_update": datetime.now().strftime("%Y-%m-%d")})

async def admin_create_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args or len(context.args) < 2: return
    create_promo(context.args[0].upper(), int(context.args[1]), int(context.args[2]) if len(context.args) > 2 else 0)

async def admin_promos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    promos = load_promos()
    if not promos: return
    text = "🎟 ПРОМОКОДЫ:\n\n"
    for code, data in promos.items(): text += f"{code}: {data['amount']} 💮\n"
    await update.message.reply_text(text)

async def admin_delete_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args: return
    promos = load_promos(); code = context.args[0].upper()
    if code in promos: del promos[code]; save_promos(promos)

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
    new_rate = get_token_rate()
    await update.message.reply_text(f"💮 Курс: ${new_rate.get('rate', 0.005):.8f}")

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args: return
    text = " ".join(context.args); users = load_users(); sent = 0
    for uid in users:
        try: await context.bot.send_message(int(uid), f"📢 {text}"); sent += 1; await asyncio.sleep(0.05)
        except: pass
    await update.message.reply_text(f"✅ Отправлено: {sent}")

async def reply_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text; user_id = update.effective_user.id
    username = update.effective_user.username
    if username:
        users = load_users(); uid = str(user_id)
        if uid in users: users[uid]["username"] = username; save_users(users)
    
    if text == "💬 NeBlock AI V2":
        users = load_users(); users[str(user_id)]["current_model"] = "text"; users[str(user_id)]["waiting_for_image"] = False; save_users(users)
        await update.message.reply_text(f"💬 NeBlock AI V2\n━━━━━━━━━━━━━━━━\n📊 Осталось: {remaining(user_id)}\n📝 Отправьте вопрос.")
        return True
    if text == "🎨 NeBlock Images V2":
        users = load_users(); users[str(user_id)]["current_model"] = "image"; users[str(user_id)]["waiting_for_image"] = True; save_users(users)
        await update.message.reply_text(f"🎨 NeBlock Images V2\n━━━━━━━━━━━━━━━━\n📊 Осталось: {image_remaining(user_id)}\n📝 Опишите изображение.")
        return True
    if text == "👤 Профиль":
        u = get_user(user_id); joined = datetime.fromisoformat(u.get("joined", "")).strftime("%d.%m.%Y")
        last = "Никогда"
        if u.get("last_request"): last = datetime.fromisoformat(u["last_request"]).strftime("%d.%m.%Y в %H:%M")
        cm = "💬 NeBlock AI V2" if u.get("current_model") == "text" else "🎨 NeBlock Images V2"
        premium = "💎 Активен" if is_premium(user_id) else "Не активен"
        premium_icon = " 💎" if is_premium(user_id) else ""
        rate_data = get_token_rate(); rate = rate_data.get("rate", 0.005); usd = u.get("tokens", 0) * rate
        streak = u.get("daily_bonus_streak", 0)
        active_preset = u.get("active_preset")
        preset_name = "Нет"
        if active_preset:
            preset = DEFAULT_PRESETS.get(active_preset) or u.get("custom_presets", {}).get(active_preset)
            if preset: preset_name = f"{preset['icon']} {preset['name']}"
        def fmt(x):
            if not x: return "Не активен"
            try:
                if datetime.now() < datetime.fromisoformat(x):
                    d = datetime.fromisoformat(x) - datetime.now(); days, hours = d.days, d.seconds // 3600
                    return f"Активен ({days}д {hours}ч)" if days > 0 else f"Активен ({hours}ч)"
            except: pass
            return "Не активен"
        premium_info = ""
        if is_premium(user_id):
            premium_info = (
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"💎 PREMIUM ПРИВИЛЕГИИ:\n"
                f"🔄 Кэшбек: {CASHBACK_PERCENT}% (получено: {u.get('cashback_earned', 0):,} 💮)\n"
                f"💤 Пассивный доход: {PASSIVE_INCOME_HOURLY} 💮/час\n"
                f"🔄 Продление Premium: -{PREMIUM_RENEWAL_DISCOUNT}%\n"
                f"🛒 Чат-товары: -{PREMIUM_CHAT_DISCOUNT}%\n"
                f"👥 Рефералы: {PREMIUM_REFERRAL_BONUS}/{PREMIUM_INVITED_BONUS} 💮\n"
                f"💸 Лимит перевода: {PREMIUM_MAX_TRANSFER:,} 💮\n"
                f"📝 Кастомные пресеты: ✅\n"
            )
        await update.message.reply_text(
            f"👤 ПРОФИЛЬ{premium_icon}\n━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🆔 {user_id} | 📅 {joined}\n🔮 {cm} | 💎 {premium}\n📝 Пресет: {preset_name}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💰 Баланс: {u.get('tokens', 0):,} 💮 (~${usd:.2f})\n💮 Курс: 1 NBT = ${rate:.8f}\n🔥 Серия: {streak} дн.\n"
            f"💎 Заработано: {u.get('earned_tokens', 0):,} | Потрачено: {u.get('spent_tokens', 0):,}\n🌍 Донатов: {u.get('donated_tokens', 0):,} 💮\n"
            f"{premium_info}"
            f"━━━━━━━━━━━━━━━━━━━━\n\n📊 СЕГОДНЯ:\n"
            f"💬 Текст: {u.get('requests_today', 0)}/{DAILY_LIMIT + u.get('extra_requests', 0)} | {fmt(u.get('unlimited_until'))}\n"
            f"🎨 Фото: {u.get('image_requests_today', 0)}/{IMAGE_DAILY_LIMIT + u.get('extra_image_requests', 0)} | {fmt(u.get('image_unlimited_until'))}\n"
            f"👥 Чаты: {u.get('chat_requests_today', 0)}/{CHAT_DAILY_LIMIT + u.get('extra_chat_requests', 0)}\n"
            f"💸 Переводов: {u.get('daily_transfer_total', 0)} 💮\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n📈 ВСЕГО: 💬{u.get('total_requests', 0):,} | 🎨{u.get('total_images', 0):,}\n"
            f"🛡 {u.get('warnings', 0)}/5 | 👥 {u.get('referrals', 0)} | 🕐 {last}",
            reply_markup=main_menu()
        )
        return True
    if text == "🛒 Магазин": 
        await update.message.reply_text(f"🛒 МАГАЗИН\n━━━━━━━━━━━━━━━━\n💰 {get_tokens(user_id)} 💮\n\nВыберите категорию:", reply_markup=shop_keyboard("private", user_id))
        return True
    if text == "🔥 Награды": 
        user = get_user(user_id); streak = user.get("daily_bonus_streak", 0)
        await update.message.reply_text(f"🔥 НАГРАДЫ\n━━━━━━━━━━━━━━━━\n\n📊 Серия: {streak} дн.\n💰 Баланс: {get_tokens(user_id)} 💮\n\nВыберите действие:", reply_markup=earn_keyboard())
        return True
    if text == "📝 Пресеты": await presets_cmd(update, context); return True
    if text == "💸 Перевод": await transfer_button_handler(update, context); return True
    if text == "🌍 Донат": await donate_info_cmd(update, context); return True
    if text == "🎟 Промокод": await promo_cmd(update, context); return True
    if text == "📚 FAQ": 
        await update.message.reply_text(FAQ_TEXT[:4000])
        if len(FAQ_TEXT) > 4000: await update.message.reply_text(FAQ_TEXT[4000:])
        return True
    if text == "🎫 Скидки": await discounts_cmd(update, context); return True
    if text == "💮 Курс NBT": await tokenrate_cmd(update, context); return True
    return False

async def inline_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer(); user_id = query.from_user.id; data = query.data
    shop_items = get_shop_items(user_id)
    
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
            sender = get_user(user_id); premium = is_premium(user_id)
            if sender.get("tokens", 0) < amount: await query.edit_message_text("❌ Недостаточно!"); return
            tax, tax_percent, _ = get_transfer_tax(amount, premium)
            receiver = get_user(to_id)
            if not receiver: await query.edit_message_text("❌ Не найден!"); return
            final_amount = amount - tax
            users = load_users()
            uid_from = str(user_id); uid_to = str(to_id)
            users[uid_from]["tokens"] = users[uid_from].get("tokens", 0) - amount
            users[uid_from]["spent_tokens"] = users[uid_from].get("spent_tokens", 0) + amount
            users[uid_from]["daily_transfer_total"] = users[uid_from].get("daily_transfer_total", 0) + amount
            users[uid_to]["tokens"] = users[uid_to].get("tokens", 0) + final_amount
            users[uid_to]["earned_tokens"] = users[uid_to].get("earned_tokens", 0) + final_amount
            save_users(users); log_transfer(user_id, to_id, amount, tax, final_amount)
            tax_info = f"\n📊 Налог: {tax} 💮 ({tax_percent}%)" if tax > 0 else ""
            await query.edit_message_text(f"✅ ПЕРЕВОД!\n👤 ID {to_id}\n💸 {amount:,} 💮\n💰 Зачислено: {final_amount:,} 💮{tax_info}\n💎 Баланс: {get_tokens(user_id):,} 💮")
        return
    
    if data == "presets_menu": await presets_cmd(update, context)
    
    if data.startswith("preset_"):
        preset_id = data.replace("preset_", "")
        if preset_id == "off":
            users = load_users(); uid = str(user_id)
            users[uid]["active_preset"] = None; save_users(users)
            await query.edit_message_text("✅ Пресет отключён.", reply_markup=back_button())
            return
        if preset_id == "create":
            if not is_premium(user_id): await query.edit_message_text("❌ Только для Premium!\n💎 /shop\n\nИспользуйте /add_preset", reply_markup=back_button()); return
            await query.edit_message_text("📝 Используйте команду:\n/add_preset НАЗВАНИЕ | ТЕКСТ_РОЛИ\n\nПример:\n/add_preset Юрист | Ты опытный юрист...", reply_markup=back_button())
            return
        if preset_id == "my":
            user = get_user(user_id); custom = user.get("custom_presets", {})
            if not custom: await query.edit_message_text("У вас пока нет своих пресетов.", reply_markup=back_button()); return
            text = "📝 МОИ ПРЕСЕТЫ\n━━━━━━━━━━━━━━━━\n\n"
            for pid, preset in custom.items(): text += f"{preset.get('icon', '✏️')} {preset['name']}\n   {preset['prompt'][:80]}...\n\n"
            await query.edit_message_text(text, reply_markup=back_button())
            return
        preset = DEFAULT_PRESETS.get(preset_id) or get_user(user_id).get("custom_presets", {}).get(preset_id)
        if preset:
            users = load_users(); uid = str(user_id)
            users[uid]["active_preset"] = preset_id; save_users(users)
            await query.edit_message_text(f"✅ {preset['icon']} {preset['name']}\n📝 {preset['prompt'][:200]}...\n\nИИ будет отвечать в этой роли.", reply_markup=back_button())
        return
    
    if data == "streak_info":
        user = get_user(user_id); streak = user.get("daily_bonus_streak", 0)
        rate_data = get_token_rate(); rate = rate_data.get("rate", 0.005)
        text = f"📅 ПОДРОБНО О НАГРАДАХ\n━━━━━━━━━━━━━━━━\n\n📊 Серия: {streak} дн. | 💮 Курс: ${rate:.8f}\n\n📐 Формула: база дня × множитель курса\n⚠️ Не забрали до 00:00 МСК — серия СГОРИТ!\n👑 30-й день: Premium ЛС 1 день\n\n📅 ВСЕ 30 ДНЕЙ (БАЗА):\n\n"
        for day in range(1, 31):
            reward = STREAK_BASE_REWARDS[day]
            text += f"{reward['icon']} {reward['name']}: {reward['base_min']}-{reward['base_max']} 💮"
            if reward.get("premium_bonus"): text += " + 🎁 Premium"
            text += f"\n   {reward['desc']}\n\n"
        if len(text) > 4000:
            await query.edit_message_text(text[:4000], reply_markup=back_button())
            await context.bot.send_message(chat_id=query.message.chat_id, text=text[4000:], reply_markup=back_button())
        else: await query.edit_message_text(text, reply_markup=back_button())
        return
    
    if data == "menu": await query.edit_message_text(f"🧠 NeBlock AI V{BOT_VERSION}\n━━━━━━━━━━━━━━━━\n\n💰 {get_tokens(user_id):,} 💮\n\nВыберите раздел:", reply_markup=main_menu()); return
    if data == "about": await query.edit_message_text(f"ℹ️ О БОТЕ\n━━━━━━━━━━━━━━━━\n\n📌 Версия: {BOT_VERSION}\n\n💬 NeBlock AI V2 — текст\n🎨 NeBlock Images V2 — фото\n💎 Premium — безлимит + привилегии\n\n📊 Лимиты Free: {DAILY_LIMIT} текст + {IMAGE_DAILY_LIMIT} фото/день", reply_markup=back_button()); return
    if data == "donate_info": await query.edit_message_text(DONATE_INFO_TEXT, reply_markup=back_button()); return
    if data == "models": await query.edit_message_text("🧠 МОДЕЛИ\n━━━━━━━━━━━━━━━━\n\n💬 NeBlock AI V2 — текст\n🎨 NeBlock Images V2 — фото\n📝 /genimage — генерация", reply_markup=back_button()); return
    if data == "tokenrate":
        rd = get_token_rate()
        await query.edit_message_text(f"💮 КУРС NBT\n━━━━━━━━━━━━━━━━\n\n💰 1 NBT = ${rd.get('rate', 0.005):.8f}\n💎 Кап: ${rd.get('market_cap', 0):,.2f}\n🪙 В обороте: {rd.get('total_supply', 0):,} NBT\n🔥 Сожжено: {rd.get('total_donated', 0):,} 💮\n{rd.get('day_icon', '📊')} {rd.get('day_name', '')}", reply_markup=back_button()); return
    if data == "transfer": 
        context.user_data["waiting_transfer"] = True
        await query.edit_message_text(f"{TRANSFER_INFO}\n\nОтправьте: ID КОЛИЧЕСТВО", reply_markup=back_button()); return
    if data == "commands": await query.edit_message_text(COMMANDS_LIST, reply_markup=back_button()); return
    if data == "changelog": await query.edit_message_text(CHANGELOG, reply_markup=back_button()); return
    if data == "discounts_info":
        discounts = get_discounts(); active = {k: v for k, v in discounts.items() if k not in ["last_update", "generated_at"]}
        text = "🎫 СКИДКИ\n\n"
        if not active: text += "Нет активных."
        else:
            for item_id, disc in sorted(active.items(), key=lambda x: x[1]["percent"], reverse=True):
                item = shop_items.get(item_id)
                if item:
                    current_price = item["price"]
                    discounted_price = max(1, int(current_price * (1 - disc["percent"] / 100)))
                    text += f"{disc.get('color', '🟢')} {item['icon']} {item['name']}\n   -{disc['percent']}% = {discounted_price} 💮\n\n"
        await query.edit_message_text(text, reply_markup=back_button()); return
    
    if data == "premium_info":
        premium_user = is_premium(user_id)
        renewal_info = ""
        if premium_user:
            user = get_user(user_id)
            prem_until = user.get("premium_until")
            if prem_until:
                remaining = datetime.fromisoformat(prem_until) - datetime.now()
                days_left = max(0, remaining.days)
                renewal_info = (
                    f"\n\n🔄 ПРОДЛЕНИЕ PREMIUM:\n"
                    f"• Ваш Premium активен ещё {days_left} дн.\n"
                    f"• При покупке любого тарифа — скидка {PREMIUM_RENEWAL_DISCOUNT}%!\n"
                    f"• Дни суммируются с текущим сроком\n"
                    f"• Цены ниже уже включают вашу скидку"
                )
        
        comparison = (
            f"💎 NeBlock Premium\n━━━━━━━━━━━━━━━━\n\n"
            f"📊 СРАВНЕНИЕ FREE vs PREMIUM:\n\n"
            f"┌─────────────────────┬──────────┬──────────┐\n"
            f"│ Возможность         │   FREE   │ PREMIUM  │\n"
            f"├─────────────────────┼──────────┼──────────┤\n"
            f"│ Текст (ЛС)          │  {DAILY_LIMIT}/день   │ Безлимит │\n"
            f"│ Фото (ЛС)           │  {IMAGE_DAILY_LIMIT}/день   │ Безлимит │\n"
            f"│ Кэшбек с покупок    │    0%    │   {CASHBACK_PERCENT}%   │\n"
            f"│ Скидка на продление │    -     │   {PREMIUM_RENEWAL_DISCOUNT}%    │\n"
            f"│ Скидка на чат-товары│    -     │   {PREMIUM_CHAT_DISCOUNT}%    │\n"
            f"│ Пассивный доход     │    ❌    │ {PASSIVE_INCOME_HOURLY} 💮/час  │\n"
            f"│ Рефералы            │ {REFERRAL_BONUS}/{INVITED_BONUS} 💮  │ {PREMIUM_REFERRAL_BONUS}/{PREMIUM_INVITED_BONUS} 💮 │\n"
            f"│ Макс. перевод       │ {MAX_TRANSFER:,} 💮 │ {PREMIUM_MAX_TRANSFER:,} 💮│\n"
            f"│ Налог на перевод    │  0-15%   │  0-10%   │\n"
            f"│ Макс. донат         │ {MAX_DONATION:,} 💮│{PREMIUM_MAX_DONATION:,} 💮│\n"
            f"│ Пресеты             │ 8 готовых│ +свои    │\n"
            f"│ Значок в профиле    │    ❌    │    💎    │\n"
            f"└─────────────────────┴──────────┴──────────┘\n"
            f"{renewal_info}\n\n"
            f"🛒 ТАРИФЫ (с учётом ваших скидок):\n"
            f"⭐ 1 день — {shop_items.get('premium_day', {}).get('price', '?')} 💮\n"
            f"⭐ 7 дней — {shop_items.get('premium_week', {}).get('price', '?')} 💮\n"
            f"💎 30 дней — {shop_items.get('premium_30d', {}).get('price', '?')} 💮 (-25%)\n"
            f"🚀 60 дней — {shop_items.get('premium_60d', {}).get('price', '?')} 💮 (-37%)\n"
            f"👑 90 дней — {shop_items.get('premium_90d', {}).get('price', '?')} 💮 (-50%)\n"
            f"💫 1 год — {shop_items.get('premium_year', {}).get('price', '?')} 💮 (-72%)\n"
            f"🌟 Навсегда — {shop_items.get('premium_forever', {}).get('price', '?')} 💮\n\n"
            f"💡 30-й день серии даёт Premium 1 день!\n"
            f"🔄 Premium пользователи получают скидку {PREMIUM_RENEWAL_DISCOUNT}% на продление!\n"
            f"🛒 Premium пользователи получают скидку {PREMIUM_CHAT_DISCOUNT}% на чат-товары!"
        )
        await query.edit_message_text(comparison, reply_markup=back_button())
        return
    
    if data == "stats":
        u = get_user(user_id); premium = is_premium(user_id)
        await query.edit_message_text(
            f"📊 СТАТИСТИКА\n━━━━━━━━━━━━━━━━\n\n"
            f"💬 Запросов: {u.get('requests_today', 0)}\n"
            f"🎨 Генераций: {u.get('image_requests_today', 0)}\n"
            f"💰 Баланс: {u.get('tokens', 0):,} 💮\n"
            f"🔥 Серия: {u.get('daily_bonus_streak', 0)} дн.\n"
            f"🌍 Донатов: {u.get('donated_tokens', 0):,} 💮\n"
            f"👥 Рефералов: {u.get('referrals', 0)}\n"
            + (f"🔄 Кэшбек: {u.get('cashback_earned', 0):,} 💮\n" if premium else ""),
            reply_markup=back_button()
        )
        return
    
    if data == "shop": 
        await query.edit_message_text(f"🛒 МАГАЗИН\n━━━━━━━━━━━━━━━━\n💰 {get_tokens(user_id):,} 💮\n\nВыберите категорию:", reply_markup=shop_keyboard("private", user_id))
        return
    
    if data == "earn": 
        user = get_user(user_id); streak = user.get("daily_bonus_streak", 0)
        await query.edit_message_text(f"🔥 НАГРАДЫ\n━━━━━━━━━━━━━━━━\n\n📊 Серия: {streak} дн.\n💰 Баланс: {get_tokens(user_id):,} 💮\n\nВыберите действие:", reply_markup=earn_keyboard())
        return
    
    if data == "promo": 
        context.user_data["waiting_promo"] = True
        await query.edit_message_text("🎟 Отправьте промокод.", reply_markup=back_button())
        return
    
    if data == "faq": await query.edit_message_text(FAQ_TEXT[:4000], reply_markup=back_button()); return
    
    if data == "daily_bonus":
        u = get_user(user_id); today = datetime.now().strftime("%Y-%m-%d")
        if u.get("daily_bonus_claimed") == today: await query.answer("❌ Уже забирали сегодня!", show_alert=True)
        else:
            users = load_users(); uid = str(user_id)
            users[uid]["daily_bonus_claimed"] = today
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            if users[uid].get("last_bonus_date") == yesterday: users[uid]["daily_bonus_streak"] = users[uid].get("daily_bonus_streak", 0) + 1
            elif users[uid].get("last_bonus_date") != today: users[uid]["daily_bonus_streak"] = 1
            users[uid]["last_bonus_date"] = today; streak = users[uid]["daily_bonus_streak"]
            rate_data = get_token_rate(); rate = rate_data.get("rate", 0.005)
            bonus, icon, day_name, premium_bonus, rate_multiplier = get_user_bonus(streak, rate)
            if premium_bonus and users[uid].get("streak_30_premium_claimed"): premium_bonus = False
            save_users(users); add_tokens(user_id, bonus)
            premium_text = ""
            if premium_bonus and not users[uid].get("streak_30_premium_claimed"):
                users = load_users()
                existing = users[uid].get("premium_until")
                base = datetime.fromisoformat(existing) if existing and datetime.now() < datetime.fromisoformat(existing) else datetime.now()
                users[uid]["premium_until"] = (base + timedelta(hours=24)).isoformat()
                users[uid]["streak_30_premium_claimed"] = True; save_users(users)
                premium_text = "\n🎁 + Premium ЛС 1 день!"
            await query.answer(f"🎉 +{bonus} 💮!", show_alert=True)
            await query.edit_message_text(f"🎁 БОНУС ПОЛУЧЕН!\n━━━━━━━━━━━━━━━━\n\n{icon} {day_name}\n💰 +{bonus} 💮{premium_text}\n💎 Баланс: {get_tokens(user_id):,} 💮\n🔥 Серия: {streak} дн.\n\n⚠️ Заберите завтра до 00:00 МСК!", reply_markup=back_button())
        return
    
    if data == "ref_link":
        user = get_user(user_id); bot_username = (await context.bot.get_me()).username
        bonus_you = PREMIUM_REFERRAL_BONUS if is_premium(user_id) else REFERRAL_BONUS
        bonus_friend = PREMIUM_INVITED_BONUS if is_premium(user_id) else INVITED_BONUS
        await query.edit_message_text(f"👥 РЕФЕРАЛЫ\n━━━━━━━━━━━━━━━━\n\n🔗 https://t.me/{bot_username}?start=ref_{user.get('referral_code', '')}\n\n💰 Вы: +{bonus_you} 💮 | Друг: +{bonus_friend} 💮\n📊 Рефералов: {user.get('referrals', 0)}\n" + ("💎 Premium бонусы!" if is_premium(user_id) else "\n💡 С Premium: +35/+12 💮"), reply_markup=back_button())
        return
    
    if data.startswith("confirm_"):
        item_id = data.replace("confirm_", ""); item = shop_items.get(item_id)
        if not item: return
        price, percent, disc = get_discounted_price(item_id, user_id)
        tokens = get_tokens(user_id)
        if tokens < price: await query.answer("❌ Недостаточно!", show_alert=True); return
        remove_tokens(user_id, price)
        cashback = process_cashback(user_id, price)
        users = load_users(); uid = str(user_id)
        
        actions = {"extra5": ("extra_requests", 5), "extra10": ("extra_requests", 10), "extra50": ("extra_requests", 50), "image1": ("extra_image_requests", 1), "image5": ("extra_image_requests", 5), "image20": ("extra_image_requests", 20), "chat_extra10": ("extra_chat_requests", 10), "chat_extra50": ("extra_chat_requests", 50), "chat_image5": ("extra_chat_image_requests", 5), "chat_image20": ("extra_chat_image_requests", 20)}
        time_actions = {"unlimited_1h": ("unlimited_until", 1), "unlimited_24h": ("unlimited_until", 24), "unlimited_7d": ("unlimited_until", 168), "image_unlimited_1h": ("image_unlimited_until", 1), "chat_unlimited_1h": ("chat_unlimited_until", 1), "chat_unlimited_24h": ("chat_unlimited_until", 24)}
        premium_actions = {"premium_day": 1, "premium_week": 7, "premium_30d": 30, "premium_60d": 60, "premium_90d": 90, "premium_year": 365, "premium_forever": 36500, "chat_premium_day": 1, "chat_premium_week": 7, "chat_premium_30d": 30, "chat_premium_60d": 60, "chat_premium_90d": 90, "chat_premium_year": 365, "chat_premium_forever": 36500}
        
        if item_id in actions:
            field, amount = actions[item_id]; users[uid][field] = users[uid].get(field, 0) + amount
        elif item_id in time_actions:
            field, hours = time_actions[item_id]; users[uid][field] = (datetime.now() + timedelta(hours=hours)).isoformat()
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
        
        dt = f"\n🎫 Скидка {percent}%" if percent > 0 else ""
        if disc and disc.get("type") == "legendary": dt = "\n🌟 ЛЕГЕНДАРНАЯ СКИДКА!"
        cashback_text = f"\n🔄 Кэшбек: +{cashback} 💮" if cashback > 0 else ""
        premium_info = ""
        if is_premium(user_id) and item_id.startswith("premium_"):
            premium_info = f"\n🔄 Продление Premium (скидка {PREMIUM_RENEWAL_DISCOUNT}%)"
        elif is_premium(user_id) and item.get("location") == "chat":
            premium_info = f"\n🛒 Premium скидка на чат: {PREMIUM_CHAT_DISCOUNT}%"
        
        await query.answer(f"✅ {item['name']}!", show_alert=True)
        await query.edit_message_text(
            f"✅ ПОКУПКА!\n━━━━━━━━━━━━━━━━\n\n"
            f"{item['icon']} {item['name']}\n{dt}{premium_info}{cashback_text}\n"
            f"💰 Потрачено: {price} 💮\n💎 Остаток: {get_tokens(user_id):,} 💮\n"
            f"⏱ {item.get('duration', 'Н/Д')}",
            reply_markup=back_button()
        )
        return
    
    if data.startswith("buy_"):
        item_id = data.replace("buy_", ""); item = shop_items.get(item_id)
        if not item: return
        price, percent, disc = get_discounted_price(item_id, user_id)
        tokens = get_tokens(user_id); can = "✅ Хватает" if tokens >= price else "❌ Не хватает"
        premium = is_premium(user_id)
        
        # Информация о скидках Premium
        discount_info = ""
        if premium:
            if item.get("category") == "premium" and item.get("location") == "private":
                discount_info = f"\n💎 Ваша скидка на продление: {PREMIUM_RENEWAL_DISCOUNT}%"
            elif item.get("location") == "chat":
                discount_info = f"\n💎 Ваша скидка на чат-товары: {PREMIUM_CHAT_DISCOUNT}%"
        
        cashback_info = ""
        if premium:
            cb = int(price * CASHBACK_PERCENT / 100)
            cashback_info = f"\n🔄 Кэшбек: +{cb} 💮"
        
        benefits_text = "\n".join([f"  ✓ {b}" for b in item.get("benefits", [])])
        
        dt = ""
        original_price = item["price"]
        if percent > 0 and disc:
            if disc.get("type") == "legendary": dt = "\n\n🌟 ЛЕГЕНДАРНАЯ СКИДКА 100%!\n💰 Цена: 0 💮 (БЕСПЛАТНО!)"
            else: dt = f"\n\n{disc.get('color', '🟢')} СКИДКА {disc.get('icon', '🏷️')} {percent}%\n💵 Обычная: {original_price} 💮\n🔥 Со скидкой: {price} 💮\n💰 Экономия: {original_price - price} 💮"
        else: dt = f"\n\n💵 Цена: {price} 💮"
        
        premium_comparison = ""
        if item_id.startswith("premium_"):
            premium_comparison = (
                f"\n\n📊 ЧТО ВЫ ПОЛУЧАЕТЕ:\n"
                f"┌─────────────────────┬──────────┬──────────┐\n"
                f"│ Возможность         │   FREE   │ PREMIUM  │\n"
                f"├─────────────────────┼──────────┼──────────┤\n"
                f"│ Текст (ЛС)          │  {DAILY_LIMIT}/день   │ Безлимит │\n"
                f"│ Фото (ЛС)           │  {IMAGE_DAILY_LIMIT}/день   │ Безлимит │\n"
                f"│ Кэшбек с покупок    │    0%    │   {CASHBACK_PERCENT}%   │\n"
                f"│ Скидка на продление │    -     │   {PREMIUM_RENEWAL_DISCOUNT}%    │\n"
                f"│ Скидка на чат       │    -     │   {PREMIUM_CHAT_DISCOUNT}%    │\n"
                f"│ Пассивный доход     │    ❌    │ {PASSIVE_INCOME_HOURLY} 💮/час  │\n"
                f"│ Рефералы            │ {REFERRAL_BONUS}/{INVITED_BONUS} 💮  │ {PREMIUM_REFERRAL_BONUS}/{PREMIUM_INVITED_BONUS} 💮 │\n"
                f"│ Переводы            │ до {MAX_TRANSFER:,} │ до {PREMIUM_MAX_TRANSFER:,} │\n"
                f"│ Налог на перевод    │  0-15%   │  0-10%   │\n"
                f"│ Пресеты             │ 8 готовых│ +свои    │\n"
                f"│ Значок              │    ❌    │    💎    │\n"
                f"└─────────────────────┴──────────┴──────────┘"
            )
        
        text = (
            f"🛒 {item['icon']} {item['name']}\n━━━━━━━━━━━━━━━━\n\n"
            f"📝 {item['desc']}\n\n"
            f"✨ ПРЕИМУЩЕСТВА:\n{benefits_text}\n"
            f"{dt}{discount_info}{cashback_info}{premium_comparison}\n\n"
            f"⏱ Длительность: {item.get('duration', 'Н/Д')}\n"
            f"📦 Тип: {item.get('type', 'Н/Д')}\n"
            f"⚠️ {item.get('warning', '')}\n\n"
            f"💎 Ваш баланс: {tokens:,} 💮\n{can}"
        )
        
        await query.edit_message_text(text, reply_markup=confirm_keyboard(item_id))
        return

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤔 Неизвестная команда.\n/start | /commands")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip() if update.message.text else ""
    user_id = update.effective_user.id; chat_type = update.effective_chat.type; chat_id = update.effective_chat.id
    bot_username = context.bot.username
    
    username = update.effective_user.username
    if username:
        users = load_users(); uid = str(user_id)
        if uid in users: users[uid]["username"] = username; save_users(users)
    
    if is_user_muted(user_id): await update.message.reply_text("🚫 Заблокированы."); return
    is_clean, severity, reason = moderate_content(text)
    if not is_clean: muted, warn = warn_user(user_id, severity); await update.message.reply_text(f"⚠️ {reason}\n{warn}"); return
    
    if context.user_data.get("waiting_transfer"):
        context.user_data["waiting_transfer"] = False
        parts = text.split()
        if len(parts) >= 2:
            try:
                to_id = int(parts[0]); amount = int(parts[1])
                context.args = [str(to_id), str(amount)]
                await transfer_cmd(update, context)
                return
            except: await update.message.reply_text("❌ ID КОЛИЧЕСТВО"); return
    
    if chat_type == "private":
        if await reply_button_handler(update, context): return
    
    is_image_request = False; should_respond = False
    
    if chat_type in ["group", "supergroup"]:
        mention = f"@{bot_username}"
        text_lower = text.lower().strip()
        if mention in text:
            clean_text = text.replace(mention, "").strip()
            should_respond = True
            if clean_text.lower().startswith("нарисуй"): text = clean_text[7:].strip(); is_image_request = True
            else: text = clean_text
        if not should_respond:
            keywords_map = {"нарисуй ": True, "сгенерируй ": True, "создай ": True, "бот ": False, "нейробот ": False, "нейросеть ": False, "ai ": False}
            for kw, is_image in keywords_map.items():
                if text_lower.startswith(kw):
                    clean_text = text[len(kw):].strip()
                    should_respond = True                    if is_image: is_image_request = True; text = clean_text
                    else: text = clean_text
                    break
        if not should_respond: return
        if not text:
            await update.message.reply_text(f"🧠 NeBlock AI V2!\n💬 @{bot_username} вопрос\n🎨 /genimage\n💸 /transfer", reply_to_message_id=update.message.message_id)
            return
    
    user = get_user(user_id)
    if context.user_data.get("waiting_promo"): 
        context.user_data["waiting_promo"] = False
        success, result = use_promo(user_id, text)
        await update.message.reply_text(f"🎟 +{result} 💮!" if success else f"❌ {result}")
        return
    
    active_preset_id = user.get("active_preset")
    if active_preset_id and not is_image_request:
        preset = DEFAULT_PRESETS.get(active_preset_id) or user.get("custom_presets", {}).get(active_preset_id)
        if preset: text = f"{preset['prompt']}\n\nЗапрос пользователя: {text}"
    
    if is_image_request or (chat_type == "private" and (user.get("current_model") == "image" or user.get("waiting_for_image"))):
        if chat_type == "private": users = load_users(); users[str(user_id)]["waiting_for_image"] = False; save_users(users)
        if not can_image_request(user_id, chat_type, chat_id): await update.message.reply_text("🚫 Лимит фото!", reply_markup=limit_reached_keyboard() if chat_type == "private" else None); return
        msg = await update.message.reply_text("🎨 Генерирую...")
        try:
            image_bytes, error = await generate_image(text)
            if image_bytes: add_image_request(user_id, chat_type); await msg.delete(); await update.message.reply_photo(photo=image_bytes, caption=f"🎨 NeBlock Images V2\n📝 {text[:200]}")
            else: await msg.edit_text("❌ Ошибка")
        except:
            try: await msg.delete()
            except: pass
            await update.message.reply_text("❌ Ошибка")
        return
    
    if not can_request(user_id, chat_type, chat_id): await update.message.reply_text("🚫 Лимит!", reply_markup=limit_reached_keyboard() if chat_type == "private" else None); return
    
    msg = await update.message.reply_text("💬 Генерирую...")
    try:
        response = client.responses.create(prompt={"id": PROMPT_ID}, input=text); answer = response.output_text
        add_request(user_id, chat_type); await msg.delete()
        if answer:
            rem = remaining(user_id, chat_type, chat_id)
            if chat_type in ["group", "supergroup"]: used = user.get("chat_requests_today", 0) + 1; total = CHAT_DAILY_LIMIT + user.get("extra_chat_requests", 0); label = "👥 Чат"
            else: used = user.get("requests_today", 0) + 1; total = DAILY_LIMIT + user.get("extra_requests", 0); label = "💬 NeBlock AI V2"
            footer = f"\n\n━━━━━━━━━━━━━━━━\n{label} | 📊 {used}/{total} | Осталось: {rem}{AI_DISCLAIMER}"
            for i in range(0, len(answer), 4000): 
                chunk = answer[i:i+4000]
                await update.message.reply_text(chunk + footer if i == 0 else chunk, reply_to_message_id=update.message.message_id if chat_type != "private" else None)
        else: await update.message.reply_text(f"🤷 Пусто{AI_DISCLAIMER}")
    except:
        try: await msg.delete()
        except: pass
        await update.message.reply_text(f"❌ Ошибка{AI_DISCLAIMER}")

def main():
    print(f"🧠 NeBlock AI V{BOT_VERSION}")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("streak", streak_cmd))
    app.add_handler(CommandHandler("streak_info", streak_info_cmd))
    app.add_handler(CommandHandler("genimage", genimage_cmd))
    app.add_handler(CommandHandler("tokenrate", tokenrate_cmd))
    app.add_handler(CommandHandler("discounts", discounts_cmd))
    app.add_handler(CommandHandler("transfer", transfer_cmd))
    app.add_handler(CommandHandler("transferinfo", transfer_info_cmd))
    app.add_handler(CommandHandler("donate", donate_cmd))
    app.add_handler(CommandHandler("donatetop", donatetop_cmd))
    app.add_handler(CommandHandler("promo", promo_cmd))
    app.add_handler(CommandHandler("presets", presets_cmd))
    app.add_handler(CommandHandler("my_presets", my_presets_cmd))
    app.add_handler(CommandHandler("add_preset", add_preset_cmd))
    app.add_handler(CommandHandler("faq", lambda u, c: u.message.reply_text(FAQ_TEXT[:4000])))
    app.add_handler(CommandHandler("changelog", changelog_cmd))
    app.add_handler(CommandHandler("commands", commands_cmd))
    app.add_handler(CommandHandler("shopdesc", shopdesc_cmd))
    app.add_handler(CommandHandler("chatowner", chatowner_cmd))
    app.add_handler(CommandHandler("chatshop", chatshop_cmd))
    app.add_handler(CommandHandler("shop", lambda u, c: u.message.reply_text("🛒 Магазин", reply_markup=shop_keyboard("private", u.effective_user.id))))
    
    app.add_handler(CommandHandler("give", admin_give))
    app.add_handler(CommandHandler("take", admin_take))
    app.add_handler(CommandHandler("resetuser", admin_resetuser))
    app.add_handler(CommandHandler("setpremium", admin_setpremium))
    app.add_handler(CommandHandler("userinfo", admin_userinfo))
    app.add_handler(CommandHandler("top", admin_top))
    app.add_handler(CommandHandler("cleardiscounts", admin_cleardiscounts))
    app.add_handler(CommandHandler("createpromo", admin_create_promo))
    app.add_handler(CommandHandler("promos", admin_promos))
    app.add_handler(CommandHandler("deletepromo", admin_delete_promo))
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CommandHandler("forcediscounts", admin_forcediscounts))
    app.add_handler(CommandHandler("forcerate", admin_force_rate))
    app.add_handler(CommandHandler("broadcast", admin_broadcast))
    
    app.add_handler(CallbackQueryHandler(inline_button_handler))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    print("✅ Бот запущен!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
