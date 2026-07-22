iimport openai
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
# 🧠 NeBlock AI V4.1 - Конфигурация
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
DISCOUNTS_FILE = "discounts.json"
TOKEN_RATE_FILE = "token_rate.json"
TOKEN_HISTORY_FILE = "token_history.json"
TRANSFER_LOG_FILE = "transfer_log.json"
DONATION_FILE = "donations.json"
ADMIN_IDS = [1671403667]
START_BONUS = 50
REFERRAL_BONUS = 25
INVITED_BONUS = 10
BOT_VERSION = "4.1"

MIN_TRANSFER = 1
MAX_TRANSFER = 10000
DAILY_TRANSFER_LIMIT = 50000
MIN_DONATION = 1
MAX_DONATION = 100000

# ═══════════════════════════════════════════
# 🔥 СИСТЕМА ЕЖЕДНЕВНЫХ НАГРАД (СТРИКИ ДО 30 ДНЕЙ)
# ═══════════════════════════════════════════

STREAK_BASE_REWARDS = {
    1: {"name": "День 1", "base_min": 5, "base_max": 10, "icon": "🌱", "desc": "Начало пути! Первый день получения бонуса."},
    2: {"name": "День 2", "base_min": 6, "base_max": 12, "icon": "🌿", "desc": "Второй день подряд. Бонус немного увеличивается."},
    3: {"name": "День 3", "base_min": 8, "base_max": 15, "icon": "🌳", "desc": "Третий день! Стабильность вознаграждается."},
    4: {"name": "День 4", "base_min": 10, "base_max": 18, "icon": "🍀", "desc": "Четвёртый день. Удача на вашей стороне!"},
    5: {"name": "День 5", "base_min": 12, "base_max": 22, "icon": "⭐", "desc": "Пятый день. Вы настоящий постоянный пользователь!"},
    6: {"name": "День 6", "base_min": 15, "base_max": 25, "icon": "🌟", "desc": "Шестой день. Почти неделя! Бонус значительно вырос."},
    7: {"name": "НЕДЕЛЯ! 🎉", "base_min": 20, "base_max": 35, "icon": "🔥", "desc": "Целая неделя ежедневных бонусов! Максимальная награда за неделю."},
    8: {"name": "День 8", "base_min": 22, "base_max": 38, "icon": "💫", "desc": "Вторая неделя! Бонусы продолжают расти."},
    9: {"name": "День 9", "base_min": 24, "base_max": 40, "icon": "✨", "desc": "Девятый день. Вы не сдаётесь!"},
    10: {"name": "День 10 🎊", "base_min": 26, "base_max": 45, "icon": "🎯", "desc": "Юбилейный 10-й день! Отличный результат."},
    11: {"name": "День 11", "base_min": 28, "base_max": 48, "icon": "🔮", "desc": "Одиннадцатый день. Магия постоянства."},
    12: {"name": "День 12", "base_min": 30, "base_max": 50, "icon": "💎", "desc": "Двенадцатый день. Драгоценная серия!"},
    13: {"name": "День 13", "base_min": 32, "base_max": 52, "icon": "🌈", "desc": "Тринадцатый день. Радуга наград."},
    14: {"name": "2 НЕДЕЛИ! 🏆", "base_min": 35, "base_max": 58, "icon": "👑", "desc": "Две недели! Вы легенда постоянства."},
    15: {"name": "День 15", "base_min": 38, "base_max": 60, "icon": "🎪", "desc": "Пятнадцатый день. Праздник продолжается."},
    16: {"name": "День 16", "base_min": 40, "base_max": 62, "icon": "🎭", "desc": "Шестнадцатый день. Театр наград."},
    17: {"name": "День 17", "base_min": 42, "base_max": 65, "icon": "🎪", "desc": "Семнадцатый день. Арена бонусов."},
    18: {"name": "День 18", "base_min": 44, "base_max": 68, "icon": "🏰", "desc": "Восемнадцатый день. Замок постоянства."},
    19: {"name": "День 19", "base_min": 46, "base_max": 70, "icon": "🌋", "desc": "Девятнадцатый день. Извержение бонусов."},
    20: {"name": "День 20 🎖️", "base_min": 48, "base_max": 75, "icon": "🏅", "desc": "Двадцатый день! Медаль за упорство."},
    21: {"name": "3 НЕДЕЛИ! 🌟", "base_min": 50, "base_max": 80, "icon": "💫", "desc": "Три недели! Вы на вершине постоянства."},
    22: {"name": "День 22", "base_min": 52, "base_max": 82, "icon": "🎯", "desc": "Двадцать второй день. Точное попадание."},
    23: {"name": "День 23", "base_min": 54, "base_max": 85, "icon": "🔱", "desc": "Двадцать третий день. Трезубец удачи."},
    24: {"name": "День 24", "base_min": 56, "base_max": 88, "icon": "⚡", "desc": "Двадцать четвёртый день. Электричество бонусов."},
    25: {"name": "День 25 🎂", "base_min": 58, "base_max": 90, "icon": "🎂", "desc": "Серебряный юбилей! 25 дней подряд."},
    26: {"name": "День 26", "base_min": 60, "base_max": 92, "icon": "🚀", "desc": "Двадцать шестой день. Взлёт наград."},
    27: {"name": "День 27", "base_min": 62, "base_max": 95, "icon": "🌌", "desc": "Двадцать седьмой день. Космические бонусы."},
    28: {"name": "4 НЕДЕЛИ! 🌍", "base_min": 65, "base_max": 100, "icon": "🌍", "desc": "Целый месяц! Мировое достижение."},
    29: {"name": "День 29", "base_min": 68, "base_max": 105, "icon": "🔮", "desc": "Предпоследний день перед супер-наградой!"},
    30: {"name": "ДЕНЬ 30! 👑✨", "base_min": 75, "base_max": 120, "icon": "👑", "desc": "МЕГА-ДЕНЬ! Максимальная награда + Премиум ЛС на 1 день (единоразово)!", "premium_bonus": True},
}

MAX_STREAK_DAY = 30

def get_daily_bonus_info():
    """Возвращает подробную информацию о всех днях серии"""
    text = "🔥 ЕЖЕДНЕВНЫЕ НАГРАДЫ (СЕРИЯ ДО 30 ДНЕЙ)\n━━━━━━━━━━━━━━━━━━━━\n\n"
    text += "📐 КАК РАБОТАЕТ СИСТЕМА:\n"
    text += "• Заходите каждый день и забирайте бонус\n"
    text += "• Чем дольше серия — тем выше базовая награда\n"
    text += "• Размер награды зависит от дня серии и курса NBT\n"
    text += "• Формула: базовая награда дня × множитель курса\n"
    text += "• Множитель курса = 1.0 + (курс × 10 - 0.1)\n"
    text += "• При курсе $0.01 → множитель ×1.0 (базовый)\n"
    text += "• При курсе $0.02 → множитель ×1.1 (+10%)\n"
    text += "• При курсе $0.005 → множитель ×0.95 (-5%)\n\n"
    text += "⚠️ ВАЖНО: Если не забрать бонус до 00:00 МСК — серия СГОРИТ!\n"
    text += "👑 На 30-й день: единоразовый Премиум ЛС на 1 день!\n"
    text += "💡 После 30 дня награды фиксируются (как в 30-й день, но без премиума)\n\n"
    
    text += "📅 ВСЕ НАГРАДЫ ПО ДНЯМ (БАЗОВЫЕ, БЕЗ УЧЁТА КУРСА):\n\n"
    
    for day in range(1, 31):
        reward = STREAK_BASE_REWARDS[day]
        text += f"{reward['icon']} {reward['name']}: {reward['base_min']}-{reward['base_max']} 💮 (база)"
        if reward.get("premium_bonus"):
            text += " + 🎁 Премиум ЛС 1 день! (единоразово)"
        text += f"\n   {reward['desc']}\n\n"
    
    text += "🎁 Как получить: кнопка «🔥 Награды» → «🎁 Забрать ежедневный бонус»\n"
    text += "📊 Статистика: команда /streak"
    
    return text

def get_user_bonus(streak, rate=0.01):
    """
    Рассчитывает бонус в зависимости от серии и текущего курса.
    
    Зависимость от дня серии:
    - День 1: база 5-10 💮
    - День 7: база 20-35 💮
    - День 14: база 35-58 💮
    - День 21: база 50-80 💮
    - День 30: база 75-120 💮 + Премиум
    
    Зависимость от курса:
    - Множитель = 1.0 + (rate × 10 - 0.1)
    - Ограничение: 0.5x - 1.5x
    """
    if streak >= MAX_STREAK_DAY:
        reward = STREAK_BASE_REWARDS[MAX_STREAK_DAY]
        is_max = True
    elif streak >= 1:
        reward = STREAK_BASE_REWARDS.get(streak, STREAK_BASE_REWARDS[1])
        is_max = False
    else:
        reward = STREAK_BASE_REWARDS[1]
        is_max = False
    
    rate_multiplier = 1.0 + (rate * 10 - 0.1)
    rate_multiplier = max(0.5, min(1.5, rate_multiplier))
    
    base_bonus = random.randint(reward["base_min"], reward["base_max"])
    bonus = max(1, int(base_bonus * rate_multiplier))
    
    premium_bonus = reward.get("premium_bonus", False)
    if is_max and streak > MAX_STREAK_DAY:
        premium_bonus = False
    
    return bonus, reward["icon"], reward["name"], premium_bonus, rate_multiplier

STREAK_INFO = get_daily_bonus_info()

