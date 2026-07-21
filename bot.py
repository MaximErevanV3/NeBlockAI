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
# 🧠 NeBlock AI V3.7 - Конфигурация
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
DAILY_BONUS_MIN = 5
DAILY_BONUS_MAX = 15
REFERRAL_BONUS = 25
INVITED_BONUS = 10
BOT_VERSION = "3.7"

MIN_TRANSFER = 1
MAX_TRANSFER = 10000
DAILY_TRANSFER_LIMIT = 50000
MIN_DONATION = 1
MAX_DONATION = 100000

TRANSFER_TAX_BRACKETS = [
    {"min": 0, "max": 199, "tax_percent": 0, "name": "Без налога"},
    {"min": 200, "max": 499, "tax_percent": 3, "name": "Малый перевод"},
    {"min": 500, "max": 999, "tax_percent": 5, "name": "Средний перевод"},
    {"min": 1000, "max": 2499, "tax_percent": 8, "name": "Крупный перевод"},
    {"min": 2500, "max": 4999, "tax_percent": 12, "name": "Очень крупный перевод"},
    {"min": 5000, "max": 10000, "tax_percent": 15, "name": "Максимальный перевод"},
]

TRANSFER_WARNING = """
⚠️ ВНИМАНИЕ! ПРОВЕРЬТЕ ДАННЫЕ ПЕРЕВОДА!
━━━━━━━━━━━━━━━━━━━━

Убедитесь что получатель указан верно!
Если вы отправите токены не тому пользователю — вернуть их будет НЕВОЗМОЖНО!
Транзакции в блокчейне NeBlock необратимы.
"""

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

# ═══════════════════════════════════════════
# 📚 МАКСИМАЛЬНО ПОДРОБНЫЙ FAQ
# ═══════════════════════════════════════════

FAQ_TEXT = f"""
📚 ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ
━━━━━━━━━━━━━━━━━━━━

═══════════════════════════════════════
❓ ЧТО ТАКОЕ NeBlock AI?
═══════════════════════════════════════

NeBlock AI — это передовая платформа искусственного интеллекта, работающая прямо в Telegram. Платформа объединяет две мощные нейросети для решения широкого спектра задач.

💬 NeBlock AI V2 — ТЕКСТОВАЯ МОДЕЛЬ
Назначение: ответы на вопросы, написание кода, объяснение сложных тем, переводы, помощь с учёбой.
• Качество ответов улучшено на 40%
• Скорость генерации увеличена в 2 раза (2-5 секунд)
• Контекст диалога расширен до 8000 токенов
• Поддержка 50+ языков с автоопределением
• Многошаговые инструкции
• Работает в ЛС и чатах

🎨 NeBlock Images V2 — ГЕНЕРАЦИЯ ФОТО
Назначение: создание уникальных изображений по текстовому описанию.
• Качество изображений повышено на 50%
• Разные стили: реализм, аниме, арт, 3D, скетч
• Размер: 1024x1024 пикселей
• Скорость генерации до 15 секунд
• Каждое изображение уникально
• Работает в ЛС и чатах

═══════════════════════════════════════
❓ КАК ПОЛЬЗОВАТЬСЯ БОТОМ?
═══════════════════════════════════════

1. В ЛИЧНЫХ СООБЩЕНИЯХ (ЛС):
• Напишите вопрос в чат — бот ответит
• Кнопки внизу для навигации
• 💬 NeBlock AI V2 — текстовая модель
• 🎨 NeBlock Images V2 — генерация фото
• 👤 Профиль — статистика и баланс
• 🛒 Магазин — покупка запросов и Премиума
• 💰 Заработать — бонусы и рефералы
• 💸 Перевод — отправить токены
• 🌍 Донат — сжечь токены (благотворительность)
• 🎫 Скидки — активные скидки
• 💮 Курс NBT — токеномика

2. В ЧАТАХ И ГРУППАХ:
• @имя_бота вопрос — текстовый ответ
• @имя_бота нарисуй описание — фото
• нарисуй описание — фото (ключевое слово)
• /genimage описание — фото (команда)
• /transfer @username СУММА — перевод
• Бот реагирует только на обращения
• Обычные сообщения игнорируются

3. КОМАНДЫ:
/start — главное меню
/shop — магазин товаров
/faq — этот раздел
/discounts — активные скидки
/tokenrate — курс 💮 NBT
/transfer — перевод токенов
/transferinfo — о переводах и налогах
/donate — благотворительность
/donatetop — топ благотворителей
/genimage — генерация фото
/changelog — история обновлений
/promo — активация промокода
/commands — все команды

═══════════════════════════════════════
❓ КАКИЕ ЛИМИТЫ И ЗАЧЕМ ОНИ?
═══════════════════════════════════════

Лимиты обеспечивают стабильную работу нейросети для всех пользователей.

📊 ЛИМИТЫ В ЛС:
• {DAILY_LIMIT} текстовых вопросов в день
• {IMAGE_DAILY_LIMIT} генераций фото в день
• Сброс в 00:00 МСК каждый день
• Неиспользованные запросы НЕ переносятся

📊 ЛИМИТЫ В ЧАТАХ:
• {CHAT_DAILY_LIMIT} текстовых вопросов в день (на весь чат)
• {CHAT_IMAGE_LIMIT} генераций фото в день (на весь чат)
• Сброс в 00:00 МСК

⚠️ ВАЖНО:
• Доп. запросы из магазина СГОРАЮТ при сбросе
• Безлимиты действуют точное время и НЕ сгорают
• Премиум отключает все лимиты
• Покупайте доп. запросы только на сегодня
• Для долгосрочного использования — безлимиты или Премиум

═══════════════════════════════════════
❓ ЧТО ТАКОЕ 💮 NBT И КАК РАБОТАЕТ КУРС?
═══════════════════════════════════════

💮 NeBlock Token (NBT) — внутренняя валюта платформы.
• Тикер: NBT | Символ: 💮
• Курс обновляется каждые 4 часа
• Не продаётся за реальные деньги
• Можно только заработать

ФАКТОРЫ КУРСА:
1. Предложение (supply): чем больше токенов — тем выше курс
2. Активность: чем активнее пользователи — тем выше курс
3. Сжигание (burn): налоги и донаты повышают курс
4. Волатильность: исторические колебания
5. Рыночный шум: случайные колебания ±8%

ФОРМУЛА КУРСА:
rate = $0.01 × supply_factor × activity_factor × burn_factor × volatility × market_noise

Рыночная капитализация = общее_количество × курс
Изменение за 24ч = (текущий - вчера) / вчера × 100%

Где посмотреть: /tokenrate или кнопка "💮 Курс NBT"

═══════════════════════════════════════
❓ КАК ЗАРАБОТАТЬ 💮 NBT?
═══════════════════════════════════════

1. ЕЖЕДНЕВНЫЙ БОНУС:
• {DAILY_BONUS_MIN}-{DAILY_BONUS_MAX} 💮 каждый день
• Кнопка "💰 Заработать" → "🎁 Ежедневный бонус"
• Серия бонусов (стрик) увеличивается
• При пропуске дня серия сбрасывается

2. РЕФЕРАЛЬНАЯ ПРОГРАММА:
• Пригласите друга по ссылке
• Вы получаете +{REFERRAL_BONUS} 💮
• Друг получает +{INVITED_BONUS} 💮
• Количество рефералов не ограничено

3. СТАРТОВЫЙ БОНУС:
• {START_BONUS} 💮 при первом запуске
• Начисляется автоматически

4. ПРОМОКОДЫ:
• Создаёт администратор
• Вводите в разделе "🎟 Промокод"
• Один код — одно использование

5. ПЕРЕВОДЫ ОТ ДРУГИХ:
• Пользователи могут отправить вам 💮
• Работает в ЛС и чатах

═══════════════════════════════════════
❓ КАК РАБОТАЮТ СКИДКИ?
═══════════════════════════════════════

Скидки обновляются каждые 2 дня в 9:00 МСК.

ТИПЫ СКИДОК (от частых к редким):
🟢 Обычная (5-25%) — шанс 40%
🔴 Супер (30-50%) — шанс 20%
📦 Набор (15-35%) — шанс 12%
⚡ Флеш (40-70%, 24 часа) — шанс 8%
💎 Премиум (10-30%) — шанс 5%
🌟 ЛЕГЕНДАРНАЯ (100%, 3 часа) — шанс 0.5%

Скидки применяются автоматически в магазине.
Просмотр: /discounts или кнопка "🎫 Скидки"

═══════════════════════════════════════
❓ ЧТО ТАКОЕ ПРЕМИУМ?
═══════════════════════════════════════

Премиум полностью отключает все лимиты.

💎 ПРЕМИУМ ЛС:
• Безлимит текста и фото в личных сообщениях
• Сроки: 1 день, 7 дней, навсегда

💎 ПРЕМИУМ ЧАТ:
• Безлимит для всех участников чата
• Покупает владелец чата
• Сроки: 1 день, 7 дней, навсегда

Премиум навсегда — самая выгодная покупка!

═══════════════════════════════════════
❓ КАК РАБОТАЮТ ПЕРЕВОДЫ?
═══════════════════════════════════════

💸 СПОСОБЫ ПЕРЕВОДА:
1. ЛС: /transfer ID КОЛИЧЕСТВО
2. Чат (reply): ответ + /transfer КОЛИЧЕСТВО
3. Чат (@username): /transfer @username КОЛИЧЕСТВО
4. Кнопка "💸 Перевод"

⚠️ Проверяйте ID получателя! Ошибка = потеря токенов!

📊 ЛИМИТЫ:
• {MIN_TRANSFER}-{MAX_TRANSFER} 💮 за раз
• {DAILY_TRANSFER_LIMIT} 💮 в день

💰 НАЛОГИ:
• 1-199 💮 — 0% (без налога)
• 200-499 💮 — 3%
• 500-999 💮 — 5%
• 1,000-2,499 💮 — 8%
• 2,500-4,999 💮 — 12%
• 5,000-10,000 💮 — 15%

Налоги сжигаются и повышают курс 💮!

═══════════════════════════════════════
❓ ЧТО ТАКОЕ БЛАГОТВОРИТЕЛЬНОСТЬ? 🌍
═══════════════════════════════════════

Вы можете добровольно сжечь свои токены навсегда!
Это уменьшает предложение NBT и повышает курс для всех.

🌍 КАК ЭТО РАБОТАЕТ:
• /donate СУММА — сжечь токены
• Токены навсегда удаляются из экономики
• Уменьшение предложения повышает курс
• Вы получаете признание в топе благотворителей

🏆 ТОП БЛАГОТВОРИТЕЛЕЙ:
• /donatetop — рейтинг донатов
• Медали: 🥇🥈🥉
• Статистика в профиле

💡 Донаты учитываются в курсе NBT!
Чем больше сожжено — тем выше курс для всех.

═══════════════════════════════════════
❓ КАК ГЕНЕРИРОВАТЬ ФОТО В ЧАТАХ?
═══════════════════════════════════════

Три способа:
1. @бот нарисуй описание
2. нарисуй описание (ключевое слово)
3. /genimage описание (специальная команда)

═══════════════════════════════════════
❓ БОТ ПОМНИТ ИСТОРИЮ? ЯЗЫКИ? ПРОБЛЕМЫ?
═══════════════════════════════════════

• Да, текстовая модель учитывает контекст диалога
• 50+ языков с автоматическим определением
• При проблемах: проверьте интернет, /start, лимиты
• /changelog — история обновлений
"""

