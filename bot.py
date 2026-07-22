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
# 🧠 NeBlock AI V5.0 - Конфигурация
# ═══════════════════════════════════════════

TELEGRAM_TOKEN = "8700124191:AAE6qSSouLjlDxPWwoFObJORMbDotsby9co"
YANDEX_API_KEY = "AQVNy7Dm-dvQRzejHvH0383oHTZhhW2fda95I558"
YANDEX_FOLDER = "b1guk4h3j9t48lsjl6sq"
PROMPT_ID = "fvt621uiq1fftiu5qomu"
IMAGE_MODEL = "art://b1guk4h3j9t48lsjl6sq/aliceai-image-art-3.0/latest"

# ═══════════════════════════════════════════
# 📊 БАЛАНСИРОВКА ЭКОНОМИКИ V5.0
# ═══════════════════════════════════════════

# Лимиты снижены на 40% для стимулирования покупок
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

# Стартовые бонусы уменьшены на 50%
START_BONUS = 25
REFERRAL_BONUS = 15
INVITED_BONUS = 5
BOT_VERSION = "5.0"

# Лимиты переводов и донатов скорректированы
MIN_TRANSFER = 1
MAX_TRANSFER = 5000
DAILY_TRANSFER_LIMIT = 25000
MIN_DONATION = 1
MAX_DONATION = 50000

# ═══════════════════════════════════════════
# 🔥 СИСТЕМА ЕЖЕДНЕВНЫХ НАГРАД (СТРИКИ ДО 30 ДНЕЙ)
# ═══════════════════════════════════════════

# Базовые награды уменьшены на 60-70% для баланса
STREAK_BASE_REWARDS = {
    1: {"name": "День 1", "base_min": 1, "base_max": 3, "icon": "🌱", "desc": "Начало пути! Первый день получения бонуса."},
    2: {"name": "День 2", "base_min": 2, "base_max": 4, "icon": "🌿", "desc": "Второй день подряд. Бонус немного увеличивается."},
    3: {"name": "День 3", "base_min": 2, "base_max": 5, "icon": "🌳", "desc": "Третий день! Стабильность вознаграждается."},
    4: {"name": "День 4", "base_min": 3, "base_max": 6, "icon": "🍀", "desc": "Четвёртый день. Удача на вашей стороне!"},
    5: {"name": "День 5", "base_min": 3, "base_max": 7, "icon": "⭐", "desc": "Пятый день. Вы настоящий постоянный пользователь!"},
    6: {"name": "День 6", "base_min": 4, "base_max": 8, "icon": "🌟", "desc": "Шестой день. Почти неделя! Бонус значительно вырос."},
    7: {"name": "НЕДЕЛЯ! 🎉", "base_min": 5, "base_max": 10, "icon": "🔥", "desc": "Целая неделя ежедневных бонусов!"},
    8: {"name": "День 8", "base_min": 5, "base_max": 11, "icon": "💫", "desc": "Вторая неделя! Бонусы продолжают расти."},
    9: {"name": "День 9", "base_min": 6, "base_max": 12, "icon": "✨", "desc": "Девятый день. Вы не сдаётесь!"},
    10: {"name": "День 10 🎊", "base_min": 6, "base_max": 13, "icon": "🎯", "desc": "Юбилейный 10-й день! Отличный результат."},
    11: {"name": "День 11", "base_min": 7, "base_max": 14, "icon": "🔮", "desc": "Одиннадцатый день. Магия постоянства."},
    12: {"name": "День 12", "base_min": 7, "base_max": 15, "icon": "💎", "desc": "Двенадцатый день. Драгоценная серия!"},
    13: {"name": "День 13", "base_min": 8, "base_max": 16, "icon": "🌈", "desc": "Тринадцатый день. Радуга наград."},
    14: {"name": "2 НЕДЕЛИ! 🏆", "base_min": 8, "base_max": 18, "icon": "👑", "desc": "Две недели! Вы легенда постоянства."},
    15: {"name": "День 15", "base_min": 9, "base_max": 19, "icon": "🎪", "desc": "Пятнадцатый день. Праздник продолжается."},
    16: {"name": "День 16", "base_min": 9, "base_max": 20, "icon": "🎭", "desc": "Шестнадцатый день. Театр наград."},
    17: {"name": "День 17", "base_min": 10, "base_max": 21, "icon": "🎪", "desc": "Семнадцатый день. Арена бонусов."},
    18: {"name": "День 18", "base_min": 10, "base_max": 22, "icon": "🏰", "desc": "Восемнадцатый день. Замок постоянства."},
    19: {"name": "День 19", "base_min": 11, "base_max": 23, "icon": "🌋", "desc": "Девятнадцатый день. Извержение бонусов."},
    20: {"name": "День 20 🎖️", "base_min": 11, "base_max": 25, "icon": "🏅", "desc": "Двадцатый день! Медаль за упорство."},
    21: {"name": "3 НЕДЕЛИ! 🌟", "base_min": 12, "base_max": 27, "icon": "💫", "desc": "Три недели! Вы на вершине постоянства."},
    22: {"name": "День 22", "base_min": 13, "base_max": 28, "icon": "🎯", "desc": "Двадцать второй день. Точное попадание."},
    23: {"name": "День 23", "base_min": 13, "base_max": 29, "icon": "🔱", "desc": "Двадцать третий день. Трезубец удачи."},
    24: {"name": "День 24", "base_min": 14, "base_max": 30, "icon": "⚡", "desc": "Двадцать четвёртый день. Электричество бонусов."},
    25: {"name": "День 25 🎂", "base_min": 14, "base_max": 32, "icon": "🎂", "desc": "Серебряный юбилей! 25 дней подряд."},
    26: {"name": "День 26", "base_min": 15, "base_max": 33, "icon": "🚀", "desc": "Двадцать шестой день. Взлёт наград."},
    27: {"name": "День 27", "base_min": 15, "base_max": 34, "icon": "🌌", "desc": "Двадцать седьмой день. Космические бонусы."},
    28: {"name": "4 НЕДЕЛИ! 🌍", "base_min": 16, "base_max": 36, "icon": "🌍", "desc": "Целый месяц! Мировое достижение."},
    29: {"name": "День 29", "base_min": 17, "base_max": 38, "icon": "🔮", "desc": "Предпоследний день перед супер-наградой!"},
    30: {"name": "ДЕНЬ 30! 👑✨", "base_min": 18, "base_max": 40, "icon": "👑", "desc": "МЕГА-ДЕНЬ! Максимальная награда + Премиум ЛС на 1 день (единоразово)!", "premium_bonus": True},
}

MAX_STREAK_DAY = 30