TRANSFER_TAX_BRACKETS = [
    {"min": 0, "max": 199, "tax_percent": 0, "name": "Без налога"},
    {"min": 200, "max": 499, "tax_percent": 3, "name": "Малый перевод"},
    {"min": 500, "max": 999, "tax_percent": 5, "name": "Средний перевод"},
    {"min": 1000, "max": 2499, "tax_percent": 8, "name": "Крупный перевод"},
    {"min": 2500, "max": 4999, "tax_percent": 12, "name": "Очень крупный перевод"},
    {"min": 5000, "max": 10000, "tax_percent": 15, "name": "Максимальный перевод"},
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
    "extra5": 10, "extra10": 18, "extra50": 80,
    "unlimited_1h": 30, "unlimited_24h": 100, "unlimited_7d": 500,
    "image1": 15, "image5": 60, "image20": 200,
    "image_unlimited_1h": 50,
    "premium_day": 200, "premium_week": 1000, "premium_forever": 2500,
    "chat_extra10": 15, "chat_extra50": 60,
    "chat_unlimited_1h": 40, "chat_unlimited_24h": 150,
    "chat_image5": 50, "chat_image20": 180,
    "chat_premium_day": 300, "chat_premium_week": 1500, "chat_premium_forever": 3500,
}

AI_DISCLAIMER = "\n\n━━━━━━━━━━━━━━━━\n⚠️ ИИ может ошибаться. Только для справки."

CHANGELOG = """
📋 ЛОГ ОБНОВЛЕНИЙ NeBlock AI
━━━━━━━━━━━━━━━━━━━━

Версия 4.1 (22.07.2026)
• 🔥 Серия до 30 дней с прогрессивными наградами
• 💮 Награды зависят от курса NBT и дня серии
• 👑 30-й день: Премиум ЛС на 1 день (единоразово)
• ⚠️ Серия сгорает если не забрать до 00:00 МСК
• 📈 После 30 дня награды фиксируются
• 📐 Формула: базовая награда × множитель курса
• 🔧 Исправлены кнопки наград

Версия 4.0 (22.07.2026)
• 🔥 Улучшенная система ежедневных наград
• 📈 Награды растут с серией
• 🎉 Бонус за недельную серию

Версия 3.9 (21.07.2026)
• Курс по расписанию (0:00, 4:00, 8:00...)
• Фактор дня недели
"""

FAQ_TEXT = f"""
📚 ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ
━━━━━━━━━━━━━━━━━━━━

❓ Что такое NeBlock AI?
Платформа с ИИ-моделями в Telegram: текст и фото.

❓ Как работают ежедневные награды? 🔥
Каждый день вы получаете бонус. Размер зависит от:
• 📅 Дня серии (чем дольше, тем выше базовая награда)
• 💮 Курса NBT (чем выше курс, тем больше бонус)

📐 Формула: базовая награда × множитель курса
Множитель курса = 1.0 + (курс × 10 - 0.1)

Примеры базовых наград (без учёта курса):
• День 1: 5-10 💮 🌱
• День 7: 20-35 💮 🔥
• День 14: 35-58 💮 👑
• День 21: 50-80 💮 💫
• День 30: 75-120 💮 👑 + Премиум ЛС 1 день!

⚠️ ВАЖНО: Не забрали до 00:00 МСК — серия СГОРИТ!
💡 После 30 дня награды как в 30-й (без премиума).
/streak — подробнее

❓ Как заработать 💮?
• Ежедневный бонус (растёт с серией до 30 дней!)
• Рефералы: +{REFERRAL_BONUS} 💮 тебе, +{INVITED_BONUS} 💮 другу
• Стартовый бонус: {START_BONUS} 💮
• Промокоды, переводы от других

❓ Что такое 💮 NBT?
Внутренняя валюта. Курс обновляется каждые 4 часа по МСК.
День недели влияет на курс: Пн x1.05, Пт x1.10 🚀, Сб-Вс x0.95.
💡 Зарабатывайте в будни (выше курс), тратьте в выходные (дешевле товары)!

❓ Лимиты? Скидки? Премиум?
ЛС: {DAILY_LIMIT} текст + {IMAGE_DAILY_LIMIT} фото/день
Скидки каждые 2 дня в 9:00 МСК. Премиум — безлимит всего.
"""

DONATE_INFO_TEXT = """
🌍 БЛАГОТВОРИТЕЛЬНОСТЬ
━━━━━━━━━━━━━━━━━━━━

🔥 Что такое донат?
Вы сжигаете токены NBT навсегда, уменьшая общее предложение.
Это повышает курс токена для всех пользователей!

📊 Как это работает:
• Отправляете /donate СУММА
• Токены безвозвратно сгорают
• Вы попадаете в топ благотворителей
• Общее предложение NBT уменьшается
• Курс токена растёт

🏆 Топ благотворителей:
• /donatetop — список лучших
• 🥇🥈🥉 медали за первые 3 места

⚠️ Сожжённые токены нельзя вернуть!
💡 Минимальный донат: 1 💮
💡 Максимальный донат: 100 000 💮
"""

TRANSFER_INFO = f"""
💸 ПЕРЕВОДЫ 💮 NBT
━━━━━━━━━━━━━━━━━━━━

📤 СПОСОБЫ ПЕРЕВОДА:
• /transfer ID КОЛИЧЕСТВО — перевод по ID
• @username — перевод по username (в чатах)
• Ответ на сообщение — перевод автору сообщения (в чатах)

📊 ЛИМИТЫ:
• Минимальный перевод: {MIN_TRANSFER} 💮
• Максимальный перевод: {MAX_TRANSFER} 💮 за раз
• Дневной лимит: {DAILY_TRANSFER_LIMIT} 💮

💰 НАЛОГИ:
• 0-199 💮: без налога (0%)
• 200-499 💮: малый перевод (3%)
• 500-999 💮: средний перевод (5%)
• 1000-2499 💮: крупный перевод (8%)
• 2500-4999 💮: очень крупный перевод (12%)
• 5000-10000 💮: максимальный перевод (15%)

⚠️ Налог удерживается из суммы перевода
💡 Получатель получает сумму за вычетом налога
"""

COMMANDS_LIST = """
📋 КОМАНДЫ NeBlock AI V4.1
━━━━━━━━━━━━━━━━━━━━

💬 ОСНОВНЫЕ:
/start — главное меню бота
/commands — список всех команд
/faq — часто задаваемые вопросы
/changelog — история обновлений

🛒 МАГАЗИН И ТОКЕНЫ:
/shop — магазин запросов и премиума
/tokenrate — текущий курс NBT
/discounts — активные скидки
/promo — активировать промокод

🔥 НАГРАДЫ:
/streak — ежедневные награды (до 30 дней!)

💸 ФИНАНСЫ:
/transfer — перевод токенов
/donate — благотворительность (сжигание)
/donatetop — топ благотворителей

🎨 ГЕНЕРАЦИЯ:
/genimage — генерация изображений

👥 ЧАТЫ:
/chatowner — управление чатом
/chatshop — магазин для чата
"""

DISCOUNT_TYPES = {
    "regular": {"name": "Обычная", "min": 5, "max": 25, "color": "🟢", "chance": 40, "icon": "🏷️"},
    "super": {"name": "Супер", "min": 30, "max": 50, "color": "🔴", "chance": 20, "icon": "🔥"},
    "flash": {"name": "Флеш", "min": 40, "max": 70, "color": "⚡", "chance": 8, "icon": "⏰"},
    "bundle": {"name": "Набор", "min": 15, "max": 35, "color": "📦", "chance": 12, "icon": "🎁"},
    "premium_discount": {"name": "Премиум", "min": 10, "max": 30, "color": "👑", "chance": 5, "icon": "💎"},
    "legendary": {"name": "ЛЕГЕНДАРНАЯ", "min": 100, "max": 100, "color": "🌟", "chance": 0.5, "icon": "💫"},
}