# ═══════════════════════════════════════════
# 📋 ПОЛНЫЙ СПИСОК КОМАНД
# ═══════════════════════════════════════════

COMMANDS_LIST = """
📋 КОМАНДЫ NeBlock AI V3.7
━━━━━━━━━━━━━━━━━━━━

ОБЫЧНЫЕ КОМАНДЫ:
/start — главное меню и приветствие
/shop — магазин товаров за 💮
/shopdesc — подробное описание всех товаров
/faq — ответы на частые вопросы
/discounts — активные скидки и время обновления
/tokenrate — курс 💮 NBT и токеномика
/transfer — перевод токенов другому пользователю
/transferinfo — информация о переводах и налогах
/donate — благотворительность (сжигание токенов)
/donatetop — топ благотворителей
/genimage — генерация фото по описанию
/changelog — история всех обновлений
/promo — активация промокода
/commands — этот список команд

👥 КОМАНДЫ ДЛЯ ЧАТОВ:
/chatowner — посмотреть владельцев чата
/chatshop — магазин для чата (для владельцев)
"""

# ═══════════════════════════════════════════
# 🌍 ИНФОРМАЦИЯ О БЛАГОТВОРИТЕЛЬНОСТИ
# ═══════════════════════════════════════════

DONATE_INFO_TEXT = f"""
🌍 БЛАГОТВОРИТЕЛЬНОСТЬ В NeBlock AI
━━━━━━━━━━━━━━━━━━━━

Благотворительность в NeBlock AI — это механизм добровольного сжигания токенов NBT. Когда вы делаете донат, ваши токены навсегда удаляются из экономики платформы.

📋 КАК ЭТО РАБОТАЕТ:
1. Вы решаете сколько токенов хотите сжечь
2. Используете команду /donate СУММА
3. Токены списываются с вашего баланса
4. Токены навсегда удаляются из оборота
5. Общее предложение NBT уменьшается
6. Курс NBT растёт для всех держателей

💡 ЗАЧЕМ ЭТО НУЖНО:
• Уменьшение предложения повышает ценность NBT
• Поддержка экосистемы платформы
• Признание в топе благотворителей
• Вклад в развитие проекта

📊 СТАТИСТИКА:
• Всего сожжено: {sum(d.get('amount', 0) for d in load_json(DONATION_FILE).get('donations', [])):,} 💮
• Количество донатов: {len(load_json(DONATION_FILE).get('donations', []))}

🏆 КОМАНДЫ:
/donate СУММА — сделать донат
/donatetop — топ благотворителей

⚠️ ВНИМАНИЕ: Сожжённые токены нельзя вернуть!
"""