def get_daily_bonus_info():
    text = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔥 ЕЖЕДНЕВНЫЕ НАГРАДЫ (СЕРИЯ ДО 30 ДНЕЙ)\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📐 КАК РАБОТАЕТ СИСТЕМА:\n"
        "• Заходите каждый день и забирайте бонус\n"
        "• Чем дольше серия — тем выше базовая награда\n"
        "• Размер награды зависит от дня серии и курса NBT\n"
        "• Формула: базовая награда дня × множитель курса\n"
        "• Множитель курса = 1.0 + (курс × 10 - 0.1)\n"
        "  - При курсе $0.01 → множитель ×1.0 (базовый)\n"
        "  - При курсе $0.02 → множитель ×1.1 (+10%)\n"
        "  - При курсе $0.005 → множитель ×0.95 (-5%)\n"
        "  - Диапазон: 0.5x – 1.5x\n\n"
        "⚠️ ВАЖНЫЕ ПРАВИЛА:\n"
        "• Если не забрать бонус до 00:00 МСК — серия СГОРИТ!\n"
        "• На 30-й день: единоразовый Премиум ЛС на 1 день!\n"
        "• После 30 дня награды как в 30-й день (без премиума)\n"
        "• Серия может длиться бесконечно\n\n"
        "📅 ВСЕ НАГРАДЫ ПО ДНЯМ (БАЗОВЫЕ):\n\n"
    )
    
    for day in range(1, 31):
        reward = STREAK_BASE_REWARDS[day]
        text += f"{reward['icon']} {reward['name']}: {reward['base_min']}-{reward['base_max']} 💮 (база)"
        if reward.get("premium_bonus"):
            text += " + 🎁 Премиум ЛС 1 день! (единоразово)"
        text += f"\n   {reward['desc']}\n\n"
    
    text += (
        "🎁 Как получить: кнопка «🔥 Награды» → «🎁 Забрать ежедневный бонус»\n"
        "📊 Статистика: команда /streak\n"
        "📋 Все дни: команда /streak_info"
    )
    
    return text

def get_user_bonus(streak, rate=0.01):
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