SHOP_ITEMS_BASE = {
    "extra5": {"name": "+5 запросов", "price": 10, "icon": "📝", "category": "text", "desc": "5 дополнительных текстовых запросов.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "private", "usage": "В ЛС."},
    "extra10": {"name": "+10 запросов", "price": 18, "icon": "📝", "category": "text", "desc": "10 дополнительных текстовых запросов.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "private", "usage": "В ЛС."},
    "extra50": {"name": "+50 запросов", "price": 80, "icon": "📝", "category": "text", "desc": "50 дополнительных текстовых запросов.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "private", "usage": "Активно."},
    "unlimited_1h": {"name": "Безлимит 1ч", "price": 30, "icon": "♾️", "category": "text", "desc": "Безлимитные текстовые запросы на 1 час.", "warning": "⚠️ Действует 1 час с момента покупки.", "location": "private", "usage": "Без лимита."},
    "unlimited_24h": {"name": "Безлимит 24ч", "price": 100, "icon": "♾️", "category": "text", "desc": "Безлимитные текстовые запросы на 24 часа.", "warning": "⚠️ Действует 24 часа с момента покупки.", "location": "private", "usage": "Сутки."},
    "unlimited_7d": {"name": "Безлимит 7д", "price": 500, "icon": "♾️", "category": "text", "desc": "Безлимитные текстовые запросы на 7 дней.", "warning": "⚠️ Действует 7 дней с момента покупки.", "location": "private", "usage": "Неделя."},
    "image1": {"name": "1 фото", "price": 15, "icon": "🎨", "category": "image", "desc": "1 дополнительная генерация изображения.", "warning": "⚠️ Сгорает в 00:00 МСК.", "location": "private", "usage": "Опишите."},
    "image5": {"name": "5 фото", "price": 60, "icon": "🎨", "category": "image", "desc": "5 дополнительных генераций изображений.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "private", "usage": "5 фото."},
    "image20": {"name": "20 фото", "price": 200, "icon": "🎨", "category": "image", "desc": "20 дополнительных генераций изображений.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "private", "usage": "Творчество."},
    "image_unlimited_1h": {"name": "Безлимит фото 1ч", "price": 50, "icon": "♾️", "category": "image", "desc": "Безлимитные генерации изображений на 1 час.", "warning": "⚠️ Действует 1 час с момента покупки.", "location": "private", "usage": "Без лимита."},
    "premium_day": {"name": "Премиум ЛС 1д", "price": 200, "icon": "⭐", "category": "premium", "desc": "Полный безлимит на всё в ЛС на 24 часа.", "warning": "⚠️ Действует 24 часа с момента покупки.", "location": "private", "usage": "Всё включено."},
    "premium_week": {"name": "Премиум ЛС 7д", "price": 1000, "icon": "⭐", "category": "premium", "desc": "Полный безлимит на всё в ЛС на 7 дней.", "warning": "⚠️ Действует 7 дней с момента покупки.", "location": "private", "usage": "Неделя комфорта."},
    "premium_forever": {"name": "Премиум ЛС навсегда", "price": 2500, "icon": "👑", "category": "premium", "desc": "Полный безлимит на всё в ЛС навсегда.", "warning": "⚠️ Только для личных сообщений.", "location": "private", "usage": "Максимальная выгода!"},
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
    now = datetime.now()
    hour = now.hour
    block_hour = (hour // 4) * 4
    return f"{now.strftime('%Y-%m-%d')}-{block_hour:02d}", block_hour

def get_next_rate_update():
    now = datetime.now()
    hour = now.hour
    block_hour = (hour // 4) * 4
    next_block = block_hour + 4
    if next_block >= 24:
        next_update = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        next_update = now.replace(hour=next_block, minute=0, second=0, microsecond=0)
    return next_update

def get_transfer_tax(amount):
    for bracket in TRANSFER_TAX_BRACKETS:
        if bracket["min"] <= amount <= bracket["max"]:
            return int(amount * bracket["tax_percent"] / 100), bracket["tax_percent"], bracket["name"]
    return 0, 0, "Без налога"

def log_transfer(from_id, to_id, amount, tax, final_amount, chat_type="private", chat_id=None):
    log = load_json(TRANSFER_LOG_FILE)
    if "transfers" not in log: log["transfers"] = []
    log["transfers"].append({
        "date": datetime.now().strftime("%Y-%m-%d"), "timestamp": datetime.now().isoformat(),
        "from_id": from_id, "to_id": to_id, "amount": amount, "tax": tax,
        "final_amount": final_amount, "chat_type": chat_type,
        "chat_id": str(chat_id) if chat_id else None,
    })
    if len(log["transfers"]) > 1000: log["transfers"] = log["transfers"][-1000:]
    save_json(TRANSFER_LOG_FILE, log)

def log_donation(user_id, amount):
    donations = load_donations()
    if "donations" not in donations: donations["donations"] = []
    donations["donations"].append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "amount": amount,
    })
    if len(donations["donations"]) > 1000: donations["donations"] = donations["donations"][-1000:]
    save_donations(donations)

def get_token_rate():
    rate_data = load_json(TOKEN_RATE_FILE)
    history = load_json(TOKEN_HISTORY_FILE)
    now = datetime.now()
    current_block, block_hour = get_current_rate_block()
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
        
        base_rate = 0.01
        supply_factor = max(0.3, min(3.0, 15000 / max(total_tokens, 500))) if total_tokens > 0 else 1.0
        activity_factor = 0.7 + ((active_users / max(total_users, 1)) * 0.6) if total_users > 0 else 1.0
        burn_factor = 0.8 + ((total_burned / max(total_earned + donated_total, 1)) * 0.4) if (total_earned + donated_total) > 0 else 1.0
        day_factor, day_name, day_icon = get_day_factor()
        
        volatility = 1.0
        if history:
            rates = [h.get("rate", base_rate) for h in history.values() if h.get("rate")]
            if len(rates) > 1:
                avg_rate = sum(rates) / len(rates)
                std_dev = math.sqrt(sum((r - avg_rate) ** 2 for r in rates) / len(rates))
                volatility = 1.0 + (std_dev / max(avg_rate, 0.0001)) * 0.5
        
        market_noise = random.uniform(0.92, 1.08)
        rate = round(base_rate * supply_factor * activity_factor * burn_factor * day_factor * volatility * market_noise, 8)
        rate = max(0.0001, min(1.0, rate))
        market_cap = round(total_tokens * rate, 2)
        yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_rate = history.get(yesterday, {}).get("rate", rate)
        change_24h = round(((rate - yesterday_rate) / max(yesterday_rate, 0.0001)) * 100, 2)
        trend = "📈" if change_24h > 0.5 else "📉" if change_24h < -0.5 else "📊"
        next_update = get_next_rate_update()
        
        rate_data = {
            "rate_block": current_block, "block_hour": block_hour, "date": now.strftime("%Y-%m-%d"),
            "rate": rate, "total_supply": total_tokens, "total_burned": total_burned,
            "total_donated": donated_total, "day_factor": day_factor, "day_name": day_name, "day_icon": day_icon,
            "supply_factor": round(supply_factor, 4), "activity_factor": round(activity_factor, 4),
            "burn_factor": round(burn_factor, 4), "volatility_index": round(volatility, 4),
            "market_cap": market_cap, "change_24h": change_24h, "trend": trend,
            "next_update": next_update.strftime("%H:%M МСК"), "updated_at": now.isoformat(),
        }
        save_json(TOKEN_RATE_FILE, rate_data)
        
        today = now.strftime("%Y-%m-%d")
        history[today] = {"rate": rate, "supply": total_tokens, "market_cap": market_cap}
        if len(history) > 30: history = dict(sorted(history.items())[-30:])
        save_json(TOKEN_HISTORY_FILE, history)
        logger.info(f"💮 Курс: ${rate:.8f} | Блок: {block_hour}:00 | {day_name} {day_icon}")
    
    return rate_data

def get_item_price(item_id):
    rate_data = get_token_rate()
    return max(1, int(BASE_PRICES_USD.get(item_id, 10) / 100 / rate_data.get("rate", 0.01)))

def get_shop_items():
    return {item_id: {**item, "price": get_item_price(item_id)} for item_id, item in SHOP_ITEMS_BASE.items()}

def generate_discounts():
    all_items = list(SHOP_ITEMS_BASE.keys())
    discounts = {"generated_at": datetime.now().isoformat()}
    used_items = set()
    if random.uniform(0, 100) < DISCOUNT_TYPES["legendary"]["chance"]:
        item_id = random.choice(all_items)
        discounts[item_id] = {"percent": 100, "original": get_item_price(item_id), "new_price": 0, "type": "legendary", "type_name": "ЛЕГЕНДАРНАЯ", "color": "🌟", "icon": "💫", "expires": (datetime.now() + timedelta(hours=3)).isoformat(), "special": True}
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
        original = get_item_price(item_id)
        new_price = max(1, int(original * (1 - percent / 100)))
        expires = (datetime.now() + timedelta(hours=24)).isoformat() if disc_type == "flash" else None
        discounts[item_id] = {"percent": percent, "original": original, "new_price": new_price, "type": disc_type, "type_name": dconfig["name"], "color": dconfig["color"], "icon": dconfig["icon"], "expires": expires}
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

def get_discounted_price(item_id):
    discounts = get_discounts()
    shop_items = get_shop_items()
    if item_id in discounts and item_id not in ["last_update", "generated_at"]:
        d = discounts[item_id]
        if not d.get("expires") or datetime.now() <= datetime.fromisoformat(d["expires"]):
            return d["new_price"], d["percent"], d
    return shop_items[item_id]["price"], 0, None

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
        "donated_tokens": 0,
        "used_promos": [], "waiting_for_image": False, "current_model": "text",
        "warnings": 0, "muted_until": None, "banned": False,
        "daily_transfer_total": 0, "transfer_reset_date": datetime.now().strftime("%Y-%m-%d"),
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

def donate_tokens(user_id, amount):
    users = load_users()
    uid = str(user_id)
    if uid in users:
        users[uid]["tokens"] = users[uid].get("tokens", 0) - amount
        users[uid]["spent_tokens"] = users[uid].get("spent_tokens", 0) + amount
        users[uid]["donated_tokens"] = users[uid].get("donated_tokens", 0) + amount
        save_users(users)
        log_donation(user_id, amount)
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

COMPILED_BLOCKED = [re.compile(w, re.IGNORECASE) for w in [
    r'\b(?:взлом|хак(?:ер|нуть)?|hack|crack|warez|кряк|keygen)\b',
    r'\b(?:наркотик|drugs|наркота|спайс|героин|кокаин)\b',
    r'\b(?:оружие|weapon|gun|бомба|bomb|взрывчатка|пистолет|автомат)\b',
    r'\b(?:дет[иь] порно|child porn|педофил|pedo|инцест)\b',
    r'\b(?:уби[йт]|убью|kill|murder|зака[зж]|hitman|киллер)\b',
    r'\b(?:террор|terror|теракт|ИГИЛ|ISIS|джихад)\b',
    r'\b(?:суицид|suicide|самоубий|повес[иь])\b',
]]
COMPILED_SEVERE = [re.compile(w, re.IGNORECASE) for w in [
    r'\b(?:дет[иь] порно|child porn|педофил|pedo|террор|terror|ИГИЛ|ISIS|уби[йт]|kill|суицид|suicide)\b'
]]

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
    ], resize_keyboard=True)

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("ℹ️ О боте", callback_data="about"), InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🧠 Модели", callback_data="models"), InlineKeyboardButton("💎 Премиум", callback_data="premium_info")],
        [InlineKeyboardButton("🔥 Награды", callback_data="streak_info"), InlineKeyboardButton("💮 Курс NBT", callback_data="tokenrate")],
        [InlineKeyboardButton("💸 Перевод", callback_data="transfer"), InlineKeyboardButton("🌍 Донат", callback_data="donate_info")],
    ])

def back_button(): return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="menu")]])