# ═══════════════════════════════════════════
# 💸 ИНФОРМАЦИЯ О ПЕРЕВОДАХ
# ═══════════════════════════════════════════

TRANSFER_INFO = f"""
💸 ПЕРЕВОДЫ 💮 NBT
━━━━━━━━━━━━━━━━━━━━

Система переводов позволяет отправлять токены NBT другим пользователям платформы.

📋 СПОСОБЫ ПЕРЕВОДА:
1. В ЛС: /transfer ID КОЛИЧЕСТВО
   Пример: /transfer 1671403667 100
   Узнать свой ID можно в профиле (кнопка 👤 Профиль)

2. В ЧАТЕ (ответ на сообщение):
   Ответьте на сообщение пользователя (Reply)
   Напишите: /transfer КОЛИЧЕСТВО
   Пример: /transfer 100

3. В ЧАТЕ (по @username):
   /transfer @username КОЛИЧЕСТВО
   Пример: /transfer @user 100

4. Через кнопку "💸 Перевод" в меню

⚠️ ВНИМАНИЕ:
• Проверяйте ID получателя перед отправкой!
• Если отправите не тому — токены не вернуть!
• Транзакции в блокчейне NeBlock необратимы
• Не отправляйте токены незнакомым пользователям

📊 ЛИМИТЫ ПЕРЕВОДОВ:
• Минимальная сумма: {MIN_TRANSFER} 💮
• Максимальная за раз: {MAX_TRANSFER} 💮
• Максимальная в день: {DAILY_TRANSFER_LIMIT} 💮
• Дневной лимит сбрасывается в 00:00 МСК

💰 НАЛОГИ НА ПЕРЕВОДЫ:
Налог взимается с отправителя. Собранные налоги сжигаются.

Ставки:
• 1-199 💮 — 0% (без налога)
• 200-499 💮 — 3% (малый перевод)
• 500-999 💮 — 5% (средний перевод)
• 1,000-2,499 💮 — 8% (крупный перевод)
• 2,500-4,999 💮 — 12% (очень крупный)
• 5,000-10,000 💮 — 15% (максимальный)

Примеры:
• 100 💮 → получатель получит 100 💮 (налог 0)
• 300 💮 → получатель получит 291 💮 (налог 9)
• 1,000 💮 → получатель получит 920 💮 (налог 80)
• 5,000 💮 → получатель получит 4,250 💮 (налог 750)

💡 Налоги сжигаются и повышают курс NBT для всех!
"""

# ═══════════════════════════════════════════
# 💮 ИНФОРМАЦИЯ О КУРСЕ NBT
# ═══════════════════════════════════════════