# Налоги скорректированы под новые лимиты
TRANSFER_TAX_BRACKETS = [
    {"min": 0, "max": 99, "tax_percent": 0, "name": "Без налога"},
    {"min": 100, "max": 249, "tax_percent": 3, "name": "Малый перевод"},
    {"min": 250, "max": 499, "tax_percent": 5, "name": "Средний перевод"},
    {"min": 500, "max": 999, "tax_percent": 8, "name": "Крупный перевод"},
    {"min": 1000, "max": 2499, "tax_percent": 12, "name": "Очень крупный перевод"},
    {"min": 2500, "max": 5000, "tax_percent": 15, "name": "Максимальный перевод"},
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

# ═══════════════════════════════════════════
# 🛒 ПОЛНОСТЬЮ ПЕРЕСМОТРЕННЫЕ ЦЕНЫ В USD
# ═══════════════════════════════════════════

BASE_PRICES_USD = {
    # 📝 Текстовые запросы (снижены на 50%)
    "extra5": 5, "extra10": 8, "extra50": 35,
    "unlimited_1h": 15, "unlimited_24h": 50, "unlimited_7d": 250,
    
    # 🎨 Генерация изображений (снижены на 40%)
    "image1": 8, "image5": 30, "image20": 100,
    "image_unlimited_1h": 25,
    
    # ⭐ NeBlock Premium (Новая линейка!)
    "premium_day": 100,      # 1 день
    "premium_week": 500,     # 7 дней
    "premium_30d": 1500,     # 30 дней (NEW!)
    "premium_60d": 2500,     # 60 дней (NEW!)
    "premium_90d": 3500,     # 90 дней (NEW!)
    "premium_year": 10000,   # 365 дней (NEW!)
    "premium_forever": 25000, # Навсегда
    
    # 👥 Чат (снижены на 50%)
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

Версия 5.0 (22.07.2026) 🔥 КРУПНОЕ ОБНОВЛЕНИЕ!
• Полная балансировка экономики
• Новые товары: NeBlock Premium 30/60/90 дней и на год
• Снижены лимиты для стимулирования покупок
• Уменьшены стартовые бонусы на 50%
• Пересмотрены все цены в USD
• Скорректированы ежедневные награды
• Налоги адаптированы под новую экономику
• Улучшена формула курса NBT

Версия 4.3 (22.07.2026)
• Убрано ограничение курса NBT
• Улучшена формула расчёта курса

Версия 4.2 (22.07.2026)
• Улучшенный визуал всех разделов

Версия 4.1 (22.07.2026)
• Серия до 30 дней с прогрессивными наградами

Версия 4.0 (22.07.2026)
• Улучшенная система ежедневных наград
"""

FAQ_TEXT = f"""
📚 ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ
━━━━━━━━━━━━━━━━━━━━

❓ Что такое NeBlock AI?
Платформа с собственными ИИ-моделями в Telegram:
• 💬 NeBlock AI V2 — текстовая модель
• 🎨 NeBlock Images V2 — генерация изображений

❓ Как работает экономика бота?
Внутренняя валюта — NBT токен.
• Курс обновляется каждые 4 часа по МСК
• Зависит от: предложения, активности, сжигания, дня недели
• Чем меньше токенов в обороте — тем выше курс
• Сжигание токенов повышает курс для всех

❓ Как работают ежедневные награды? 🔥
Каждый день вы получаете бонус. Размер зависит от:
  • 📅 Дня серии (чем дольше, тем выше базовая награда)
  • 💮 Курса NBT (чем выше курс, тем больше бонус)
⚠️ Не забрали до 00:00 МСК — серия СГОРИТ!

❓ Что такое NeBlock Premium? 💎
Премиум-подписка, снимающая все лимиты в ЛС.
Доступна на: 1 день, 7 дней, 30 дней, 60 дней, 90 дней, 1 год, навсегда.
• Безлимитные текстовые запросы
• Безлимитная генерация изображений
• Приоритетная обработка запросов

❓ Как заработать 💮?
  • Ежедневный бонус (растёт с серией до 30 дней!)
  • Рефералы: +{REFERRAL_BONUS} 💮 тебе, +{INVITED_BONUS} 💮 другу
  • Стартовый бонус: {START_BONUS} 💮
  • Промокоды, переводы от других пользователей

❓ Лимиты?
  • ЛС: {DAILY_LIMIT} текст + {IMAGE_DAILY_LIMIT} фото/день
  • Чаты: {CHAT_DAILY_LIMIT} текст + {CHAT_IMAGE_LIMIT} фото/день
  • Скидки обновляются каждые 2 дня в 9:00 МСК
  • NeBlock Premium снимает все лимиты в ЛС
"""

DONATE_INFO_TEXT = f"""
🌍 БЛАГОТВОРИТЕЛЬНОСТЬ
━━━━━━━━━━━━━━━━━━━━

🔥 Что такое донат?
Вы сжигаете токены NBT навсегда, уменьшая общее предложение.
Это повышает курс токена для всех пользователей!

📊 Как это работает:
  1. Отправляете команду /donate СУММА
  2. Токены безвозвратно сгорают
  3. Вы попадаете в топ благотворителей
  4. Общее предложение NBT уменьшается
  5. Курс токена растёт для всех

🏆 Топ благотворителей:
  • /donatetop — список лучших донаторов
  • 🥇🥈🥉 медали за первые 3 места

⚠️ ВАЖНО:
  • Сожжённые токены нельзя вернуть
  • Минимальный донат: {MIN_DONATION} 💮
  • Максимальный донат: {MAX_DONATION:,} 💮
  • Донаты не облагаются налогом

💡 Совет: Донатьте при низком курсе — сожжёте больше токенов!
"""

TRANSFER_INFO = f"""
💸 ПЕРЕВОДЫ 💮 NBT
━━━━━━━━━━━━━━━━━━━━

📤 СПОСОБЫ ПЕРЕВОДА:
  1. /transfer ID КОЛИЧЕСТВО
  2. @username КОЛИЧЕСТВО (в чатах)
  3. Ответ на сообщение + сумма

📊 ЛИМИТЫ:
  • Мин: {MIN_TRANSFER} 💮 | Макс: {MAX_TRANSFER:,} 💮/раз
  • Дневной лимит: {DAILY_TRANSFER_LIMIT:,} 💮

💰 НАЛОГИ:
  • 0-99 💮 → 0% | 100-249 💮 → 3%
  • 250-499 💮 → 5% | 500-999 💮 → 8%
  • 1 000-2 499 💮 → 12% | 2 500-5 000 💮 → 15%

⚠️ Налог удерживается из суммы перевода
💡 Получатель получает сумму за вычетом налога
"""

COMMANDS_LIST = """
📋 КОМАНДЫ NeBlock AI V5.0
━━━━━━━━━━━━━━━━━━━━

💬 ОСНОВНЫЕ:
/start — главное меню | /faq — вопросы
/commands — команды | /changelog — обновления

🛒 МАГАЗИН И ТОКЕНЫ:
/shop — магазин | /tokenrate — курс NBT
/discounts — скидки | /promo — промокод

🔥 НАГРАДЫ:
/streak — серия | /streak_info — все 30 дней

💸 ФИНАНСЫ:
/transfer — перевод | /donate — донат
/donatetop — топ донатов

🎨 ГЕНЕРАЦИЯ:
/genimage — изображения

👥 ЧАТЫ:
/chatowner — владельцы | /chatshop — магазин чата

💎 NEELOCK PREMIUM:
Премиум-подписка в /shop — безлимит всего!
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
    # 📝 Текстовые запросы
    "extra5": {"name": "+5 запросов", "price": 5, "icon": "📝", "category": "text", "desc": "5 дополнительных текстовых запросов.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "private"},
    "extra10": {"name": "+10 запросов", "price": 8, "icon": "📝", "category": "text", "desc": "10 дополнительных текстовых запросов.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "private"},
    "extra50": {"name": "+50 запросов", "price": 35, "icon": "📝", "category": "text", "desc": "50 дополнительных текстовых запросов.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "private"},
    "unlimited_1h": {"name": "Безлимит текста 1ч", "price": 15, "icon": "♾️", "category": "text", "desc": "Безлимитные текстовые запросы на 1 час.", "warning": "⚠️ Действует 1 час с момента покупки.", "location": "private"},
    "unlimited_24h": {"name": "Безлимит текста 24ч", "price": 50, "icon": "♾️", "category": "text", "desc": "Безлимитные текстовые запросы на 24 часа.", "warning": "⚠️ Действует 24 часа с момента покупки.", "location": "private"},
    "unlimited_7d": {"name": "Безлимит текста 7д", "price": 250, "icon": "♾️", "category": "text", "desc": "Безлимитные текстовые запросы на 7 дней.", "warning": "⚠️ Действует 7 дней с момента покупки.", "location": "private"},
    
    # 🎨 Генерация изображений
    "image1": {"name": "1 фото", "price": 8, "icon": "🎨", "category": "image", "desc": "1 генерация изображения.", "warning": "⚠️ Сгорает в 00:00 МСК.", "location": "private"},
    "image5": {"name": "5 фото", "price": 30, "icon": "🎨", "category": "image", "desc": "5 генераций изображений.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "private"},
    "image20": {"name": "20 фото", "price": 100, "icon": "🎨", "category": "image", "desc": "20 генераций изображений.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "private"},
    "image_unlimited_1h": {"name": "Безлимит фото 1ч", "price": 25, "icon": "♾️", "category": "image", "desc": "Безлимитные генерации изображений на 1 час.", "warning": "⚠️ Действует 1 час с момента покупки.", "location": "private"},
    
    # ⭐ NeBlock Premium (Новая линейка!)
    "premium_day": {"name": "Premium 1 день", "price": 100, "icon": "⭐", "category": "premium", "desc": "Полный безлимит в ЛС на 1 день.", "warning": "⚠️ Действует 24 часа.", "location": "private"},
    "premium_week": {"name": "Premium 7 дней", "price": 500, "icon": "⭐", "category": "premium", "desc": "Полный безлимит в ЛС на 7 дней.", "warning": "⚠️ Действует 7 дней.", "location": "private"},
    "premium_30d": {"name": "Premium 30 дней 🔥", "price": 1500, "icon": "💎", "category": "premium", "desc": "Полный безлимит в ЛС на 30 дней. Экономия 25%!", "warning": "⚠️ Действует 30 дней.", "location": "private"},
    "premium_60d": {"name": "Premium 60 дней 🚀", "price": 2500, "icon": "💎", "category": "premium", "desc": "Полный безлимит в ЛС на 60 дней. Экономия 37%!", "warning": "⚠️ Действует 60 дней.", "location": "private"},
    "premium_90d": {"name": "Premium 90 дней 👑", "price": 3500, "icon": "💎", "category": "premium", "desc": "Полный безлимит в ЛС на 90 дней. Экономия 50%!", "warning": "⚠️ Действует 90 дней.", "location": "private"},
    "premium_year": {"name": "Premium 1 год 💫", "price": 10000, "icon": "👑", "category": "premium", "desc": "Полный безлимит в ЛС на 365 дней. Экономия 72%!", "warning": "⚠️ Действует 365 дней.", "location": "private"},
    "premium_forever": {"name": "Premium НАВСЕГДА ✨", "price": 25000, "icon": "🌟", "category": "premium", "desc": "Полный безлимит в ЛС навсегда. Максимальная выгода!", "warning": "⚠️ Только для личных сообщений.", "location": "private"},
    
    # 👥 Чат
    "chat_extra10": {"name": "+10 запросов (чат)", "price": 8, "icon": "👥", "category": "chat", "desc": "10 доп. запросов в чатах.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "chat"},
    "chat_extra50": {"name": "+50 запросов (чат)", "price": 30, "icon": "👥", "category": "chat", "desc": "50 доп. запросов в чатах.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "chat"},
    "chat_unlimited_1h": {"name": "Безлимит чат 1ч", "price": 20, "icon": "♾️", "category": "chat", "desc": "Безлимит в чатах на 1 час.", "warning": "⚠️ Действует 1 час.", "location": "chat"},
    "chat_unlimited_24h": {"name": "Безлимит чат 24ч", "price": 75, "icon": "♾️", "category": "chat", "desc": "Безлимит в чатах на 24 часа.", "warning": "⚠️ Действует 24 часа.", "location": "chat"},
    "chat_image5": {"name": "5 фото (чат)", "price": 25, "icon": "🎨", "category": "chat_image", "desc": "5 генераций в чатах.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "chat"},
    "chat_image20": {"name": "20 фото (чат)", "price": 90, "icon": "🎨", "category": "chat_image", "desc": "20 генераций в чатах.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "chat"},
    "chat_premium_day": {"name": "Premium чат 1д", "price": 150, "icon": "⭐", "category": "chat_premium", "desc": "Безлимит в чате на 1 день.", "warning": "⚠️ Действует 24 часа.", "location": "chat"},
    "chat_premium_week": {"name": "Premium чат 7д", "price": 750, "icon": "⭐", "category": "chat_premium", "desc": "Безлимит в чате на 7 дней.", "warning": "⚠️ Действует 7 дней.", "location": "chat"},
    "chat_premium_30d": {"name": "Premium чат 30д", "price": 2500, "icon": "💎", "category": "chat_premium", "desc": "Безлимит в чате на 30 дней.", "warning": "⚠️ Действует 30 дней.", "location": "chat"},
    "chat_premium_60d": {"name": "Premium чат 60д", "price": 4000, "icon": "💎", "category": "chat_premium", "desc": "Безлимит в чате на 60 дней.", "warning": "⚠️ Действует 60 дней.", "location": "chat"},
    "chat_premium_90d": {"name": "Premium чат 90д", "price": 5500, "icon": "💎", "category": "chat_premium", "desc": "Безлимит в чате на 90 дней.", "warning": "⚠️ Действует 90 дней.", "location": "chat"},
    "chat_premium_year": {"name": "Premium чат 1 год", "price": 15000, "icon": "👑", "category": "chat_premium", "desc": "Безлимит в чате на 365 дней.", "warning": "⚠️ Действует 365 дней.", "location": "chat"},
    "chat_premium_forever": {"name": "Premium чат НАВСЕГДА", "price": 35000, "icon": "🌟", "category": "chat_premium", "desc": "Безлимит в чате навсегда.", "warning": "⚠️ Только для чатов.", "location": "chat"},
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
        
        # Базовая ставка увеличена до 0.005 для более стабильного старта
        base_rate = 0.005
        
        # Supply factor: чем меньше токенов, тем выше курс
        ideal_supply = 5000  # Снижено с 10000
        if total_tokens > 0:
            supply_ratio = ideal_supply / max(total_tokens, 1)
            supply_factor = supply_ratio ** 0.6  # Увеличена чувствительность
            supply_factor = max(0.1, min(50.0, supply_factor))
        else:
            supply_factor = 1.0
        
        # Activity factor
        if total_users > 0:
            activity_ratio = active_users / total_users
            activity_factor = 0.5 + (activity_ratio * 1.5)
        else:
            activity_factor = 1.0
        
        # Burn factor
        total_supply = total_earned + donated_total
        if total_supply > 0:
            burn_ratio = total_burned / total_supply
            burn_factor = 0.7 + (burn_ratio * 3.0)
        else:
            burn_factor = 1.0
        
        day_factor, day_name, day_icon = get_day_factor()
        
        # Volatility
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
        logger.info(f"💮 Курс: ${rate:.8f} | Блок: {block_hour}:00 | {day_name} {day_icon} | Supply: {supply_factor:.2f}")
    
    return rate_data

def get_item_price(item_id):
    rate_data = get_token_rate()
    return max(1, int(BASE_PRICES_USD.get(item_id, 10) / 100 / rate_data.get("rate", 0.005)))

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
        [InlineKeyboardButton("🔥 Награды", callback_data="earn"), InlineKeyboardButton("💮 Курс NBT", callback_data="tokenrate")],
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
    cats = {"private": [("📝 Текст", "text"), ("🎨 Фото", "image"), ("⭐ Premium", "premium")], "chat": [("👥 Запросы", "chat"), ("🖼️ Фото", "chat_image"), ("⭐ Premium", "chat_premium")]}
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
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 Забрать ежедневный бонус", callback_data="daily_bonus")],
        [InlineKeyboardButton("👥 Реферальная ссылка", callback_data="ref_link")],
        [InlineKeyboardButton("📅 Подробно о наградах", callback_data="streak_info")],
        [InlineKeyboardButton("🔙 Назад", callback_data="menu")],
    ])

def limit_reached_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Купить запросы", callback_data="shop"), InlineKeyboardButton("🔥 Награды", callback_data="earn")],
        [InlineKeyboardButton("💎 NeBlock Premium", callback_data="premium_info")]
    ])

# ═══════════════════════════════════════════
# ОБРАБОТЧИКИ КОМАНД
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
        await update.message.reply_text(
            f"🧠 NeBlock AI V{BOT_VERSION} в чате!\n\n"
            f"💬 @{context.bot.username} вопрос\n"
            f"🎨 /genimage — NeBlock Images V2\n"
            f"💸 /transfer — перевод токенов\n"
            f"🔥 /streak — ежедневные награды"
        )
        return
    premium = "💎 Активен" if is_premium(user_id) else "Не активен"
    rate_data = get_token_rate(); rate = rate_data.get("rate", 0.005)
    day_icon = rate_data.get("day_icon", "📊"); day_name = rate_data.get("day_name", "")
    next_update = rate_data.get("next_update", "")
    streak = user.get("daily_bonus_streak", 0)
    donated_total, _, _ = get_donation_stats()
    await update.message.reply_text(
        f"🧠 NeBlock AI V{BOT_VERSION}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💬 Текст | 🎨 Фото | 💸 Переводы | 🌍 Донаты\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💎 Premium: {premium}\n"
        f"💰 Баланс: {user.get('tokens', 0):,} 💮 (~${user.get('tokens', 0) * rate:.2f})\n"
        f"💮 Курс NBT: 1 NBT = ${rate:.8f}\n"
        f"📅 {day_icon} {day_name} | 🕐 Обновление: {next_update}\n"
        f"🔥 Серия бонусов: {streak} дн. | Сожжено: {donated_total:,} 💮\n"
        f"📊 Лимиты: {DAILY_LIMIT} текст + {IMAGE_DAILY_LIMIT} фото/день\n\n"
        f"👇 Выберите модель:",
        reply_markup=main_reply_keyboard()
    )

async def streak_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    streak = user.get("daily_bonus_streak", 0)
    rate_data = get_token_rate()
    rate = rate_data.get("rate", 0.005)
    
    text = f"🔥 ВАША СЕРИЯ: {streak} дн.\n━━━━━━━━━━━━━━━━\n\n"
    
    if streak == 0:
        text += "🌱 Вы ещё не начали серию!\nНачните сегодня — заберите первый бонус!\n\n"
    elif streak >= MAX_STREAK_DAY:
        text += f"👑 Максимальная серия ({MAX_STREAK_DAY} дней)!\n⚠️ Забирайте бонус каждый день до 00:00 МСК!\n\n"
    else:
        next_day = streak + 1
        if next_day <= MAX_STREAK_DAY:
            next_reward = STREAK_BASE_REWARDS[next_day]
            rate_multiplier = 1.0 + (rate * 10 - 0.1)
            rate_multiplier = max(0.5, min(1.5, rate_multiplier))
            est_min = max(1, int(next_reward["base_min"] * rate_multiplier))
            est_max = max(1, int(next_reward["base_max"] * rate_multiplier))
            text += f"➡️ Завтра день {next_day}: {next_reward['icon']} {next_reward['name']}\n"
            text += f"   База: {next_reward['base_min']}-{next_reward['base_max']} 💮\n"
            text += f"   С курсом: ~{est_min}-{est_max} 💮\n"
            if next_reward.get("premium_bonus"):
                text += "   🎁 + Премиум ЛС 1 день!\n"
            text += "\n"
    
    text += (
        "📐 ФОРМУЛА: базовая награда × множитель курса\n"
        f"💮 Текущий курс: ${rate:.8f} | Множитель: ×{1.0 + (rate * 10 - 0.1):.2f}\n\n"
        "⚠️ Не забрали до 00:00 МСК — серия СГОРИТ!\n"
        "📋 Все 30 дней: /streak_info"
    )
    
    await update.message.reply_text(text)

async def streak_info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(STREAK_INFO) > 4000:
        await update.message.reply_text(STREAK_INFO[:4000])
        await update.message.reply_text(STREAK_INFO[4000:])
    else:
        await update.message.reply_text(STREAK_INFO)

async def tokenrate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rate_data = get_token_rate(); history = load_json(TOKEN_HISTORY_FILE)
    rate = rate_data.get("rate", 0.005); supply = rate_data.get("total_supply", 0)
    market_cap = rate_data.get("market_cap", 0); donated = rate_data.get("total_donated", 0)
    burned = rate_data.get("total_burned", 0)
    day_icon = rate_data.get("day_icon", "📊"); day_name = rate_data.get("day_name", "")
    block_hour = rate_data.get("block_hour", 0); next_update = rate_data.get("next_update", "")
    updated = rate_data.get("updated_at", "")
    updated_time = datetime.fromisoformat(updated).strftime("%d.%m.%Y %H:%M") if updated else "Нет"
    change_24h = rate_data.get("change_24h", 0)
    trend = rate_data.get("trend", "📊")
    supply_factor = rate_data.get("supply_factor", 1.0)
    burn_factor = rate_data.get("burn_factor", 1.0)
    
    text = (
        f"💮 КУРС NBT ТОКЕНА\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"💰 1 NBT = ${rate:.8f}\n"
        f"💎 Капитализация: ${market_cap:,.2f}\n"
        f"{trend} Изменение 24ч: {change_24h:+.2f}%\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"📊 ФАКТОРЫ КУРСА:\n"
        f"🪙 Предложение: ×{supply_factor:.2f} (в обороте: {supply:,} NBT)\n"
        f"🔥 Сжигание: ×{burn_factor:.2f} (сожжено: {burned:,} 💮)\n"
        f"🌍 Пожертвовано: {donated:,} 💮\n"
        f"📅 День: {day_icon} {day_name}\n"
        f"🕐 Обновление: {updated_time} | След: {next_update}\n\n"
        f"💡 Курс влияет на размер ежедневных наград!\n"
        f"💡 Донаты повышают курс через сжигание!\n\n"
        f"📈 История за 7 дней:\n"
    )
    for date, h in sorted(history.items())[-7:]: 
        text += f"• {date}: ${h.get('rate', 0):.8f}\n"
    await update.message.reply_text(text)

async def donate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text(f"{DONATE_INFO_TEXT}\n\n/donate СУММА")
        return
    try: amount = int(context.args[0])
    except: await update.message.reply_text("❌ /donate СУММА"); return
    if amount < MIN_DONATION or amount > MAX_DONATION: return
    user = get_user(user_id)
    if user.get("tokens", 0) < amount: await update.message.reply_text("❌ Недостаточно!"); return
    await update.message.reply_text(
        f"🌍 ПОДТВЕРЖДЕНИЕ ДОНАТА\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"💰 Сумма: {amount:,} 💮\n"
        f"🔥 Токены сгорят НАВСЕГДА\n"
        f"💎 Баланс: {user.get('tokens', 0):,} → {user.get('tokens', 0) - amount:,} 💮\n\n"
        f"Подтвердите:",
        reply_markup=donate_confirm_keyboard(amount)
    )

async def donatetop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total, count, top_donors = get_donation_stats()
    if not top_donors: 
        await update.message.reply_text("🌍 ТОП БЛАГОТВОРИТЕЛЕЙ\n\nПока никто не делал донатов.\n/donate СУММА")
        return
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
    if not context.args: 
        await update.message.reply_text("🎨 NeBlock Images V2\n/genimage ОПИСАНИЕ")
        return
    text = " ".join(context.args)
    if not can_image_request(user_id, chat_type, chat_id): 
        await update.message.reply_text("🚫 Лимит генераций!\n💡 /shop или 💎 Premium")
        return
    msg = await update.message.reply_text("🎨 Генерирую...")
    try:
        image_bytes, error = await generate_image(text)
        if image_bytes: 
            add_image_request(user_id, chat_type)
            await msg.delete()
            await update.message.reply_photo(photo=image_bytes, caption=f"🎨 NeBlock Images V2\n📝 {text[:200]}")
        else: 
            await msg.edit_text("❌ Ошибка")
    except:
        try: await msg.delete()
        except: pass
        await update.message.reply_text("❌ Ошибка")

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
            if not to_id: await update.message.reply_text(f"❌ @{username} не найден"); return
        else: return
    else:
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(f"{TRANSFER_INFO}\n\n/transfer ID КОЛИЧЕСТВО")
            return
        try: to_id = int(context.args[0]); amount = int(context.args[1])
        except: return
    if not to_id or not amount: return
    if amount < MIN_TRANSFER or amount > MAX_TRANSFER: return
    if to_id == user_id: await update.message.reply_text("❌ Нельзя себе!"); return
    sender = get_user(user_id)
    if sender.get("daily_transfer_total", 0) + amount > DAILY_TRANSFER_LIMIT: return
    if sender.get("tokens", 0) < amount: await update.message.reply_text("❌ Недостаточно!"); return
    tax, tax_percent, tax_name = get_transfer_tax(amount)
    receiver = get_user(to_id)
    if not receiver: await update.message.reply_text("❌ Не найден!"); return
    final_amount = amount - tax
    receiver_name = receiver.get("username") or f"ID:{to_id}"
    tax_info = f"Налог: {tax} 💮 ({tax_percent}%)" if tax > 0 else "Без налога"
    await update.message.reply_text(
        f"⚠️ ПРОВЕРЬТЕ ПЕРЕВОД\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"👤 @{receiver_name} | 🆔 {to_id}\n"
        f"💸 {amount:,} 💮 | 📊 {tax_info}\n"
        f"💰 Получит: {final_amount:,} 💮\n\n"
        f"Подтвердите:",
        reply_markup=transfer_confirm_keyboard(to_id, amount)
    )

async def transfer_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["waiting_transfer"] = True
    await update.message.reply_text(f"{TRANSFER_INFO}\n\nОтправьте: ID КОЛИЧЕСТВО")

async def transfer_info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(TRANSFER_INFO)

async def discounts_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    discounts = get_discounts(); active = {k: v for k, v in discounts.items() if k not in ["last_update", "generated_at"]}
    text = f"🎫 СКИДКИ\n━━━━━━━━━━━━━━━━\n\n🔄 {get_next_update_time().strftime('%d.%m.%Y 9:00 МСК')}\n\n"
    if not active: text += "Нет активных скидок."
    else:
        for item_id, disc in sorted(active.items(), key=lambda x: x[1]["percent"], reverse=True):
            item = get_shop_items().get(item_id)
            if item: 
                text += f"{disc.get('color', '🟢')} {item['icon']} {item['name']}\n   -{disc['percent']}% = {disc['new_price']} 💮\n\n"
    await update.message.reply_text(text)

async def promo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["waiting_promo"] = True
    await update.message.reply_text("🎟 Отправьте промокод.")

async def changelog_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    await update.message.reply_text(CHANGELOG)

async def commands_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    await update.message.reply_text(COMMANDS_LIST)

async def shopdesc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    await update.message.reply_text("📋 /shop — магазин")

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
    await update.message.reply_text(f"🛒 МАГАЗИН ЧАТА\n💰 {get_tokens(user_id)} 💮", reply_markup=shop_keyboard("chat"))

# Админ
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
    await update.message.reply_text(f"📊 СТАТИСТИКА\n👥 {len(users)}\n💮 {rate_data.get('total_supply', 0):,} NBT\n🔥 {donated_total:,} 💮")

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
        rate_data = get_token_rate(); rate = rate_data.get("rate", 0.005); usd = u.get("tokens", 0) * rate
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
            f"👤 ПРОФИЛЬ\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🆔 {user_id} | 📅 {joined}\n"
            f"🔮 {cm} | 💎 {premium}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💰 Баланс: {u.get('tokens', 0):,} 💮 (~${usd:.2f})\n"
            f"💮 Курс: 1 NBT = ${rate:.8f}\n"
            f"🔥 Серия: {streak} дн.\n"
            f"💎 Заработано: {u.get('earned_tokens', 0):,} | Потрачено: {u.get('spent_tokens', 0):,}\n"
            f"🌍 Донатов: {u.get('donated_tokens', 0):,} 💮\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📊 СЕГОДНЯ:\n"
            f"💬 Текст: {u.get('requests_today', 0)}/{DAILY_LIMIT + u.get('extra_requests', 0)} | {fmt(u.get('unlimited_until'))}\n"
            f"🎨 Фото: {u.get('image_requests_today', 0)}/{IMAGE_DAILY_LIMIT + u.get('extra_image_requests', 0)} | {fmt(u.get('image_unlimited_until'))}\n"
            f"👥 Чаты: {u.get('chat_requests_today', 0)}/{CHAT_DAILY_LIMIT + u.get('extra_chat_requests', 0)}\n"
            f"💸 Переводов: {u.get('daily_transfer_total', 0)} 💮\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📈 ВСЕГО: 💬{u.get('total_requests', 0):,} | 🎨{u.get('total_images', 0):,}\n"
            f"🛡 {u.get('warnings', 0)}/5 | 👥 {u.get('referrals', 0)} | 🕐 {last}",
            reply_markup=main_menu()
        )
        return True
    
    if text == "🛒 Магазин": 
        await update.message.reply_text(f"🛒 МАГАЗИН\n━━━━━━━━━━━━━━━━\n💰 {get_tokens(user_id)} 💮\n\nВыберите категорию:", reply_markup=shop_keyboard("private"))
        return True
    
    if text == "🔥 Награды": 
        user = get_user(user_id); streak = user.get("daily_bonus_streak", 0)
        await update.message.reply_text(
            f"🔥 НАГРАДЫ\n━━━━━━━━━━━━━━━━\n\n📊 Серия: {streak} дн.\n💰 Баланс: {get_tokens(user_id)} 💮\n\nВыберите действие:",
            reply_markup=earn_keyboard()
        )
        return True
    
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
    shop_items = get_shop_items()
    
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
            sender = get_user(user_id)
            if sender.get("tokens", 0) < amount: await query.edit_message_text("❌ Недостаточно!"); return
            tax, tax_percent, _ = get_transfer_tax(amount)
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
    
    if data == "streak_info":
        user = get_user(user_id); streak = user.get("daily_bonus_streak", 0)
        rate_data = get_token_rate(); rate = rate_data.get("rate", 0.005)
        text = (
            f"📅 ПОДРОБНО О НАГРАДАХ\n"
            f"━━━━━━━━━━━━━━━━\n\n"
            f"📊 Серия: {streak} дн. | 💮 Курс: ${rate:.8f}\n"
            f"📈 Множитель: ×{1.0 + (rate * 10 - 0.1):.2f}\n\n"
            f"📐 Формула: база дня × множитель курса\n"
            f"⚠️ Не забрали до 00:00 МСК — серия СГОРИТ!\n"
            f"👑 30-й день: Премиум ЛС 1 день (единоразово)\n\n"
            f"📅 ВСЕ 30 ДНЕЙ (БАЗА):\n\n"
        )
        for day in range(1, 31):
            reward = STREAK_BASE_REWARDS[day]
            text += f"{reward['icon']} {reward['name']}: {reward['base_min']}-{reward['base_max']} 💮"
            if reward.get("premium_bonus"): text += " + 🎁 Премиум"
            text += f"\n   {reward['desc']}\n\n"
        
        if len(text) > 4000:
            await query.edit_message_text(text[:4000], reply_markup=back_button())
            await context.bot.send_message(chat_id=query.message.chat_id, text=text[4000:], reply_markup=back_button())
        else:
            await query.edit_message_text(text, reply_markup=back_button())
        return
    
    if data == "menu": 
        await query.edit_message_text(f"🧠 NeBlock AI V{BOT_VERSION}\n━━━━━━━━━━━━━━━━\n\n💰 {get_tokens(user_id):,} 💮\n\nВыберите раздел:", reply_markup=main_menu())
        return
    
    if data == "about": 
        await query.edit_message_text(
            f"ℹ️ О БОТЕ NeBlock AI\n"
            f"━━━━━━━━━━━━━━━━\n\n"
            f"📌 Версия: {BOT_VERSION}\n\n"
            f"💬 NeBlock AI V2 — текстовая модель\n"
            f"🎨 NeBlock Images V2 — генерация изображений\n"
            f"💸 Переводы | 🌍 Донаты | 🔥 Награды\n"
            f"💮 Валюта NBT с рыночным курсом\n"
            f"💎 NeBlock Premium — безлимитная подписка\n\n"
            f"📊 Лимиты ЛС: {DAILY_LIMIT} текст + {IMAGE_DAILY_LIMIT} фото/день\n"
            f"📊 Лимиты чатов: {CHAT_DAILY_LIMIT} текст + {CHAT_IMAGE_LIMIT} фото/день\n\n"
            f"💡 Используйте /faq для ответов на вопросы",
            reply_markup=back_button()
        )
        return
    
    if data == "donate_info": await query.edit_message_text(DONATE_INFO_TEXT, reply_markup=back_button()); return
    
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
            f"💰 1 NBT = ${rd.get('rate', 0.005):.8f}\n"
            f"💎 Кап: ${rd.get('market_cap', 0):,.2f}\n"
            f"🪙 В обороте: {rd.get('total_supply', 0):,} NBT\n"
            f"🔥 Сожжено: {rd.get('total_donated', 0):,} 💮\n"
            f"📊 Supply: ×{rd.get('supply_factor', 1):.2f} | Burn: ×{rd.get('burn_factor', 1):.2f}\n"
            f"{rd.get('day_icon', '📊')} {rd.get('day_name', '')} | 🔄 {rd.get('next_update', '')}\n\n"
            f"💡 Донаты повышают курс!",
            reply_markup=back_button()
        )
        return
    
    if data == "transfer": 
        context.user_data["waiting_transfer"] = True
        await query.edit_message_text(f"{TRANSFER_INFO}\n\nОтправьте: ID КОЛИЧЕСТВО", reply_markup=back_button())
        return
    
    if data == "commands": await query.edit_message_text(COMMANDS_LIST, reply_markup=back_button()); return
    if data == "changelog": await query.edit_message_text(CHANGELOG, reply_markup=back_button()); return
    
    if data == "discounts_info":
        discounts = get_discounts(); active = {k: v for k, v in discounts.items() if k not in ["last_update", "generated_at"]}
        text = "🎫 СКИДКИ\n\n"
        if not active: text += "Нет активных."
        else:
            for item_id, disc in sorted(active.items(), key=lambda x: x[1]["percent"], reverse=True):
                item = shop_items.get(item_id)
                if item: text += f"{disc.get('color', '🟢')} {item['icon']} {item['name']}\n🔥 -{disc['percent']}% = {disc['new_price']} 💮\n\n"
        await query.edit_message_text(text, reply_markup=back_button())
        return
    
    if data == "premium_info": 
        await query.edit_message_text(
            f"💎 NeBlock Premium\n━━━━━━━━━━━━━━━━\n\n"
            f"Премиум-подписка снимает все лимиты в ЛС:\n"
            f"• Безлимитные текстовые запросы\n"
            f"• Безлимитная генерация фото\n\n"
            f"🛒 ДОСТУПНЫЕ ТАРИФЫ:\n"
            f"⭐ 1 день — {shop_items.get('premium_day', {}).get('price', '?')} 💮\n"
            f"⭐ 7 дней — {shop_items.get('premium_week', {}).get('price', '?')} 💮\n"
            f"💎 30 дней — {shop_items.get('premium_30d', {}).get('price', '?')} 💮 (экономия 25%)\n"
            f"🚀 60 дней — {shop_items.get('premium_60d', {}).get('price', '?')} 💮 (экономия 37%)\n"
            f"👑 90 дней — {shop_items.get('premium_90d', {}).get('price', '?')} 💮 (экономия 50%)\n"
            f"💫 1 год — {shop_items.get('premium_year', {}).get('price', '?')} 💮 (экономия 72%)\n"
            f"🌟 Навсегда — {shop_items.get('premium_forever', {}).get('price', '?')} 💮\n\n"
            f"💡 30-й день серии даёт Premium 1 день!",
            reply_markup=back_button()
        )
        return
    
    if data == "stats":
        u = get_user(user_id)
        await query.edit_message_text(
            f"📊 СТАТИСТИКА\n━━━━━━━━━━━━━━━━\n\n"
            f"💬 Запросов: {u.get('requests_today', 0)}\n"
            f"🎨 Генераций: {u.get('image_requests_today', 0)}\n"
            f"💰 Баланс: {u.get('tokens', 0):,} 💮\n"
            f"🔥 Серия: {u.get('daily_bonus_streak', 0)} дн.\n"
            f"🌍 Донатов: {u.get('donated_tokens', 0):,} 💮\n"
            f"👥 Рефералов: {u.get('referrals', 0)}",
            reply_markup=back_button()
        )
        return
    
    if data == "shop": 
        await query.edit_message_text(f"🛒 МАГАЗИН\n━━━━━━━━━━━━━━━━\n💰 {get_tokens(user_id):,} 💮\n\nВыберите категорию:", reply_markup=shop_keyboard("private"))
        return
    
    if data == "earn": 
        user = get_user(user_id); streak = user.get("daily_bonus_streak", 0)
        text = f"🔥 НАГРАДЫ\n━━━━━━━━━━━━━━━━\n\n📊 Серия: {streak} дн.\n💰 Баланс: {get_tokens(user_id):,} 💮\n\nВыберите действие:"
        await query.edit_message_text(text, reply_markup=earn_keyboard())
        return
    
    if data == "promo": 
        context.user_data["waiting_promo"] = True
        await query.edit_message_text("🎟 Отправьте промокод.", reply_markup=back_button())
        return
    
    if data == "faq": 
        await query.edit_message_text(FAQ_TEXT[:4000], reply_markup=back_button())
        return
    
    if data == "daily_bonus":
        u = get_user(user_id); today = datetime.now().strftime("%Y-%m-%d")
        if u.get("daily_bonus_claimed") == today:
            await query.answer("❌ Уже забирали сегодня!", show_alert=True)
        else:
            users = load_users(); uid = str(user_id)
            users[uid]["daily_bonus_claimed"] = today
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            
            if users[uid].get("last_bonus_date") == yesterday:
                users[uid]["daily_bonus_streak"] = users[uid].get("daily_bonus_streak", 0) + 1
            elif users[uid].get("last_bonus_date") != today:
                users[uid]["daily_bonus_streak"] = 1
            
            users[uid]["last_bonus_date"] = today
            streak = users[uid]["daily_bonus_streak"]
            
            rate_data = get_token_rate()
            rate = rate_data.get("rate", 0.005)
            bonus, icon, day_name, premium_bonus, rate_multiplier = get_user_bonus(streak, rate)
            
            if premium_bonus and users[uid].get("streak_30_premium_claimed"):
                premium_bonus = False
            
            save_users(users)
            add_tokens(user_id, bonus)
            
            premium_text = ""
            if premium_bonus and not users[uid].get("streak_30_premium_claimed"):
                users = load_users()
                existing = users[uid].get("premium_until")
                base = datetime.fromisoformat(existing) if existing and datetime.now() < datetime.fromisoformat(existing) else datetime.now()
                users[uid]["premium_until"] = (base + timedelta(hours=24)).isoformat()
                users[uid]["streak_30_premium_claimed"] = True
                save_users(users)
                premium_text = "\n🎁 + Premium ЛС 1 день!"
            
            rate_info = f"\n📈 Множитель курса: ×{rate_multiplier:.2f}" if abs(rate_multiplier - 1.0) > 0.01 else ""
            
            await query.answer(f"🎉 +{bonus} 💮!", show_alert=True)
            await query.edit_message_text(
                f"🎁 БОНУС ПОЛУЧЕН!\n━━━━━━━━━━━━━━━━\n\n"
                f"{icon} {day_name}\n"
                f"💰 +{bonus} 💮{premium_text}{rate_info}\n"
                f"💎 Баланс: {get_tokens(user_id):,} 💮\n"
                f"🔥 Серия: {streak} дн.\n\n"
                f"⚠️ Заберите завтра до 00:00 МСК!",
                reply_markup=back_button()
            )
        return
    
    if data == "ref_link":
        user = get_user(user_id); bot_username = (await context.bot.get_me()).username
        await query.edit_message_text(
            f"👥 РЕФЕРАЛЫ\n━━━━━━━━━━━━━━━━\n\n"
            f"🔗 https://t.me/{bot_username}?start=ref_{user.get('referral_code', '')}\n\n"
            f"💰 Вы: +{REFERRAL_BONUS} 💮 | Друг: +{INVITED_BONUS} 💮\n"
            f"📊 Рефералов: {user.get('referrals', 0)}",
            reply_markup=back_button()
        )
        return
    
    if data.startswith("confirm_"):
        item_id = data.replace("confirm_", ""); item = shop_items.get(item_id)
        if not item: return
        price, percent, disc = get_discounted_price(item_id)
        tokens = get_tokens(user_id)
        if tokens < price: await query.answer("❌ Недостаточно!", show_alert=True); return
        remove_tokens(user_id, price); users = load_users(); uid = str(user_id)
        
        # Стандартные действия
        actions = {
            "extra5": ("extra_requests", 5), "extra10": ("extra_requests", 10), "extra50": ("extra_requests", 50),
            "image1": ("extra_image_requests", 1), "image5": ("extra_image_requests", 5), "image20": ("extra_image_requests", 20),
            "chat_extra10": ("extra_chat_requests", 10), "chat_extra50": ("extra_chat_requests", 50),
            "chat_image5": ("extra_chat_image_requests", 5), "chat_image20": ("extra_chat_image_requests", 20),
        }
        time_actions = {
            "unlimited_1h": ("unlimited_until", 1), "unlimited_24h": ("unlimited_until", 24), "unlimited_7d": ("unlimited_until", 168),
            "image_unlimited_1h": ("image_unlimited_until", 1),
            "chat_unlimited_1h": ("chat_unlimited_until", 1), "chat_unlimited_24h": ("chat_unlimited_until", 24),
        }
        premium_actions = {
            "premium_day": 1, "premium_week": 7, "premium_30d": 30, "premium_60d": 60,
            "premium_90d": 90, "premium_year": 365, "premium_forever": 36500,
            "chat_premium_day": 1, "chat_premium_week": 7, "chat_premium_30d": 30,
            "chat_premium_60d": 60, "chat_premium_90d": 90, "chat_premium_year": 365, "chat_premium_forever": 36500,
        }
        
        if item_id in actions:
            field, amount = actions[item_id]
            users[uid][field] = users[uid].get(field, 0) + amount
        elif item_id in time_actions:
            field, hours = time_actions[item_id]
            users[uid][field] = (datetime.now() + timedelta(hours=hours)).isoformat()
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
        dt = f"\n🎫 -{percent}%" if percent > 0 else ""
        if disc and disc.get("type") == "legendary": dt = "\n🌟 ЛЕГЕНДАРНАЯ!"
        await query.answer(f"✅ {item['name']}!", show_alert=True)
        await query.edit_message_text(f"✅ {item['name']}{dt}\n💰 Потрачено: {price} 💮\n💎 Остаток: {get_tokens(user_id):,} 💮", reply_markup=back_button())
        return
    
    if data.startswith("buy_"):
        item_id = data.replace("buy_", ""); item = shop_items.get(item_id)
        if not item: return
        price, percent, disc = get_discounted_price(item_id)
        tokens = get_tokens(user_id); can = "✅ Хватает" if tokens >= price else "❌ Не хватает"
        dt = ""
        if percent > 0 and disc:
            if disc.get("type") == "legendary": dt = "\n\n🌟 БЕСПЛАТНО!"
            else: dt = f"\n\n{disc.get('color', '🟢')} -{percent}%\n💵 {disc['original']} → 🔥 {price} 💮"
        await query.edit_message_text(
            f"🛒 {item['icon']} {item['name']}\n━━━━━━━━━━━━━━━━\n\n"
            f"📝 {item['desc']}\n⚠️ {item.get('warning', '')}{dt}\n\n"
            f"💎 Баланс: {tokens} 💮\n{can}",
            reply_markup=confirm_keyboard(item_id)
        )
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
                    should_respond = True
                    if is_image: is_image_request = True; text = clean_text
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
    
    if is_image_request or (chat_type == "private" and (user.get("current_model") == "image" or user.get("waiting_for_image"))):
        if chat_type == "private": users = load_users(); users[str(user_id)]["waiting_for_image"] = False; save_users(users)
        if not can_image_request(user_id, chat_type, chat_id):
            await update.message.reply_text("🚫 Лимит фото!", reply_markup=limit_reached_keyboard() if chat_type == "private" else None)
            return
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
    
    if not can_request(user_id, chat_type, chat_id):
        await update.message.reply_text("🚫 Лимит!", reply_markup=limit_reached_keyboard() if chat_type == "private" else None)
        return
    
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