def shop_keyboard(location="private"):
    keyboard = []
    discounts = get_discounts()
    shop_items = get_shop_items()
    active = {k: v for k, v in discounts.items() if k not in ["last_update", "generated_at"]}
    if active:
        legendary = any(d.get("type") == "legendary" for d in active.values())
        keyboard.append([InlineKeyboardButton("🌟 ЛЕГЕНДАРНАЯ СКИДКА! 🌟" if legendary else "🎫 Скидки", callback_data="discounts_info")])
    cats = {"private": [("📝 Текст", "text"), ("🎨 Фото", "image"), ("⭐ Премиум", "premium")], "chat": [("👥 Запросы", "chat"), ("🖼️ Фото", "chat_image"), ("⭐ Премиум", "chat_premium")]}
    for label, cat in cats.get(location, cats["private"]):
        items_in_cat = False
        for item_id, item in shop_items.items():
            if item["category"] == cat and item.get("location") == location:
                if not items_in_cat: keyboard.append([InlineKeyboardButton(f"── {label} ──", callback_data="none")]); items_in_cat = True
                price, percent, disc = get_discounted_price(item_id)
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
    """Клавиатура раздела Награды"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 Забрать ежедневный бонус", callback_data="daily_bonus")],
        [InlineKeyboardButton("👥 Реферальная ссылка", callback_data="ref_link")],
        [InlineKeyboardButton("📅 Подробно о наградах", callback_data="streak_info")],
        [InlineKeyboardButton("🔙 Назад", callback_data="menu")],
    ])

def limit_reached_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🛒 Купить запросы", callback_data="shop"), InlineKeyboardButton("🔥 Награды", callback_data="streak_info")], [InlineKeyboardButton("💎 Премиум", callback_data="premium_info")]])

# ═══════════════════════════════════════════
# КОМАНДЫ
# ═══════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id; user = get_user(user_id); chat_type = update.effective_chat.type
    username = update.effective_user.username
    if username:
        users = load_users(); uid = str(user_id)
        if uid in users: users[uid]["username"] = username; save_users(users)
    if context.args and context.args[0].startswith("ref_"):
        ref_code = context.args[0].replace("ref_", ""); users = load_users(); uid = str(user_id)
        for u_id, u_data in users.items():
            if u_data.get("referral_code") == ref_code and u_id != uid and not users[uid].get("referred_by"):
                users[uid]["referred_by"] = u_id; add_tokens(int(u_id), REFERRAL_BONUS); add_tokens(user_id, INVITED_BONUS)
                users[u_id]["referrals"] = users[u_id].get("referrals", 0) + 1; save_users(users)
                try: await context.bot.send_message(int(u_id), f"🎉 Реферал!\n💰 +{REFERRAL_BONUS} 💮")
                except: pass
                break
    if chat_type in ["group", "supergroup"]:
        await update.message.reply_text(f"🧠 NeBlock AI V{BOT_VERSION} в чате!\n💬 @{context.bot.username} вопрос\n🎨 /genimage\n💸 /transfer\n🔥 /streak")
        return
    premium = "💎 Активен" if is_premium(user_id) else "Не активен"
    rate_data = get_token_rate(); rate = rate_data.get("rate", 0.01)
    day_icon = rate_data.get("day_icon", "📊"); day_name = rate_data.get("day_name", "")
    next_update = rate_data.get("next_update", "")
    streak = user.get("daily_bonus_streak", 0)
    donated_total, _, _ = get_donation_stats()
    await update.message.reply_text(
        f"🧠 NeBlock AI V{BOT_VERSION}\n━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💬 Текст | 🎨 Фото | 💸 Переводы | 🌍 Донаты\n"
        f"💎 Премиум ЛС: {premium}\n\n"
        f"💰 Баланс: {user.get('tokens', 0)} 💮 (~${user.get('tokens', 0) * rate:.2f})\n"
        f"💮 1 NBT = ${rate:.8f}\n"
        f"📅 {day_icon} {day_name} | 🕐 Обновление: {next_update}\n"
        f"🔥 Серия бонусов: {streak} дн. | Сожжено: {donated_total:,} 💮\n"
        f"📊 Лимиты: {DAILY_LIMIT} вопр. + {IMAGE_DAILY_LIMIT} фото/день\n\n"
        f"👇 Выбери модель:",
        reply_markup=main_reply_keyboard()
    )

async def streak_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подробная информация о ежедневных наградах"""
    user_id = update.effective_user.id
    user = get_user(user_id)
    streak = user.get("daily_bonus_streak", 0)
    rate_data = get_token_rate()
    rate = rate_data.get("rate", 0.01)
    
    text = f"🔥 ВАША СЕРИЯ: {streak} дн.\n━━━━━━━━━━━━━━━━\n\n"
    
    # Текущий статус
    if streak == 0:
        text += "🌱 Вы ещё не начали серию!\n"
        text += "Начните сегодня — заберите первый бонус!\n\n"
    elif streak >= MAX_STREAK_DAY:
        text += f"👑 Вы достигли максимальной серии ({MAX_STREAK_DAY} дней)!\n"
        text += f"Награды как в {MAX_STREAK_DAY}-й день (без премиума).\n"
        text += "⚠️ Не забудьте забирать бонус каждый день до 00:00 МСК, иначе серия сгорит!\n\n"
    else:
        next_day = streak + 1
        if next_day <= MAX_STREAK_DAY:
            next_reward = STREAK_BASE_REWARDS[next_day]
            rate_multiplier = 1.0 + (rate * 10 - 0.1)
            rate_multiplier = max(0.5, min(1.5, rate_multiplier))
            est_min = max(1, int(next_reward["base_min"] * rate_multiplier))
            est_max = max(1, int(next_reward["base_max"] * rate_multiplier))
            text += f"➡️ Завтра будет день {next_day}: {next_reward['icon']} {next_reward['name']}\n"
            text += f"   Базовая награда: {next_reward['base_min']}-{next_reward['base_max']} 💮\n"
            text += f"   С учётом курса (${rate:.6f}): ~{est_min}-{est_max} 💮\n"
            if next_reward.get("premium_bonus"):
                text += "   🎁 + Премиум ЛС на 1 день! (единоразово)\n"
            text += "\n"
    
    # Объяснение системы
    text += "📐 КАК СЧИТАЕТСЯ НАГРАДА:\n"
    text += "• Берётся базовая награда для вашего дня серии\n"
    text += "• Умножается на множитель курса NBT\n"
    text += "• Множитель = 1.0 + (курс × 10 - 0.1)\n"
    text += f"• Текущий курс: ${rate:.8f}\n"
    text += f"• Текущий множитель: ×{1.0 + (rate * 10 - 0.1):.2f}\n"
    text += "• Диапазон множителя: 0.5x - 1.5x\n\n"
    
    text += "⚠️ ВАЖНО:\n"
    text += "• Не забрали бонус до 00:00 МСК — серия СГОРИТ!\n"
    text += "• На 30-й день даётся Премиум ЛС на 1 день (единоразово)\n"
    text += "• После 30 дня награды как в 30-й день (без премиума)\n"
    text += "• Серия может длиться бесконечно\n\n"
    
    # Ключевые вехи
    text += "📅 КЛЮЧЕВЫЕ ВЕХИ (БАЗОВЫЕ НАГРАДЫ):\n"
    milestones = [1, 7, 14, 21, 28, 30]
    for day in milestones:
        reward = STREAK_BASE_REWARDS[day]
        text += f"{reward['icon']} День {day}: {reward['base_min']}-{reward['base_max']} 💮"
        if reward.get("premium_bonus"):
            text += " + 🎁 Премиум ЛС 1 день!"
        text += "\n"
    
    text += f"\n📋 Все 30 дней: /streak_info"
    
    await update.message.reply_text(text)