TOKEN_RATE_INFO = """
💮 КУРС NeBlock Token (NBT)
━━━━━━━━━━━━━━━━━━━━

NBT — внутренняя валюта платформы с динамическим курсом.

ОСНОВНЫЕ ХАРАКТЕРИСТИКИ:
• Тикер: NBT
• Символ: 💮
• Курс: обновляется каждые 4 часа
• Не продаётся за реальные деньги
• Можно только заработать
• Нельзя вывести или обменять

ФАКТОРЫ КУРСА:

1. ПРЕДЛОЖЕНИЕ (Supply Factor):
Коэффициент: 0.3 - 3.0
Чем больше токенов в обороте — тем выше курс.
При 500 токенах: фактор = 3.0 (максимальный)
При 50,000 токенах: фактор = 0.3 (минимальный)

2. АКТИВНОСТЬ (Activity Factor):
Коэффициент: 0.7 - 1.3
Отношение активных пользователей к общему числу.
При 100% активности: фактор = 1.3

3. СЖИГАНИЕ (Burn Factor):
Коэффициент: 0.8 - 1.2
Налоги с переводов и донаты сжигаются.
Чем больше сожжено — тем выше курс.

4. ВОЛАТИЛЬНОСТЬ (Volatility Index):
Коэффициент: 1.0 - 1.5
Анализ колебаний за последние 30 дней.

5. РЫНОЧНЫЙ ШУМ (Market Noise):
Диапазон: ±8%
Случайный фактор для реалистичности.

ИТОГОВАЯ ФОРМУЛА:
rate = $0.01 × supply × activity × burn × volatility × noise

РЫНОЧНАЯ КАПИТАЛИЗАЦИЯ:
market_cap = общее_количество_токенов × текущий_курс

ИЗМЕНЕНИЕ ЗА 24 ЧАСА:
change_24h = (текущий - вчерашний) / вчерашний × 100%

Просмотр: /tokenrate или кнопка "💮 Курс NBT"
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
    "extra5": {"name": "+5 запросов", "price": 10, "icon": "📝", "category": "text", "desc": "5 запросов.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "private", "usage": "В ЛС."},
    "extra10": {"name": "+10 запросов", "price": 18, "icon": "📝", "category": "text", "desc": "10 запросов.", "warning": "⚠️ Сгорают.", "location": "private", "usage": "В ЛС."},
    "extra50": {"name": "+50 запросов", "price": 80, "icon": "📝", "category": "text", "desc": "50 запросов.", "warning": "⚠️ Сгорают.", "location": "private", "usage": "Активно."},
    "unlimited_1h": {"name": "Безлимит 1ч", "price": 30, "icon": "♾️", "category": "text", "desc": "Безлимит 1ч.", "warning": "⚠️ 1 час.", "location": "private", "usage": "Без лимита."},
    "unlimited_24h": {"name": "Безлимит 24ч", "price": 100, "icon": "♾️", "category": "text", "desc": "Безлимит 24ч.", "warning": "⚠️ 24 часа.", "location": "private", "usage": "Сутки."},
    "unlimited_7d": {"name": "Безлимит 7д", "price": 500, "icon": "♾️", "category": "text", "desc": "Безлимит 7д.", "warning": "⚠️ 7 дней.", "location": "private", "usage": "Неделя."},
    "image1": {"name": "1 фото", "price": 15, "icon": "🎨", "category": "image", "desc": "1 фото.", "warning": "⚠️ Сгорают.", "location": "private", "usage": "Опишите."},
    "image5": {"name": "5 фото", "price": 60, "icon": "🎨", "category": "image", "desc": "5 фото.", "warning": "⚠️ Сгорают.", "location": "private", "usage": "5 фото."},
    "image20": {"name": "20 фото", "price": 200, "icon": "🎨", "category": "image", "desc": "20 фото.", "warning": "⚠️ Сгорают.", "location": "private", "usage": "Творчество."},
    "image_unlimited_1h": {"name": "Безлимит фото 1ч", "price": 50, "icon": "♾️", "category": "image", "desc": "Безлимит 1ч.", "warning": "⚠️ 1 час.", "location": "private", "usage": "Без лимита."},
    "premium_day": {"name": "Премиум ЛС 1д", "price": 200, "icon": "⭐", "category": "premium", "desc": "Безлимит 24ч.", "warning": "⚠️ 24ч.", "location": "private", "usage": "Всё."},
    "premium_week": {"name": "Премиум ЛС 7д", "price": 1000, "icon": "⭐", "category": "premium", "desc": "Безлимит 7д.", "warning": "⚠️ 7д.", "location": "private", "usage": "Неделя."},
    "premium_forever": {"name": "Премиум ЛС навсегда", "price": 2500, "icon": "👑", "category": "premium", "desc": "Навсегда.", "warning": "⚠️ ЛС.", "location": "private", "usage": "Выгодно!"},
    "chat_extra10": {"name": "+10 в чатах", "price": 15, "icon": "👥", "category": "chat", "desc": "10 для всех.", "warning": "⚠️ Владелец.", "location": "chat", "usage": "Все +10."},
    "chat_extra50": {"name": "+50 в чатах", "price": 60, "icon": "👥", "category": "chat", "desc": "50 для всех.", "warning": "⚠️ Владелец.", "location": "chat", "usage": "Все +50."},
    "chat_unlimited_1h": {"name": "Безлимит чат 1ч", "price": 40, "icon": "♾️", "category": "chat", "desc": "Безлимит 1ч.", "warning": "⚠️ Владелец.", "location": "chat", "usage": "Час."},
    "chat_unlimited_24h": {"name": "Безлимит чат 24ч", "price": 150, "icon": "♾️", "category": "chat", "desc": "Безлимит 24ч.", "warning": "⚠️ Владелец.", "location": "chat", "usage": "Сутки."},
    "chat_image5": {"name": "5 фото в чатах", "price": 50, "icon": "🖼️", "category": "chat_image", "desc": "5 фото.", "warning": "⚠️ Владелец.", "location": "chat", "usage": "Все +5."},
    "chat_image20": {"name": "20 фото в чатах", "price": 180, "icon": "🖼️", "category": "chat_image", "desc": "20 фото.", "warning": "⚠️ Владелец.", "location": "chat", "usage": "Все +20."},
    "chat_premium_day": {"name": "Премиум чат 1д", "price": 300, "icon": "⭐", "category": "chat_premium", "desc": "Безлимит 24ч.", "warning": "⚠️ Владелец.", "location": "chat", "usage": "Все."},
    "chat_premium_week": {"name": "Премиум чат 7д", "price": 1500, "icon": "⭐", "category": "chat_premium", "desc": "Безлимит 7д.", "warning": "⚠️ Владелец.", "location": "chat", "usage": "Неделя."},
    "chat_premium_forever": {"name": "Премиум чат навсегда", "price": 3500, "icon": "👑", "category": "chat_premium", "desc": "Навсегда.", "warning": "⚠️ Владелец.", "location": "chat", "usage": "Навсегда."},
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
    current_hour_block = now.strftime("%Y-%m-%d-%H")
    last_update = rate_data.get("hour_block", "")
    
    if last_update != current_hour_block:
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
        
        volatility = 1.0
        if history:
            rates = [h.get("rate", base_rate) for h in history.values() if h.get("rate")]
            if len(rates) > 1:
                avg_rate = sum(rates) / len(rates)
                std_dev = math.sqrt(sum((r - avg_rate) ** 2 for r in rates) / len(rates))
                volatility = 1.0 + (std_dev / max(avg_rate, 0.0001)) * 0.5
        
        market_noise = random.uniform(0.92, 1.08)
        rate = round(base_rate * supply_factor * activity_factor * burn_factor * volatility * market_noise, 8)
        rate = max(0.0001, min(1.0, rate))
        market_cap = round(total_tokens * rate, 2)
        yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_rate = history.get(yesterday, {}).get("rate", rate)
        change_24h = round(((rate - yesterday_rate) / max(yesterday_rate, 0.0001)) * 100, 2)
        trend = "📈" if change_24h > 0.5 else "📉" if change_24h < -0.5 else "📊"
        
        rate_data = {
            "hour_block": current_hour_block, "date": now.strftime("%Y-%m-%d"), "rate": rate,
            "total_supply": total_tokens, "total_burned": total_burned,
            "total_donated": donated_total,
            "market_cap": market_cap, "change_24h": change_24h, "trend": trend,
            "updated_at": now.isoformat(),
        }
        save_json(TOKEN_RATE_FILE, rate_data)
        
        today = now.strftime("%Y-%m-%d")
        history[today] = {"rate": rate, "supply": total_tokens, "market_cap": market_cap}
        if len(history) > 30: history = dict(sorted(history.items())[-30:])
        save_json(TOKEN_HISTORY_FILE, history)
    
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
        [KeyboardButton("💰 Заработать"), KeyboardButton("💸 Перевод")],
        [KeyboardButton("🌍 Донат"), KeyboardButton("💮 Курс NBT")],
    ], resize_keyboard=True)

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("ℹ️ О боте", callback_data="about"), InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🧠 Модели", callback_data="models"), InlineKeyboardButton("💎 Премиум", callback_data="premium_info")],
        [InlineKeyboardButton("🎫 Скидки", callback_data="discounts_info"), InlineKeyboardButton("💮 Курс NBT", callback_data="tokenrate")],
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
    return InlineKeyboardMarkup([[InlineKeyboardButton("🎁 Ежедневный бонус", callback_data="daily_bonus"), InlineKeyboardButton("👥 Реферальная ссылка", callback_data="ref_link")], [InlineKeyboardButton("💸 Перевод", callback_data="transfer"), InlineKeyboardButton("🌍 Донат", callback_data="donate_info")], [InlineKeyboardButton("🔙 Назад", callback_data="menu")]])

def limit_reached_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🛒 Купить запросы", callback_data="shop"), InlineKeyboardButton("💰 Заработать", callback_data="earn")], [InlineKeyboardButton("💎 Премиум", callback_data="premium_info")]])

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
        await update.message.reply_text(f"🧠 NeBlock AI V{BOT_VERSION} в чате!\n💬 @{context.bot.username} вопрос\n🎨 /genimage описание\n💸 /transfer\n🌍 /donate\n👑 /chatowner | 🛒 /chatshop")
        return
    premium = "💎 Активен" if is_premium(user_id) else "Не активен"
    rate_data = get_token_rate(); rate = rate_data.get("rate", 0.01)
    donated_total, _, _ = get_donation_stats()
    await update.message.reply_text(
        f"🧠 NeBlock AI V{BOT_VERSION}\n━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💬 Текст | 🎨 Фото | 💸 Переводы | 🌍 Донаты\n"
        f"💎 Премиум ЛС: {premium}\n\n"
        f"💰 Баланс: {user.get('tokens', 0)} 💮 (~${user.get('tokens', 0) * rate:.2f})\n"
        f"💮 1 NBT = ${rate:.8f}\n"
        f"🔥 Сожжено всего: {donated_total:,} 💮\n"
        f"📊 Лимиты: {DAILY_LIMIT} вопр. + {IMAGE_DAILY_LIMIT} фото/день\n\n"
        f"👇 Выбери модель:",
        reply_markup=main_reply_keyboard()
    )

async def tokenrate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rate_data = get_token_rate(); history = load_json(TOKEN_HISTORY_FILE)
    rate = rate_data.get("rate", 0.01); supply = rate_data.get("total_supply", 0)
    market_cap = rate_data.get("market_cap", 0); donated = rate_data.get("total_donated", 0)
    burned = rate_data.get("total_burned", 0); updated = rate_data.get("updated_at", "")
    updated_time = datetime.fromisoformat(updated).strftime("%d.%m.%Y %H:%M") if updated else "Нет"
    text = (f"💮 КУРС NBT\n━━━━━━━━━━━━━━━━\n\n💰 1 NBT = ${rate:.8f}\n"
            f"💎 Капитализация: ${market_cap:,.2f}\n🪙 В обороте: {supply:,} NBT\n"
            f"🔥 Сожжено всего: {burned:,} 💮 (донатов: {donated:,} 💮)\n"
            f"🕐 Обновлён: {updated_time}\n🔄 Каждые 4 часа\n\n📈 История (7д):\n")
    for date, h in sorted(history.items())[-7:]: text += f"{date}: ${h.get('rate', 0):.8f}\n"
    text += f"\n{TOKEN_RATE_INFO}"
    await update.message.reply_text(text)

async def donate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text(f"🌍 /donate СУММА — сжечь токены\nПример: /donate 100\n\n{DONATE_INFO_TEXT[:500]}")
        return
    try: amount = int(context.args[0])
    except: await update.message.reply_text("❌ /donate СУММА"); return
    if amount < MIN_DONATION: await update.message.reply_text(f"❌ Мин: {MIN_DONATION} 💮"); return
    if amount > MAX_DONATION: await update.message.reply_text(f"❌ Макс: {MAX_DONATION} 💮"); return
    user = get_user(user_id)
    if user.get("tokens", 0) < amount: await update.message.reply_text(f"❌ Недостаточно!\n💰 Баланс: {user.get('tokens', 0)} 💮"); return
    await update.message.reply_text(
        f"🌍 ПОДТВЕРЖДЕНИЕ ДОНАТА\n━━━━━━━━━━━━━━━━\n\n"
        f"💰 Сумма: {amount} 💮\n🔥 Токены будут сожжены НАВСЕГДА\n"
        f"💮 Это повысит курс NBT для всех\n"
        f"💎 Баланс: {user.get('tokens', 0)} 💮 → {user.get('tokens', 0) - amount} 💮\n\nПодтвердите:",
        reply_markup=donate_confirm_keyboard(amount)
    )

async def donatetop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total, count, top_donors = get_donation_stats()
    if not top_donors: await update.message.reply_text("🌍 ТОП БЛАГОТВОРИТЕЛЕЙ\n\nПока никто не делал донатов.\nБудьте первым! /donate СУММА"); return
    text = f"🌍 ТОП БЛАГОТВОРИТЕЛЕЙ\n━━━━━━━━━━━━━━━━\n\n🔥 Всего сожжено: {total:,} 💮\n📊 Донатов: {count}\n\n🏆 ТОП-10:\n"
    users = load_users(); medals = ["🥇", "🥈", "🥉"]
    for i, (uid, donated) in enumerate(top_donors):
        name = f"@{users.get(uid, {}).get('username', 'Неизвестный')}" if uid in users else f"ID:{uid}"
        medal = medals[i] if i < 3 else f"{i+1}."
        text += f"{medal} {name}: {donated:,} 💮\n"
    text += "\n💡 /donate СУММА — сделать вклад"
    await update.message.reply_text(text)

async def donate_info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total, count, _ = get_donation_stats()
    text = DONATE_INFO_TEXT.format(total=total, count=count)
    await update.message.reply_text(text)

async def genimage_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id; chat_type = update.effective_chat.type; chat_id = update.effective_chat.id if chat_type != "private" else None
    if not context.args: await update.message.reply_text("🎨 /genimage ОПИСАНИЕ\nПример: /genimage кот на луне"); return
    text = " ".join(context.args)
    if not can_image_request(user_id, chat_type, chat_id): await update.message.reply_text(f"🚫 Лимит фото!\n📊 Осталось: {image_remaining(user_id, chat_type, chat_id)}"); return
    msg = await update.message.reply_text("🎨 Генерирую...")
    try:
        image_bytes, error = await generate_image(text)
        if image_bytes: add_image_request(user_id, chat_type); await msg.delete(); await update.message.reply_photo(photo=image_bytes, caption=f"🎨 NeBlock Images V2\n📝 {text[:200]}\n📊 Осталось: {image_remaining(user_id, chat_type, chat_id)}")
        else: await msg.edit_text("❌ Ошибка")
    except:
        try: await msg.delete()
        except: pass
        await update.message.reply_text("❌ Ошибка.")

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
        else: await update.message.reply_text("💸 /transfer @username КОЛИЧЕСТВО или ответьте на сообщение"); return
    else:
        if not context.args or len(context.args) < 2: return
        try: to_id = int(context.args[0]); amount = int(context.args[1])
        except: return
    if not to_id or not amount: return
    if amount < MIN_TRANSFER or amount > MAX_TRANSFER: return
    if to_id == user_id: await update.message.reply_text("❌ Нельзя себе!"); return
    sender = get_user(user_id)
    if sender.get("daily_transfer_total", 0) + amount > DAILY_TRANSFER_LIMIT: return
    if sender.get("tokens", 0) < amount: await update.message.reply_text("❌ Недостаточно!"); return
    tax, tax_percent, _ = get_transfer_tax(amount)
    receiver = get_user(to_id)
    if not receiver: await update.message.reply_text("❌ Не найден!"); return
    final_amount = amount - tax
    receiver_name = receiver.get("username") or f"ID:{to_id}"
    tax_info = f"Налог: {tax} 💮 ({tax_percent}%)" if tax > 0 else "Без налога"
    await update.message.reply_text(
        f"⚠️ ПРОВЕРЬТЕ ДАННЫЕ!\n👤 @{receiver_name}\n🆔 {to_id}\n💸 {amount} 💮\n📊 {tax_info}\n💰 Получит: {final_amount} 💮\n\nПодтвердите:",
        reply_markup=transfer_confirm_keyboard(to_id, amount)
    )

async def transfer_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["waiting_transfer"] = True
    await update.message.reply_text("💸 Отправьте: ID КОЛИЧЕСТВО")

async def transfer_info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(TRANSFER_INFO)

async def discounts_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    discounts = get_discounts(); active = {k: v for k, v in discounts.items() if k not in ["last_update", "generated_at"]}
    text = f"🎫 СКИДКИ\n\n🔄 Обновление: {get_next_update_time().strftime('%d.%m.%Y 9:00 МСК')}\n\n"
    if not active: text += "Нет активных скидок."
    else:
        for item_id, disc in sorted(active.items(), key=lambda x: x[1]["percent"], reverse=True):
            item = get_shop_items().get(item_id)
            if item: text += f"{disc.get('color', '🟢')} {item['icon']} {item['name']}: -{disc['percent']}%\n"
    await update.message.reply_text(text)

async def promo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["waiting_promo"] = True
    await update.message.reply_text("🎟 Отправьте промокод.")

async def changelog_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("📋 Версия 3.7 — Максимально подробная информация во всех разделах")
async def commands_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text(COMMANDS_LIST)
async def shopdesc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("📋 /shop — магазин товаров")

async def chatowner_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]: return
    chat_id = update.effective_chat.id; user_id = update.effective_user.id; add_chat_owner(chat_id, user_id)
    chats = load_chats(); c = chats.get(str(chat_id), {})
    owners = c.get("owners", []) if isinstance(c, dict) else c
    text = f"👑 Владельцы:\n"
    for i, oid in enumerate(owners, 1): text += f"{i}. ID: {oid}\n"
    await update.message.reply_text(text)

async def chatshop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]: return
    chat_id = update.effective_chat.id; user_id = update.effective_user.id; add_chat_owner(chat_id, user_id)
    if not is_chat_owner(chat_id, user_id): return
    await update.message.reply_text(f"🛒 Магазин чата\n💰 {get_tokens(user_id)} 💮", reply_markup=shop_keyboard("chat"))

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
        await update.message.reply_text(f"👤 @{un}\n💰 {u.get('tokens', 0)} 💮\n🔥 Донатов: {u.get('donated_tokens', 0)} 💮")
    except: pass

async def admin_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    users = load_users()
    top = sorted(users.items(), key=lambda x: x[1].get("tokens", 0), reverse=True)[:10]
    text = "🏆 ТОП 💮\n\n"
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
    text = "🎟 Промокоды:\n\n"
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
    await update.message.reply_text(f"📊 Статистика\n👥 {len(users)}\n💮 В обороте: {rate_data.get('total_supply', 0):,} NBT\n🔥 Донатов: {donated_total:,} 💮")

async def admin_forcediscounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    new_d = generate_discounts(); new_d["last_update"] = datetime.now().strftime("%Y-%m-%d"); save_discounts(new_d)

async def admin_force_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    rate_data = load_json(TOKEN_RATE_FILE); rate_data["hour_block"] = ""; save_json(TOKEN_RATE_FILE, rate_data)
    new_rate = get_token_rate()
    await update.message.reply_text(f"💮 Курс: ${new_rate.get('rate', 0.01):.8f}")

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args: return
    text = " ".join(context.args); users = load_users(); sent = 0
    for uid in users:
        try: await context.bot.send_message(int(uid), f"📢 {text}"); sent += 1; await asyncio.sleep(0.05)
        except: pass
    await update.message.reply_text(f"✅ {sent}")

async def reply_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text; user_id = update.effective_user.id
    username = update.effective_user.username
    if username:
        users = load_users(); uid = str(user_id)
        if uid in users: users[uid]["username"] = username; save_users(users)
    
    if text == "💬 NeBlock AI V2":
        users = load_users(); users[str(user_id)]["current_model"] = "text"; users[str(user_id)]["waiting_for_image"] = False; save_users(users)
        await update.message.reply_text(f"💬 NeBlock AI V2\n📊 Осталось: {remaining(user_id)}"); return True
    if text == "🎨 NeBlock Images V2":
        users = load_users(); users[str(user_id)]["current_model"] = "image"; users[str(user_id)]["waiting_for_image"] = True; save_users(users)
        await update.message.reply_text(f"🎨 NeBlock Images V2\n📊 Осталось: {image_remaining(user_id)}"); return True
    if text == "👤 Профиль":
        u = get_user(user_id); joined = datetime.fromisoformat(u.get("joined", "")).strftime("%d.%m.%Y")
        last = "Никогда"
        if u.get("last_request"): last = datetime.fromisoformat(u["last_request"]).strftime("%d.%m.%Y в %H:%M")
        cm = "💬 NeBlock AI V2" if u.get("current_model") == "text" else "🎨 NeBlock Images V2"
        premium = "💎 Активен" if is_premium(user_id) else "Не активен"
        rate_data = get_token_rate(); rate = rate_data.get("rate", 0.01); usd = u.get("tokens", 0) * rate
        def fmt(x):
            if not x: return "Не активен"
            try:
                if datetime.now() < datetime.fromisoformat(x):
                    d = datetime.fromisoformat(x) - datetime.now(); days, hours = d.days, d.seconds // 3600
                    return f"Активен ({days}д {hours}ч)" if days > 0 else f"Активен ({hours}ч)"
            except: pass
            return "Не активен"
        await update.message.reply_text(
            f"👤 Профиль V{BOT_VERSION}\n━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🆔 {user_id}\n📅 {joined}\n🔮 {cm}\n💎 Премиум: {premium}\n\n"
            f"💰 Баланс: {u.get('tokens', 0)} 💮 (~${usd:.2f})\n"
            f"💮 Курс: 1 NBT = ${rate:.8f}\n"
            f"💎 Заработано: {u.get('earned_tokens', 0)} | 💸 Потрачено: {u.get('spent_tokens', 0)}\n"
            f"🌍 Донатов: {u.get('donated_tokens', 0)} 💮\n"
            f"🔥 Серия: {u.get('daily_bonus_streak', 0)} дн.\n\n"
            f"💬 ЛС: {u.get('requests_today', 0)}/{DAILY_LIMIT + u.get('extra_requests', 0)} | {fmt(u.get('unlimited_until'))}\n"
            f"🎨 Фото: {u.get('image_requests_today', 0)}/{IMAGE_DAILY_LIMIT + u.get('extra_image_requests', 0)} | {fmt(u.get('image_unlimited_until'))}\n"
            f"👥 Чаты: {u.get('chat_requests_today', 0)}/{CHAT_DAILY_LIMIT + u.get('extra_chat_requests', 0)} | {fmt(u.get('chat_unlimited_until'))}\n"
            f"💸 Переводов: {u.get('daily_transfer_total', 0)} 💮\n\n"
            f"📈 Всего: {u.get('total_requests', 0)} текст | {u.get('total_images', 0)} фото\n"
            f"🛡 {u.get('warnings', 0)}/5 | 👥 {u.get('referrals', 0)}\n🕐 {last}",
            reply_markup=main_menu()
        )
        return True
    if text == "🛒 Магазин": await update.message.reply_text(f"🛒 Магазин\n💰 {get_tokens(user_id)} 💮", reply_markup=shop_keyboard("private")); return True
    if text == "💰 Заработать": await update.message.reply_text(f"💰 Заработок\n💎 {get_tokens(user_id)} 💮\n🎁 Бонус: {DAILY_BONUS_MIN}-{DAILY_BONUS_MAX}/день\n👥 Рефералы: +{REFERRAL_BONUS} 💮", reply_markup=earn_keyboard()); return True
    if text == "💸 Перевод": await transfer_button_handler(update, context); return True
    if text == "🌍 Донат": await donate_info_cmd(update, context); return True
    if text == "🎟 Промокод": await promo_cmd(update, context); return True
    if text == "📚 FAQ": await update.message.reply_text(FAQ_TEXT); return True
    if text == "🎫 Скидки": await discounts_cmd(update, context); return True
    if text == "💮 Курс NBT": await tokenrate_cmd(update, context); return True
    return False

async def inline_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer(); user_id = query.from_user.id; data = query.data
    shop_items = get_shop_items()
    
    if data == "none": return
    if data == "transfer_cancel": await query.edit_message_text("❌ Перевод отменён."); return
    if data == "donate_cancel": await query.edit_message_text("❌ Донат отменён."); return
    
    if data.startswith("donate_confirm_"):
        amount = int(data.replace("donate_confirm_", ""))
        user = get_user(user_id)
        if user.get("tokens", 0) < amount: await query.edit_message_text("❌ Недостаточно!"); return
        if donate_tokens(user_id, amount):
            donated_total, _, _ = get_donation_stats()
            await query.edit_message_text(f"🌍 ДОНАТ ВЫПОЛНЕН!\n🔥 Сожжено: {amount} 💮\n💎 Баланс: {get_tokens(user_id)} 💮\n🌍 Всего сожжено: {donated_total:,} 💮")
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
            await query.edit_message_text(f"✅ ПЕРЕВОД ВЫПОЛНЕН!\n👤 {to_id}\n💸 {amount} 💮\n💰 Зачислено: {final_amount} 💮{tax_info}\n💎 Баланс: {get_tokens(user_id)} 💮")
        return
    
    if data == "menu": await query.edit_message_text(f"🧠 NeBlock AI V{BOT_VERSION}\n💰 {get_tokens(user_id)} 💮", reply_markup=main_menu())
    elif data == "about": await query.edit_message_text(f"ℹ️ NeBlock AI V{BOT_VERSION}\n\n💬 Текст\n🎨 Фото\n💸 Переводы\n🌍 Донаты\n💮 NBT\n📚 /faq — все вопросы", reply_markup=back_button())
    elif data == "donate_info": await donate_info_cmd(update, context)
    elif data == "models": await query.edit_message_text("🧠 МОДЕЛИ\n\n💬 NeBlock AI V2\n🎨 NeBlock Images V2\n📚 /faq — подробнее", reply_markup=back_button())
    elif data == "tokenrate":
        rd = get_token_rate()
        await query.edit_message_text(f"💮 NBT\n💰 1 = ${rd.get('rate', 0.01):.8f}\n💎 Кап: ${rd.get('market_cap', 0):,.2f}\n🔥 Сожжено: {rd.get('total_donated', 0):,} 💮", reply_markup=back_button())
    elif data == "transfer": context.user_data["waiting_transfer"] = True; await query.edit_message_text("💸 ПЕРЕВОД\n\nОтправьте ID и сумму:\nID КОЛИЧЕСТВО", reply_markup=back_button())
    elif data == "commands": await query.edit_message_text(COMMANDS_LIST, reply_markup=back_button())
    elif data == "changelog": await query.edit_message_text("📋 V3.7 — Максимально подробная информация")
    elif data == "discounts_info":
        discounts = get_discounts(); active = {k: v for k, v in discounts.items() if k not in ["last_update", "generated_at"]}
        text = "🎫 СКИДКИ\n\n"
        if not active: text += "Нет."
        else:
            for item_id, disc in sorted(active.items(), key=lambda x: x[1]["percent"], reverse=True):
                item = shop_items.get(item_id)
                if not item: continue
                if disc.get("type") == "legendary": text += f"🌟 {item['icon']} {item['name']}\n💫 БЕСПЛАТНО!\n\n"
                else: text += f"{disc.get('color', '🟢')} {item['icon']} {item['name']}\n🔥 -{disc['percent']}% = {disc['new_price']} 💮\n\n"
        await query.edit_message_text(text, reply_markup=back_button())
    elif data == "premium_info": await query.edit_message_text(f"💎 ПРЕМИУМ\n\nЛС: {shop_items.get('premium_day', {}).get('price', '?')}/{shop_items.get('premium_week', {}).get('price', '?')}/{shop_items.get('premium_forever', {}).get('price', '?')} 💮\n📚 /faq — подробнее", reply_markup=back_button())
    elif data == "stats":
        u = get_user(user_id)
        await query.edit_message_text(f"📊 Статистика\n💬 {u.get('requests_today', 0)}\n🎨 {u.get('image_requests_today', 0)}\n💰 {u.get('tokens', 0)} 💮\n🌍 Донатов: {u.get('donated_tokens', 0)} 💮", reply_markup=back_button())
    elif data == "shop": await query.edit_message_text(f"🛒 Магазин\n💰 {get_tokens(user_id)} 💮", reply_markup=shop_keyboard("private"))
    elif data == "earn": await query.edit_message_text(f"💰 Заработок\n💎 {get_tokens(user_id)} 💮", reply_markup=earn_keyboard())
    elif data == "promo": context.user_data["waiting_promo"] = True; await query.edit_message_text("🎟 Отправь промокод.", reply_markup=back_button())
    elif data == "faq": await query.edit_message_text(FAQ_TEXT[:4000], reply_markup=back_button())
    elif data == "daily_bonus":
        u = get_user(user_id); today = datetime.now().strftime("%Y-%m-%d")
        if u.get("daily_bonus_claimed") == today: await query.answer("❌ Уже забирали!", show_alert=True)
        else:
            bonus = random.randint(DAILY_BONUS_MIN, DAILY_BONUS_MAX); users = load_users(); uid = str(user_id)
            users[uid]["daily_bonus_claimed"] = today
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            users[uid]["daily_bonus_streak"] = users[uid].get("daily_bonus_streak", 0) + 1 if users[uid].get("last_bonus_date") == yesterday else 1
            users[uid]["last_bonus_date"] = today; save_users(users); add_tokens(user_id, bonus)
            await query.answer(f"🎉 +{bonus} 💮!", show_alert=True)
            await query.edit_message_text(f"🎁 +{bonus} 💮\n💰 {get_tokens(user_id)} 💮\n🔥 Серия: {users[uid]['daily_bonus_streak']} дн.", reply_markup=back_button())
    elif data == "ref_link":
        user = get_user(user_id); bot_username = (await context.bot.get_me()).username
        await query.edit_message_text(f"👥 https://t.me/{bot_username}?start=ref_{user.get('referral_code', '')}\n💰 +{REFERRAL_BONUS} 💮 тебе\n🎁 +{INVITED_BONUS} 💮 другу", reply_markup=back_button())
    elif data.startswith("confirm_"):
        item_id = data.replace("confirm_", ""); item = shop_items.get(item_id)
        if not item: return
        price, percent, disc = get_discounted_price(item_id)
        tokens = get_tokens(user_id)
        if tokens < price: await query.answer("❌ Недостаточно 💮!", show_alert=True); return
        remove_tokens(user_id, price); users = load_users(); uid = str(user_id)
        actions = {"extra5": ("extra_requests", 5), "extra10": ("extra_requests", 10), "extra50": ("extra_requests", 50), "image1": ("extra_image_requests", 1), "image5": ("extra_image_requests", 5), "image20": ("extra_image_requests", 20), "chat_extra10": ("extra_chat_requests", 10), "chat_extra50": ("extra_chat_requests", 50), "chat_image5": ("extra_chat_image_requests", 5), "chat_image20": ("extra_chat_image_requests", 20)}
        time_actions = {"unlimited_1h": ("unlimited_until", 1), "unlimited_24h": ("unlimited_until", 24), "unlimited_7d": ("unlimited_until", 168), "image_unlimited_1h": ("image_unlimited_until", 1), "chat_unlimited_1h": ("chat_unlimited_until", 1), "chat_unlimited_24h": ("chat_unlimited_until", 24)}
        if item_id in actions: field, amount = actions[item_id]; users[uid][field] = users[uid].get(field, 0) + amount
        elif item_id in time_actions: field, hours = time_actions[item_id]; users[uid][field] = (datetime.now() + timedelta(hours=hours)).isoformat()
        elif item_id == "premium_day": users[uid]["premium_until"] = (datetime.now() + timedelta(hours=24)).isoformat()
        elif item_id == "premium_week": users[uid]["premium_until"] = (datetime.now() + timedelta(days=7)).isoformat()
        elif item_id == "premium_forever": users[uid]["premium_until"] = (datetime.now() + timedelta(days=36500)).isoformat()
        elif item_id in ["chat_premium_day", "chat_premium_week", "chat_premium_forever"]:
            chats = load_chats(); hm = {"chat_premium_day": 24, "chat_premium_week": 168, "chat_premium_forever": 876000}
            for cid, cd in chats.items():
                if isinstance(cd, dict) and str(user_id) in cd.get("owners", []): chats[cid]["premium_until"] = (datetime.now() + timedelta(hours=hm[item_id])).isoformat(); save_chats(chats); break
        save_users(users)
        dt = f"\n🎫 -{percent}%" if percent > 0 else ""
        if disc and disc.get("type") == "legendary": dt = "\n🌟 ЛЕГЕНДАРНАЯ!"
        await query.answer(f"✅ {item['name']}!", show_alert=True)
        await query.edit_message_text(f"✅ {item['name']}{dt}\n💰 Потрачено: {price} 💮\n💎 Остаток: {get_tokens(user_id)} 💮", reply_markup=back_button())
    elif data.startswith("buy_"):
        item_id = data.replace("buy_", ""); item = shop_items.get(item_id)
        if not item: return
        price, percent, disc = get_discounted_price(item_id)
        tokens = get_tokens(user_id); can = "✅ Хватает" if tokens >= price else "❌ Не хватает"
        dt = ""
        if percent > 0 and disc:
            if disc.get("type") == "legendary": dt = "\n\n🌟 БЕСПЛАТНО!"
            else: dt = f"\n\n{disc.get('color', '🟢')} -{percent}%\n💵 {disc['original']} → 🔥 {price} 💮"
        await query.edit_message_text(f"🛒 {item['icon']} {item['name']}\n📝 {item['desc']}\n⚠️ {item.get('warning', '')}{dt}\n\n💎 {tokens} 💮\n{can}", reply_markup=confirm_keyboard(item_id))

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤔 Неизвестная команда.\n/start — меню | /commands — список")

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
            if clean_text.lower().startswith("нарисуй"):
                text = clean_text[7:].strip(); is_image_request = True
            else: text = clean_text
        
        if not should_respond:
            keywords_map = {"нарисуй ": True, "сгенерируй ": True, "создай ": True, "бот ": False, "нейробот ": False, "нейросеть ": False, "ai ": False, "AI ": False}
            for kw, is_image in keywords_map.items():
                if text_lower.startswith(kw):
                    clean_text = text[len(kw):].strip()
                    should_respond = True
                    if is_image: is_image_request = True; text = clean_text
                    else: text = clean_text
                    break
        
        if not should_respond: return
        if not text:
            await update.message.reply_text(f"🧠 NeBlock AI V2!\n💬 @{bot_username} вопрос\n🎨 @{bot_username} нарисуй\n🎨 /genimage\n💸 /transfer\n🌍 /donate", reply_to_message_id=update.message.message_id)
            return
    
    user = get_user(user_id)
    if context.user_data.get("waiting_promo"): context.user_data["waiting_promo"] = False; success, result = use_promo(user_id, text); await update.message.reply_text(f"🎟 +{result} 💮!" if success else f"❌ {result}"); return
    
    if is_image_request or (chat_type == "private" and (user.get("current_model") == "image" or user.get("waiting_for_image"))):
        if chat_type == "private": users = load_users(); users[str(user_id)]["waiting_for_image"] = False; save_users(users)
        if not can_image_request(user_id, chat_type, chat_id):
            await update.message.reply_text(f"🚫 Лимит фото!\n📊 Осталось: {image_remaining(user_id, chat_type, chat_id)}", reply_to_message_id=update.message.message_id if chat_type != "private" else None, reply_markup=limit_reached_keyboard() if chat_type == "private" else None); return
        msg = await update.message.reply_text("🎨 Генерирую...", reply_to_message_id=update.message.message_id if chat_type != "private" else None)
        try:
            image_bytes, error = await generate_image(text)
            if image_bytes: add_image_request(user_id, chat_type); await msg.delete(); await update.message.reply_photo(photo=image_bytes, caption=f"🎨 NeBlock Images V2\n📝 {text[:200]}\n📊 Осталось: {image_remaining(user_id, chat_type, chat_id)}", reply_to_message_id=update.message.message_id if chat_type != "private" else None)
            else: await msg.edit_text("❌ Ошибка")
        except:
            try: await msg.delete()
            except: pass
            await update.message.reply_text("❌ Ошибка.")
        return
    
    if not can_request(user_id, chat_type, chat_id):
        await update.message.reply_text(f"🚫 Лимит!\n📊 Осталось: {remaining(user_id, chat_type, chat_id)}", reply_markup=limit_reached_keyboard() if chat_type == "private" else None, reply_to_message_id=update.message.message_id if chat_type != "private" else None); return
    
    msg = await update.message.reply_text("💬 Генерирую...", reply_to_message_id=update.message.message_id if chat_type != "private" else None)
    try:
        response = client.responses.create(prompt={"id": PROMPT_ID}, input=text); answer = response.output_text
        add_request(user_id, chat_type); await msg.delete()
        if answer:
            rem = remaining(user_id, chat_type, chat_id)
            if chat_type in ["group", "supergroup"]: used = user.get("chat_requests_today", 0) + 1; total = CHAT_DAILY_LIMIT + user.get("extra_chat_requests", 0); label = "👥 Чат"
            else: used = user.get("requests_today", 0) + 1; total = DAILY_LIMIT + user.get("extra_requests", 0); label = "💬 NeBlock AI V2"
            footer = f"\n\n━━━━━━━━━━━━━━━━\n{label} | 📊 {used}/{total} | Осталось: {rem}{AI_DISCLAIMER}"
            for i in range(0, len(answer), 4000): chunk = answer[i:i+4000]; await update.message.reply_text(chunk + footer if i == 0 else chunk, reply_to_message_id=update.message.message_id if chat_type != "private" else None)
        else: await update.message.reply_text(f"🤷 Пусто{AI_DISCLAIMER}")
    except:
        try: await msg.delete()
        except: pass
        await update.message.reply_text(f"❌ Ошибка{AI_DISCLAIMER}")

def main():
    print(f"🧠 NeBlock AI V{BOT_VERSION}")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
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