async def streak_info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает полную информацию о всех 30 днях"""
    await update.message.reply_text(STREAK_INFO[:4000])
    if len(STREAK_INFO) > 4000:
        await update.message.reply_text(STREAK_INFO[4000:])

async def tokenrate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rate_data = get_token_rate(); history = load_json(TOKEN_HISTORY_FILE)
    rate = rate_data.get("rate", 0.01); supply = rate_data.get("total_supply", 0)
    market_cap = rate_data.get("market_cap", 0); donated = rate_data.get("total_donated", 0)
    burned = rate_data.get("total_burned", 0)
    day_icon = rate_data.get("day_icon", "📊"); day_name = rate_data.get("day_name", "")
    block_hour = rate_data.get("block_hour", 0); next_update = rate_data.get("next_update", "")
    updated = rate_data.get("updated_at", "")
    updated_time = datetime.fromisoformat(updated).strftime("%d.%m.%Y %H:%M") if updated else "Нет"
    
    text = (f"💮 КУРС NBT\n━━━━━━━━━━━━━━━━\n\n"
            f"💰 1 NBT = ${rate:.8f}\n"
            f"💎 Капитализация: ${market_cap:,.2f}\n"
            f"🪙 В обороте: {supply:,} NBT\n"
            f"🔥 Сожжено всего: {burned:,} 💮\n"
            f"🌍 Пожертвовано: {donated:,} 💮\n"
            f"🕐 Обновлён: {updated_time} (блок {block_hour}:00)\n"
            f"🔄 Следующее обновление: {next_update}\n"
            f"📅 День недели: {day_icon} {day_name}\n\n"
            f"💡 Курс влияет на размер ежедневных наград!\n"
            f"💡 Зарабатывайте в будни, тратьте в выходные!\n\n📈 История за 7 дней:\n")
    for date, h in sorted(history.items())[-7:]: text += f"{date}: ${h.get('rate', 0):.8f}\n"
    await update.message.reply_text(text)

async def donate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text(f"{DONATE_INFO_TEXT}\n\nИспользование: /donate СУММА\nПример: /donate 100")
        return
    try: amount = int(context.args[0])
    except: await update.message.reply_text("❌ /donate СУММА"); return
    if amount < MIN_DONATION: await update.message.reply_text(f"❌ Мин: {MIN_DONATION} 💮"); return
    if amount > MAX_DONATION: await update.message.reply_text(f"❌ Макс: {MAX_DONATION} 💮"); return
    user = get_user(user_id)
    if user.get("tokens", 0) < amount: await update.message.reply_text(f"❌ Недостаточно!\n💰 Баланс: {user.get('tokens', 0)} 💮"); return
    await update.message.reply_text(
        f"🌍 ПОДТВЕРЖДЕНИЕ ДОНАТА\n━━━━━━━━━━━━━━━━\n"
        f"💰 Сумма: {amount} 💮\n"
        f"🔥 Токены сгорят НАВСЕГДА\n"
        f"💎 Баланс: {user.get('tokens', 0)} 💮 → {user.get('tokens', 0) - amount} 💮\n"
        f"📈 Это уменьшит предложение и может повысить курс!\n\n"
        f"Подтвердите:",
        reply_markup=donate_confirm_keyboard(amount)
    )

async def donatetop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total, count, top_donors = get_donation_stats()
    if not top_donors: 
        await update.message.reply_text("🌍 ТОП БЛАГОТВОРИТЕЛЕЙ\n━━━━━━━━━━━━━━━━\n\nПока никто не делал донатов.\nБудьте первым! /donate СУММА")
        return
    text = f"🌍 ТОП БЛАГОТВОРИТЕЛЕЙ\n━━━━━━━━━━━━━━━━\n\n🔥 Всего сожжено: {total:,} 💮\n📊 Количество донатов: {count}\n\n🏆 ТОП-10:\n"
    users = load_users(); medals = ["🥇", "🥈", "🥉"]
    for i, (uid, donated) in enumerate(top_donors):
        name = f"@{users.get(uid, {}).get('username', 'Неизвестный')}" if uid in users else f"ID:{uid}"
        medal = medals[i] if i < 3 else f"{i+1}."
        text += f"{medal} {name}: {donated:,} 💮\n"
    text += "\n💡 /donate СУММА — сделать вклад в развитие"
    await update.message.reply_text(text)

async def donate_info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(DONATE_INFO_TEXT)

async def genimage_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id; chat_type = update.effective_chat.type; chat_id = update.effective_chat.id if chat_type != "private" else None
    if not context.args: await update.message.reply_text("🎨 /genimage ОПИСАНИЕ\nПример: /genimage красивый закат на море"); return
    text = " ".join(context.args)
    if not can_image_request(user_id, chat_type, chat_id): await update.message.reply_text(f"🚫 Лимит фото исчерпан!\n\n💡 Купите дополнительные генерации в /shop\n💎 Или активируйте Премиум"); return
    msg = await update.message.reply_text("🎨 Генерирую изображение...")
    try:
        image_bytes, error = await generate_image(text)
        if image_bytes: add_image_request(user_id, chat_type); await msg.delete(); await update.message.reply_photo(photo=image_bytes, caption=f"🎨 NeBlock Images V2\n📝 {text[:200]}")
        else: await msg.edit_text("❌ Ошибка генерации")
    except:
        try: await msg.delete()
        except: pass
        await update.message.reply_text("❌ Ошибка генерации.")

async def transfer_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id; chat_type = update.effective_chat.type; to_id = None; amount = None
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
            if not to_id: await update.message.reply_text(f"❌ @{username} не найден."); return
        else: return
    else:
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(f"{TRANSFER_INFO}\n\nИспользование: /transfer ID КОЛИЧЕСТВО")
            return
        try: to_id = int(context.args[0]); amount = int(context.args[1])
        except: return
    if not to_id or not amount: return
    if amount < MIN_TRANSFER or amount > MAX_TRANSFER: return
    if to_id == user_id: await update.message.reply_text("❌ Нельзя перевести самому себе!"); return
    sender = get_user(user_id)
    if sender.get("daily_transfer_total", 0) + amount > DAILY_TRANSFER_LIMIT: 
        await update.message.reply_text(f"❌ Дневной лимит переводов: {DAILY_TRANSFER_LIMIT} 💮")
        return
    if sender.get("tokens", 0) < amount: await update.message.reply_text("❌ Недостаточно токенов!"); return
    tax, tax_percent, tax_name = get_transfer_tax(amount)
    receiver = get_user(to_id)
    if not receiver: await update.message.reply_text("❌ Получатель не найден!"); return
    final_amount = amount - tax
    receiver_name = receiver.get("username") or f"ID:{to_id}"
    tax_info = f"Налог: {tax} 💮 ({tax_percent}% - {tax_name})" if tax > 0 else "Без налога"
    await update.message.reply_text(
        f"⚠️ ПРОВЕРЬТЕ ДАННЫЕ ПЕРЕВОДА!\n━━━━━━━━━━━━━━━━\n"
        f"👤 Получатель: @{receiver_name}\n"
        f"🆔 ID: {to_id}\n"
        f"💸 Сумма: {amount} 💮\n"
        f"📊 {tax_info}\n"
        f"💰 Получит: {final_amount} 💮\n\n"
        f"Подтвердите перевод:",
        reply_markup=transfer_confirm_keyboard(to_id, amount)
    )

async def transfer_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["waiting_transfer"] = True
    await update.message.reply_text(f"{TRANSFER_INFO}\n\n💸 Отправьте ID и сумму:\nФормат: ID КОЛИЧЕСТВО\nПример: 1671403667 100")

async def transfer_info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(TRANSFER_INFO)

async def discounts_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    discounts = get_discounts(); active = {k: v for k, v in discounts.items() if k not in ["last_update", "generated_at"]}
    text = f"🎫 АКТИВНЫЕ СКИДКИ\n━━━━━━━━━━━━━━━━\n\n"
    text += f"🔄 Следующее обновление: {get_next_update_time().strftime('%d.%m.%Y в 9:00 МСК')}\n\n"
    if not active: text += "😔 Сейчас нет активных скидок.\nЗаходите позже или проверяйте /shop!"
    else:
        text += "📊 ДОСТУПНЫЕ СКИДКИ:\n\n"
        for item_id, disc in sorted(active.items(), key=lambda x: x[1]["percent"], reverse=True):
            item = get_shop_items().get(item_id)
            if item: 
                text += f"{disc.get('color', '🟢')} {item['icon']} {item['name']}\n"
                text += f"   Скидка: -{disc['percent']}%\n"
                text += f"   Цена: {disc['new_price']} 💮 (было {disc['original']} 💮)\n"
                text += f"   Тип: {disc.get('type_name', 'Обычная')} {disc.get('icon', '')}\n\n"
    await update.message.reply_text(text)

async def promo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["waiting_promo"] = True
    await update.message.reply_text("🎟 АКТИВАЦИЯ ПРОМОКОДА\n━━━━━━━━━━━━━━━━\n\nОтправьте промокод для получения бонуса.")

async def changelog_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    await update.message.reply_text(CHANGELOG)

async def commands_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    await update.message.reply_text(COMMANDS_LIST)

async def shopdesc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    await update.message.reply_text("📋 МАГАЗИН\n━━━━━━━━━━━━━━━━\n\nИспользуйте /shop для просмотра и покупки товаров.")

async def chatowner_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]: return
    chat_id = update.effective_chat.id; user_id = update.effective_user.id; add_chat_owner(chat_id, user_id)
    chats = load_chats(); c = chats.get(str(chat_id), {})
    owners = c.get("owners", []) if isinstance(c, dict) else c
    text = f"👑 ВЛАДЕЛЬЦЫ ЧАТА\n━━━━━━━━━━━━━━━━\n\n"
    for i, oid in enumerate(owners, 1): text += f"{i}. ID: {oid}\n"
    await update.message.reply_text(text)

async def chatshop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]: return
    chat_id = update.effective_chat.id; user_id = update.effective_user.id; add_chat_owner(chat_id, user_id)
    if not is_chat_owner(chat_id, user_id): 
        await update.message.reply_text("❌ Только владельцы чата могут использовать магазин чата.")
        return
    await update.message.reply_text(f"🛒 МАГАЗИН ЧАТА\n━━━━━━━━━━━━━━━━\n💰 Ваш баланс: {get_tokens(user_id)} 💮", reply_markup=shop_keyboard("chat"))

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
        await update.message.reply_text(f"👤 @{un}\n💰 {u.get('tokens', 0)} 💮\n🔥 Серия: {u.get('daily_bonus_streak', 0)} дн.\n🌍 Донатов: {u.get('donated_tokens', 0)}")
    except: pass

async def admin_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    users = load_users()
    top = sorted(users.items(), key=lambda x: x[1].get("tokens", 0), reverse=True)[:10]
    text = "🏆 ТОП ПО ТОКЕНАМ\n\n"
    for i, (uid, data) in enumerate(top, 1):
        name = f"@{data['username']}" if data.get("username") else f"ID:{uid}"
        text += f"{i}. {name} — {data.get('tokens', 0)} 💮\n"
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
    await update.message.reply_text(f"📊 СТАТИСТИКА\n👥 Пользователей: {len(users)}\n💮 В обороте: {rate_data.get('total_supply', 0):,} NBT\n🔥 Донатов: {donated_total:,} 💮")

async def admin_forcediscounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    new_d = generate_discounts(); new_d["last_update"] = datetime.now().strftime("%Y-%m-%d"); save_discounts(new_d)

async def admin_force_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    rate_data = load_json(TOKEN_RATE_FILE); rate_data["rate_block"] = ""; save_json(TOKEN_RATE_FILE, rate_data)
    new_rate = get_token_rate()
    await update.message.reply_text(f"💮 Курс обновлён: ${new_rate.get('rate', 0.01):.8f}")

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
        await update.message.reply_text(f"💬 NeBlock AI V2 — ТЕКСТОВАЯ МОДЕЛЬ\n━━━━━━━━━━━━━━━━\n\n📊 Осталось запросов: {remaining(user_id)}\n📝 Отправьте ваш вопрос или запрос.")
        return True
    
    if text == "🎨 NeBlock Images V2":
        users = load_users(); users[str(user_id)]["current_model"] = "image"; users[str(user_id)]["waiting_for_image"] = True; save_users(users)
        await update.message.reply_text(f"🎨 NeBlock Images V2 — ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЙ\n━━━━━━━━━━━━━━━━\n\n📊 Осталось генераций: {image_remaining(user_id)}\n📝 Опишите изображение для генерации.")
        return True
    
    if text == "👤 Профиль":
        u = get_user(user_id); joined = datetime.fromisoformat(u.get("joined", "")).strftime("%d.%m.%Y")
        last = "Никогда"
        if u.get("last_request"): last = datetime.fromisoformat(u["last_request"]).strftime("%d.%m.%Y в %H:%M")
        cm = "💬 NeBlock AI V2" if u.get("current_model") == "text" else "🎨 NeBlock Images V2"
        premium = "💎 Активен" if is_premium(user_id) else "Не активен"
        rate_data = get_token_rate(); rate = rate_data.get("rate", 0.01); usd = u.get("tokens", 0) * rate
        streak = u.get("daily_bonus_streak", 0)
        def fmt(x):
            if not x: return "Не активен"
            try:
                if datetime.now() < datetime.fromisoformat(x):
                    d = datetime.fromisoformat(x) - datetime.now(); days, hours = d.days, d.seconds // 3600
                    return f"Активен ({days}д {hours}ч)" if days > 0 else f"Активен ({hours}ч)"
            except: pass
            return "Не активен"
        await update.message.reply_text(
            f"👤 ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ\n━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🆔 ID: {user_id}\n"
            f"📅 Присоединился: {joined}\n"
            f"🔮 Текущая модель: {cm}\n"
            f"💎 Премиум: {premium}\n\n"
            f"💰 Баланс: {u.get('tokens', 0)} 💮 (~${usd:.2f})\n"
            f"💮 Курс NBT: 1 = ${rate:.8f}\n"
            f"🔥 Серия бонусов: {streak} дн.\n"
            f"💎 Заработано всего: {u.get('earned_tokens', 0)} 💮\n"
            f"💸 Потрачено всего: {u.get('spent_tokens', 0)} 💮\n"
            f"🌍 Пожертвовано: {u.get('donated_tokens', 0)} 💮\n\n"
            f"📊 ИСПОЛЬЗОВАНО СЕГОДНЯ:\n"
            f"💬 Текст (ЛС): {u.get('requests_today', 0)}/{DAILY_LIMIT + u.get('extra_requests', 0)} | {fmt(u.get('unlimited_until'))}\n"
            f"🎨 Фото (ЛС): {u.get('image_requests_today', 0)}/{IMAGE_DAILY_LIMIT + u.get('extra_image_requests', 0)} | {fmt(u.get('image_unlimited_until'))}\n"
            f"👥 Текст (чаты): {u.get('chat_requests_today', 0)}/{CHAT_DAILY_LIMIT + u.get('extra_chat_requests', 0)} | {fmt(u.get('chat_unlimited_until'))}\n"
            f"💸 Переводов сегодня: {u.get('daily_transfer_total', 0)} 💮\n\n"
            f"📈 ВСЕГО ЗА ВСЁ ВРЕМЯ:\n"
            f"💬 Текстовых запросов: {u.get('total_requests', 0)}\n"
            f"🎨 Сгенерировано фото: {u.get('total_images', 0)}\n"
            f"🛡 Предупреждения: {u.get('warnings', 0)}/5\n"
            f"👥 Рефералов: {u.get('referrals', 0)}\n"
            f"🕐 Последняя активность: {last}",
            reply_markup=main_menu()
        )
        return True
    
    if text == "🛒 Магазин": 
        await update.message.reply_text(f"🛒 МАГАЗИН NeBlock AI\n━━━━━━━━━━━━━━━━\n\n💰 Ваш баланс: {get_tokens(user_id)} 💮\n\nВыберите категорию товаров:", reply_markup=shop_keyboard("private"))
        return True
    
    if text == "🔥 Награды": 
        user = get_user(user_id)
        streak = user.get("daily_bonus_streak", 0)
        rate_data = get_token_rate()
        rate = rate_data.get("rate", 0.01)
        
        text = f"🔥 НАГРАДЫ И БОНУСЫ\n━━━━━━━━━━━━━━━━\n\n"
        text += f"📊 Ваша серия: {streak} дн.\n"
        text += f"💮 Курс NBT: ${rate:.8f}\n"
        
        if streak > 0 and streak < MAX_STREAK_DAY:
            reward = STREAK_BASE_REWARDS[streak]
            text += f"🎁 Сегодняшний день: {reward['icon']} {reward['name']}\n"
        
        text += f"\n💰 Баланс: {get_tokens(user_id)} 💮\n\n"
        text += "Выберите действие:"
        
        await update.message.reply_text(text, reply_markup=earn_keyboard())
        return True
    
    if text == "💸 Перевод": 
        await transfer_button_handler(update, context)
        return True
    
    if text == "🌍 Донат": 
        await donate_info_cmd(update, context)
        return True
    
    if text == "🎟 Промокод": 
        await promo_cmd(update, context)
        return True
    
    if text == "📚 FAQ": 
        await update.message.reply_text(FAQ_TEXT[:4000])
        if len(FAQ_TEXT) > 4000:
            await update.message.reply_text(FAQ_TEXT[4000:])
        return True
    
    if text == "🎫 Скидки": 
        await discounts_cmd(update, context)
        return True
    
    if text == "💮 Курс NBT": 
        await tokenrate_cmd(update, context)
        return True
    
    return False

async def inline_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer(); user_id = query.from_user.id; data = query.data
    shop_items = get_shop_items()
    
    if data == "none": return
    if data == "transfer_cancel": await query.edit_message_text("❌ Перевод отменён."); return
    if data == "donate_cancel": await query.edit_message_text("❌ Донат отменён."); return
    
    if data.startswith("donate_confirm_"):
        amount = int(data.replace("donate_confirm_", ""))
        if get_user(user_id).get("tokens", 0) < amount: await query.edit_message_text("❌ Недостаточно токенов!"); return
        if donate_tokens(user_id, amount):
            donated_total, _, _ = get_donation_stats()
            await query.edit_message_text(
                f"🌍 ДОНАТ ВЫПОЛНЕН!\n━━━━━━━━━━━━━━━━\n\n"
                f"🔥 Сожжено: {amount} 💮\n"
                f"💎 Ваш баланс: {get_tokens(user_id)} 💮\n"
                f"🌍 Всего сожжено: {donated_total:,} 💮\n\n"
                f"Спасибо за вклад в развитие экосистемы!"
            )
        return
    
    if data.startswith("transfer_confirm_"):
        parts = data.split("_")
        if len(parts) >= 4:
            to_id = int(parts[2]); amount = int(parts[3])
            sender = get_user(user_id)
            if sender.get("tokens", 0) < amount: await query.edit_message_text("❌ Недостаточно токенов!"); return
            tax, tax_percent, tax_name = get_transfer_tax(amount)
            receiver = get_user(to_id)
            if not receiver: await query.edit_message_text("❌ Получатель не найден!"); return
            final_amount = amount - tax
            users = load_users()
            uid_from = str(user_id); uid_to = str(to_id)
            users[uid_from]["tokens"] = users[uid_from].get("tokens", 0) - amount
            users[uid_from]["spent_tokens"] = users[uid_from].get("spent_tokens", 0) + amount
            users[uid_from]["daily_transfer_total"] = users[uid_from].get("daily_transfer_total", 0) + amount
            users[uid_to]["tokens"] = users[uid_to].get("tokens", 0) + final_amount
            users[uid_to]["earned_tokens"] = users[uid_to].get("earned_tokens", 0) + final_amount
            save_users(users); log_transfer(user_id, to_id, amount, tax, final_amount)
            tax_info = f"\n📊 Налог: {tax} 💮 ({tax_percent}% - {tax_name})" if tax > 0 else "\n📊 Без налога"
            await query.edit_message_text(
                f"✅ ПЕРЕВОД ВЫПОЛНЕН!\n━━━━━━━━━━━━━━━━\n"
                f"👤 Получатель: ID {to_id}\n"
                f"💸 Сумма: {amount} 💮\n"
                f"💰 Зачислено: {final_amount} 💮{tax_info}\n"
                f"💎 Ваш баланс: {get_tokens(user_id)} 💮"
            )
        return
    
    # Обработчики для кнопки "🔥 Награды" в разных меню
    if data == "streak_info":
        # Показываем информацию о наградах с кнопками действий
        user = get_user(user_id)
        streak = user.get("daily_bonus_streak", 0)
        rate_data = get_token_rate()
        rate = rate_data.get("rate", 0.01)
        
        text = f"🔥 НАГРАДЫ И БОНУСЫ\n━━━━━━━━━━━━━━━━\n\n"
        text += f"📊 Ваша серия: {streak} дн.\n"
        text += f"💮 Курс NBT: ${rate:.8f}\n"
        
        if streak > 0 and streak < MAX_STREAK_DAY:
            reward = STREAK_BASE_REWARDS[streak]
            text += f"🎁 Сегодняшний день: {reward['icon']} {reward['name']}\n"
        elif streak >= MAX_STREAK_DAY:
            text += f"👑 Максимальная серия!\n"
        
        text += f"\n💰 Баланс: {get_tokens(user_id)} 💮\n\n"
        text += "Выберите действие:"
        
        await query.edit_message_text(text, reply_markup=earn_keyboard())
        return
    
    if data == "menu": 
        await query.edit_message_text(
            f"🧠 NeBlock AI V{BOT_VERSION}\n━━━━━━━━━━━━━━━━\n\n"
            f"💰 Баланс: {get_tokens(user_id)} 💮\n\n"
            f"Выберите раздел:",
            reply_markup=main_menu()
        )
        return
    
    if data == "about": 
        await query.edit_message_text(
            f"ℹ️ О БОТЕ NeBlock AI\n━━━━━━━━━━━━━━━━\n\n"
            f"Версия: {BOT_VERSION}\n\n"
            f"💬 Текстовые запросы — YandexGPT\n"
            f"🎨 Генерация изображений — YandexART\n"
            f"💸 Переводы токенов между пользователями\n"
            f"🌍 Благотворительность — сжигание токенов\n"
            f"🔥 Ежедневные награды — серия до 30 дней\n"
            f"💮 Внутренняя валюта NBT с рыночным курсом\n\n"
            f"📊 Лимиты в ЛС:\n"
            f"• {DAILY_LIMIT} текстовых запросов/день\n"
            f"• {IMAGE_DAILY_LIMIT} генераций фото/день\n\n"
            f"💡 Используйте /faq для ответов на вопросы",
            reply_markup=back_button()
        )
        return
    
    if data == "donate_info": 
        await query.edit_message_text(DONATE_INFO_TEXT, reply_markup=back_button())
        return
    
    if data == "models": 
        await query.edit_message_text(
            "🧠 МОДЕЛИ NeBlock AI\n━━━━━━━━━━━━━━━━\n\n"
            "💬 NeBlock AI V2 — текстовая модель\n"
            "• Отвечает на вопросы\n"
            "• Помогает с задачами\n"
            "• Работает в ЛС и чатах\n\n"
            "🎨 NeBlock Images V2 — генерация изображений\n"
            "• Создаёт изображения по описанию\n"
            "• Размер: 1024×1024\n"
            "• Команда: /genimage",
            reply_markup=back_button()
        )
        return
    
    if data == "tokenrate":
        rd = get_token_rate()
        await query.edit_message_text(
            f"💮 КУРС NBT\n━━━━━━━━━━━━━━━━\n\n"
            f"💰 1 NBT = ${rd.get('rate', 0.01):.8f}\n"
            f"💎 Капитализация: ${rd.get('market_cap', 0):,.2f}\n"
            f"🪙 В обороте: {rd.get('total_supply', 0):,} NBT\n"
            f"🔥 Сожжено: {rd.get('total_donated', 0):,} 💮\n"
            f"{rd.get('day_icon', '📊')} День: {rd.get('day_name', '')}\n"
            f"🔄 Обновление: {rd.get('next_update', '')}\n\n"
            f"💡 Курс влияет на размер ежедневных наград!",
            reply_markup=back_button()
        )
        return
    
    if data == "transfer": 
        context.user_data["waiting_transfer"] = True
        await query.edit_message_text(
            f"{TRANSFER_INFO}\n\n"
            f"💸 Отправьте ID и сумму:\n"
            f"Формат: ID КОЛИЧЕСТВО\n"
            f"Пример: 1671403667 100",
            reply_markup=back_button()
        )
        return
    
    if data == "commands": 
        await query.edit_message_text(COMMANDS_LIST, reply_markup=back_button())
        return
    
    if data == "changelog": 
        await query.edit_message_text(CHANGELOG, reply_markup=back_button())
        return
    
    if data == "discounts_info":
        discounts = get_discounts(); active = {k: v for k, v in discounts.items() if k not in ["last_update", "generated_at"]}
        text = "🎫 АКТИВНЫЕ СКИДКИ\n━━━━━━━━━━━━━━━━\n\n"
        if not active: text += "😔 Сейчас нет активных скидок."
        else:
            for item_id, disc in sorted(active.items(), key=lambda x: x[1]["percent"], reverse=True):
                item = shop_items.get(item_id)
                if not item: continue
                if disc.get("type") == "legendary": 
                    text += f"🌟 {item['icon']} {item['name']}\n💫 БЕСПЛАТНО! (ЛЕГЕНДАРНАЯ СКИДКА)\n\n"
                else: 
                    text += f"{disc.get('color', '🟢')} {item['icon']} {item['name']}\n🔥 Скидка -{disc['percent']}% = {disc['new_price']} 💮\n\n"
        await query.edit_message_text(text, reply_markup=back_button())
        return
    
    if data == "premium_info": 
        await query.edit_message_text(
            f"💎 ПРЕМИУМ В ЛС\n━━━━━━━━━━━━━━━━\n\n"
            f"Премиум снимает все лимиты в личных сообщениях:\n"
            f"• Безлимитные текстовые запросы\n"
            f"• Безлимитная генерация фото\n\n"
            f"🛒 ДОСТУПНЫЕ ТОВАРЫ:\n"
            f"⭐ Премиум ЛС 1 день — {shop_items.get('premium_day', {}).get('price', '?')} 💮\n"
            f"⭐ Премиум ЛС 7 дней — {shop_items.get('premium_week', {}).get('price', '?')} 💮\n"
            f"👑 Премиум ЛС навсегда — {shop_items.get('premium_forever', {}).get('price', '?')} 💮\n\n"
            f"💡 Также можно получить Премиум ЛС 1 день за 30-й день серии!",
            reply_markup=back_button()
        )
        return
    
    if data == "stats":
        u = get_user(user_id)
        await query.edit_message_text(
            f"📊 СТАТИСТИКА\n━━━━━━━━━━━━━━━━\n\n"
            f"💬 Запросов сегодня: {u.get('requests_today', 0)}\n"
            f"🎨 Генераций сегодня: {u.get('image_requests_today', 0)}\n"
            f"💰 Баланс: {u.get('tokens', 0)} 💮\n"
            f"🔥 Серия бонусов: {u.get('daily_bonus_streak', 0)} дн.\n"
            f"🌍 Пожертвовано: {u.get('donated_tokens', 0)} 💮\n"
            f"👥 Рефералов: {u.get('referrals', 0)}",
            reply_markup=back_button()
        )
        return
    
    if data == "shop": 
        await query.edit_message_text(
            f"🛒 МАГАЗИН\n━━━━━━━━━━━━━━━━\n\n"
            f"💰 Баланс: {get_tokens(user_id)} 💮\n\n"
            f"Выберите категорию:",
            reply_markup=shop_keyboard("private")
        )
        return
    
    if data == "earn": 
        user = get_user(user_id)
        streak = user.get("daily_bonus_streak", 0)
        await query.edit_message_text(
            f"🔥 НАГРАДЫ\n━━━━━━━━━━━━━━━━\n\n"
            f"📊 Серия: {streak} дн.\n"
            f"💰 Баланс: {get_tokens(user_id)} 💮\n\n"
            f"Выберите действие:",
            reply_markup=earn_keyboard()
        )
        return
    
    if data == "promo": 
        context.user_data["waiting_promo"] = True
        await query.edit_message_text("🎟 Отправьте промокод для активации.", reply_markup=back_button())
        return
    
    if data == "faq": 
        await query.edit_message_text(FAQ_TEXT[:4000], reply_markup=back_button())
        return
    
    if data == "daily_bonus":
        u = get_user(user_id); today = datetime.now().strftime("%Y-%m-%d")
        if u.get("daily_bonus_claimed") == today:
            await query.answer("❌ Вы уже забирали бонус сегодня! Приходите завтра.", show_alert=True)
        else:
            users = load_users(); uid = str(user_id)
            users[uid]["daily_bonus_claimed"] = today
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            
            # Обновляем серию
            if users[uid].get("last_bonus_date") == yesterday:
                users[uid]["daily_bonus_streak"] = users[uid].get("daily_bonus_streak", 0) + 1
            elif users[uid].get("last_bonus_date") != today:
                users[uid]["daily_bonus_streak"] = 1
            
            users[uid]["last_bonus_date"] = today
            streak = users[uid]["daily_bonus_streak"]
            
            # Получаем текущий курс для расчёта бонуса
            rate_data = get_token_rate()
            rate = rate_data.get("rate", 0.01)
            bonus, icon, day_name, premium_bonus, rate_multiplier = get_user_bonus(streak, rate)
            
            # Проверяем, не получил ли уже премиум за 30-й день
            if premium_bonus and users[uid].get("streak_30_premium_claimed"):
                premium_bonus = False
            
            save_users(users)
            add_tokens(user_id, bonus)
            
            # Выдаём премиум если нужно
            premium_text = ""
            if premium_bonus and not users[uid].get("streak_30_premium_claimed"):
                users = load_users()
                existing = users[uid].get("premium_until")
                base = datetime.fromisoformat(existing) if existing and datetime.now() < datetime.fromisoformat(existing) else datetime.now()
                users[uid]["premium_until"] = (base + timedelta(hours=24)).isoformat()
                users[uid]["streak_30_premium_claimed"] = True
                save_users(users)
                premium_text = "\n🎁 + Премиум ЛС на 1 день! (единоразово)"
            
            rate_info = f"\n📈 Множитель курса: ×{rate_multiplier:.2f}" if abs(rate_multiplier - 1.0) > 0.01 else ""
            
            await query.answer(f"🎉 +{bonus} 💮! {icon} {day_name}", show_alert=True)
            await query.edit_message_text(
                f"🎁 ЕЖЕДНЕВНЫЙ БОНУС ПОЛУЧЕН!\n━━━━━━━━━━━━━━━━\n\n"
                f"{icon} {day_name}\n"
                f"💰 Получено: +{bonus} 💮{premium_text}{rate_info}\n"
                f"💎 Баланс: {get_tokens(user_id)} 💮\n"
                f"🔥 Серия: {streak} дн.\n\n"
                f"⚠️ Заберите завтрашний бонус до 00:00 МСК!\n"
                f"🔄 Пропуск дня сбросит серию.\n"
                f"📅 /streak — все награды",
                reply_markup=back_button()
            )
        return
    
    if data == "ref_link":
        user = get_user(user_id); bot_username = (await context.bot.get_me()).username
        await query.edit_message_text(
            f"👥 РЕФЕРАЛЬНАЯ ПРОГРАММА\n━━━━━━━━━━━━━━━━\n\n"
            f"🔗 Ваша ссылка:\n"
            f"https://t.me/{bot_username}?start=ref_{user.get('referral_code', '')}\n\n"
            f"💰 Вы получаете: +{REFERRAL_BONUS} 💮 за каждого друга\n"
            f"🎁 Друг получает: +{INVITED_BONUS} 💮 при регистрации\n\n"
            f"📊 Ваши рефералы: {user.get('referrals', 0)}\n\n"
            f"💡 Отправьте ссылку друзьям и получайте бонусы!",
            reply_markup=back_button()
        )
        return
    
    if data.startswith("confirm_"):
        item_id = data.replace("confirm_", ""); item = shop_items.get(item_id)
        if not item: return
        price, percent, disc = get_discounted_price(item_id)
        tokens = get_tokens(user_id)
        if tokens < price: await query.answer("❌ Недостаточно токенов!", show_alert=True); return
        remove_tokens(user_id, price); users = load_users(); uid = str(user_id)
        actions = {"extra5": ("extra_requests", 5), "extra10": ("extra_requests", 10), "extra50": ("extra_requests", 50), "image1": ("extra_image_requests", 1), "image5": ("extra_image_requests", 5), "image20": ("extra_image_requests", 20)}
        time_actions = {"unlimited_1h": ("unlimited_until", 1), "unlimited_24h": ("unlimited_until", 24), "unlimited_7d": ("unlimited_until", 168), "image_unlimited_1h": ("image_unlimited_until", 1)}
        if item_id in actions: field, amount = actions[item_id]; users[uid][field] = users[uid].get(field, 0) + amount
        elif item_id in time_actions: field, hours = time_actions[item_id]; users[uid][field] = (datetime.now() + timedelta(hours=hours)).isoformat()
        elif item_id == "premium_day": users[uid]["premium_until"] = (datetime.now() + timedelta(hours=24)).isoformat()
        elif item_id == "premium_week": users[uid]["premium_until"] = (datetime.now() + timedelta(days=7)).isoformat()
        elif item_id == "premium_forever": users[uid]["premium_until"] = (datetime.now() + timedelta(days=36500)).isoformat()
        save_users(users)
        dt = f"\n🎫 Скидка: -{percent}%" if percent > 0 else ""
        if disc and disc.get("type") == "legendary": dt = "\n🌟 ЛЕГЕНДАРНАЯ СКИДКА! Товар бесплатно!"
        await query.answer(f"✅ {item['name']} куплен!", show_alert=True)
        await query.edit_message_text(
            f"✅ ПОКУПКА ВЫПОЛНЕНА!\n━━━━━━━━━━━━━━━━\n\n"
            f"{item['icon']} {item['name']}\n"
            f"📝 {item['desc']}{dt}\n"
            f"💰 Потрачено: {price} 💮\n"
            f"💎 Остаток: {get_tokens(user_id)} 💮",
            reply_markup=back_button()
        )
        return
    
    if data.startswith("buy_"):
        item_id = data.replace("buy_", ""); item = shop_items.get(item_id)
        if not item: return
        price, percent, disc = get_discounted_price(item_id)
        tokens = get_tokens(user_id); can = "✅ Хватает" if tokens >= price else "❌ Не хватает"
        dt = ""
        if percent > 0 and disc:
            if disc.get("type") == "legendary": dt = "\n\n🌟 ЛЕГЕНДАРНАЯ СКИДКА! Товар БЕСПЛАТНО!"
            else: dt = f"\n\n{disc.get('color', '🟢')} СКИДКА -{percent}%\n💵 Старая цена: {disc['original']} 💮\n🔥 Новая цена: {price} 💮"
        await query.edit_message_text(
            f"🛒 {item['icon']} {item['name']}\n━━━━━━━━━━━━━━━━\n\n"
            f"📝 Описание: {item['desc']}\n"
            f"⚠️ Важно: {item.get('warning', '')}{dt}\n\n"
            f"💎 Ваш баланс: {tokens} 💮\n"
            f"{can}",
            reply_markup=confirm_keyboard(item_id)
        )
        return

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤔 Неизвестная команда.\nИспользуйте /start для меню или /commands для списка команд.")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip() if update.message.text else ""
    user_id = update.effective_user.id; chat_type = update.effective_chat.type; chat_id = update.effective_chat.id
    bot_username = context.bot.username
    
    username = update.effective_user.username
    if username:
        users = load_users(); uid = str(user_id)
        if uid in users: users[uid]["username"] = username; save_users(users)
    
    if is_user_muted(user_id): await update.message.reply_text("🚫 Вы заблокированы."); return
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
            except: await update.message.reply_text("❌ Неверный формат. Используйте: ID КОЛИЧЕСТВО"); return
    
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
                    should_respond = True
                    if is_image: is_image_request = True; text = clean_text
                    else: text = clean_text
                    break
        if not should_respond: return
        if not text:
            await update.message.reply_text(f"🧠 NeBlock AI V2!\n💬 @{bot_username} вопрос\n🎨 @{bot_username} нарисуй\n🎨 /genimage\n💸 /transfer\n🔥 /streak", reply_to_message_id=update.message.message_id)
            return
    
    user = get_user(user_id)
    if context.user_data.get("waiting_promo"): 
        context.user_data["waiting_promo"] = False
        success, result = use_promo(user_id, text)
        await update.message.reply_text(f"🎟 Промокод активирован! +{result} 💮" if success else f"❌ {result}")
        return
    
    if is_image_request or (chat_type == "private" and (user.get("current_model") == "image" or user.get("waiting_for_image"))):
        if chat_type == "private": users = load_users(); users[str(user_id)]["waiting_for_image"] = False; save_users(users)
        if not can_image_request(user_id, chat_type, chat_id):
            await update.message.reply_text(f"🚫 Лимит генераций исчерпан!", reply_to_message_id=update.message.message_id if chat_type != "private" else None, reply_markup=limit_reached_keyboard() if chat_type == "private" else None); return
        msg = await update.message.reply_text("🎨 Генерирую изображение...", reply_to_message_id=update.message.message_id if chat_type != "private" else None)
        try:
            image_bytes, error = await generate_image(text)
            if image_bytes: add_image_request(user_id, chat_type); await msg.delete(); await update.message.reply_photo(photo=image_bytes, caption=f"🎨 NeBlock Images V2\n📝 {text[:200]}", reply_to_message_id=update.message.message_id if chat_type != "private" else None)
            else: await msg.edit_text("❌ Ошибка генерации.")
        except:
            try: await msg.delete()
            except: pass
            await update.message.reply_text("❌ Ошибка генерации.")
        return
    
    if not can_request(user_id, chat_type, chat_id):
        await update.message.reply_text(f"🚫 Лимит запросов исчерпан!", reply_markup=limit_reached_keyboard() if chat_type == "private" else None, reply_to_message_id=update.message.message_id if chat_type != "private" else None); return
    
    msg = await update.message.reply_text("💬 Генерирую ответ...", reply_to_message_id=update.message.message_id if chat_type != "private" else None)
    try:
        response = client.responses.create(prompt={"id": PROMPT_ID}, input=text); answer = response.output_text
        add_request(user_id, chat_type); await msg.delete()
        if answer:
            rem = remaining(user_id, chat_type, chat_id)
            if chat_type in ["group", "supergroup"]: used = user.get("chat_requests_today", 0) + 1; total = CHAT_DAILY_LIMIT + user.get("extra_chat_requests", 0); label = "👥 Чат"
            else: used = user.get("requests_today", 0) + 1; total = DAILY_LIMIT + user.get("extra_requests", 0); label = "💬 NeBlock AI V2"
            footer = f"\n\n━━━━━━━━━━━━━━━━\n{label} | 📊 {used}/{total} | Осталось: {rem}{AI_DISCLAIMER}"
            for i in range(0, len(answer), 4000): chunk = answer[i:i+4000]; await update.message.reply_text(chunk + footer if i == 0 else chunk, reply_to_message_id=update.message.message_id if chat_type != "private" else None)
        else: await update.message.reply_text(f"🤷 Пустой ответ{AI_DISCLAIMER}")
    except:
        try: await msg.delete()
        except: pass
        await update.message.reply_text(f"❌ Ошибка генерации{AI_DISCLAIMER}")

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
    app.add_handler(CommandHandler("faq", lambda u, c: u.message.reply_text(FAQ_TEXT[:4000])))
    app.add_handler(CommandHandler("changelog", changelog_cmd))
    app.add_handler(CommandHandler("commands", commands_cmd))
    app.add_handler(CommandHandler("shopdesc", shopdesc_cmd))
    app.add_handler(CommandHandler("chatowner", chatowner_cmd))
    app.add_handler(CommandHandler("chatshop", chatshop_cmd))
    app.add_handler(CommandHandler("shop", lambda u, c: u.message.reply_text("🛒 Магазин", reply_markup=shop_keyboard("private"))))
    
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
