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
# 🧠 NeBlock AI V3.1 - Конфигурация
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
ADMIN_IDS = [1671403667]
START_BONUS = 50
DAILY_BONUS_MIN = 5
DAILY_BONUS_MAX = 15
REFERRAL_BONUS = 25
INVITED_BONUS = 10
BOT_VERSION = "3.1"

MIN_TRANSFER = 1
MAX_TRANSFER = 10000
DAILY_TRANSFER_LIMIT = 50000

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

Убедитесь что UserID получателя указан верно!
Если вы отправите токены не на тот UserID — вернуть их будет НЕВОЗМОЖНО!
Транзакции в блокчейне NeBlock необратимы.

Проверьте:
• Правильность ID получателя
• Сумму перевода
• Размер налога и итоговую сумму

Подтверждая перевод, вы соглашаетесь с условиями.
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

CHANGELOG = """
📋 ЛОГ ОБНОВЛЕНИЙ NeBlock AI
━━━━━━━━━━━━━━━━━━━━

Версия 3.1 (21.07.2026)
• Расширенный FAQ с подробными ответами
• Полное описание всех функций

Версия 3.0 (21.07.2026)
• 💸 Переводы в ЛС и чатах
• ⚠️ Подтверждение перед отправкой
• 💰 Динамический налог

Версия 2.9 (21.07.2026)
• Курс каждые 4 часа
• Кнопка промокода
"""

# ═══════════════════════════════════════════
# 📚 РАСШИРЕННЫЙ FAQ
# ═══════════════════════════════════════════

FAQ_TEXT = f"""
📚 ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ
━━━━━━━━━━━━━━━━━━━━

═══════════════════════
❓ ЧТО ТАКОЕ NeBlock AI?
═══════════════════════

NeBlock AI — это мощная платформа с двумя ИИ-моделями, работающая прямо в Telegram. Бот использует передовые технологии искусственного интеллекта для ответов на вопросы, написания кода, объяснения сложных тем и генерации уникальных изображений.

💬 NeBlock AI V2 — ТЕКСТОВАЯ МОДЕЛЬ
Назначение: ответы на вопросы, написание кода на любых языках программирования, объяснение сложных тем простыми словами, переводы на 50+ языков, помощь с учёбой и домашними заданиями, креативные задачи и генерация идей.

Характеристики:
• Качество ответов улучшено на 40% по сравнению с предыдущей версией
• Скорость генерации увеличена в 2 раза — ответ приходит за 2-5 секунд
• Контекст диалога расширен до 8000 токенов — бот помнит о чём вы говорили
• Поддержка многошаговых инструкций — можно давать сложные задания
• Улучшенное понимание сложных и комплексных запросов
• Автоматическое определение языка (50+ языков)
• Работает в личных сообщениях и в чатах

🎨 NeBlock Images V2 — ГЕНЕРАЦИЯ ФОТО
Назначение: создание уникальных изображений по текстовому описанию. Модель понимает сложные описания и может создавать изображения в разных стилях.

Характеристики:
• Качество изображений повышено на 50% — более чёткие и детальные
• Поддержка разных художественных стилей: реализм, аниме, арт, 3D, скетч
• Улучшенная детализация мелких объектов
• Скорость генерации до 15 секунд
• Размер изображения: 1024x1024 пикселей
• Работает в личных сообщениях и в чатах
• Каждое изображение уникально и создаётся с нуля

═══════════════════════
❓ КАК ПОЛЬЗОВАТЬСЯ БОТОМ?
═══════════════════════

Существует несколько способов взаимодействия с ботом, каждый подходит для разных ситуаций:

1. В ЛИЧНЫХ СООБЩЕНИЯХ (ЛС):
Это основной режим использования. Напишите боту в личные сообщения — и он ответит.

• Просто напишите вопрос в чат — бот автоматически ответит
• Используйте кнопки внизу экрана для навигации по разделам
• Кнопка "💬 NeBlock AI V2" — активирует текстовую модель
• Кнопка "🎨 NeBlock Images V2" — активирует генерацию фото
• Кнопка "👤 Профиль" — ваш личный кабинет со статистикой
• Кнопка "🛒 Магазин" — покупка запросов и премиума
• Кнопка "💰 Заработать" — способы получения токенов
• Кнопка "💸 Перевод" — отправка токенов другим пользователям
• Кнопка "🎫 Скидки" — просмотр активных скидок
• Кнопка "💮 Курс NBT" — текущий курс и токеномика

2. В ЧАТАХ И ГРУППАХ:
Бот умеет работать в группах и супергруппах. Чтобы бот ответил, нужно обратиться к нему:

• @имя_бота ваш вопрос — бот ответит в чате
• @имя_бота нарисуй описание — бот сгенерирует фото
• Ключевые слова: бот, нейробот, нейросеть, AI, нарисуй
• Бот реагирует ТОЛЬКО на упоминания и ключевые слова
• Обычные сообщения без обращения к боту полностью игнорируются

Важно: Чтобы бот работал в чате, добавьте его как администратора!

3. ЧЕРЕЗ КОМАНДЫ:
Используйте команды для быстрого доступа к функциям:
• /start — главное меню и приветствие
• /shop — магазин товаров
• /shopdesc — подробное описание всех товаров
• /discounts — активные скидки
• /tokenrate — курс NBT и токеномика
• /transfer — перевод токенов
• /transferinfo — информация о переводах
• /faq — этот раздел
• /changelog — история обновлений
• /promo — активация промокода
• /commands — список всех команд

═══════════════════════
❓ КАКИЕ ЛИМИТЫ И ЗАЧЕМ ОНИ?
═══════════════════════

Лимиты установлены чтобы обеспечить стабильную и быструю работу нейросети для всех пользователей одновременно. Каждый запрос требует вычислительных ресурсов, и лимиты помогают равномерно распределять нагрузку.

📊 ЛИМИТЫ В ЛИЧНЫХ СООБЩЕНИЯХ:
• {DAILY_LIMIT} текстовых вопросов в день
• {IMAGE_DAILY_LIMIT} генераций фото в день
• Сброс происходит каждый день в 00:00 по московскому времени (МСК)
• Неиспользованные запросы НЕ переносятся на следующий день

📊 ЛИМИТЫ В ЧАТАХ И ГРУППАХ:
• {CHAT_DAILY_LIMIT} текстовых вопросов в день (общий лимит на чат)
• {CHAT_IMAGE_LIMIT} генераций фото в день (общий лимит на чат)
• Сброс также в 00:00 МСК каждый день
• Лимиты общие на всех участников чата

⚠️ ВАЖНАЯ ИНФОРМАЦИЯ О ЛИМИТАХ:
• Дополнительные запросы, купленные в магазине — СГОРАЮТ при ежедневном сбросе
• Безлимиты действуют точное указанное время и НЕ сгорают при сбросе
• Премиум полностью отключает ВСЕ лимиты на выбранный срок
• Безлимит действует с момента покупки (например, 1 час, 24 часа, 7 дней)
• При покупке безлимита старые купленные запросы продолжают действовать

💡 СОВЕТ: Покупайте дополнительные запросы только если планируете использовать их сегодня. Для долгосрочного использования выгоднее купить безлимит или Премиум.

═══════════════════════
❓ ЧТО ТАКОЕ 💮 NBT?
═══════════════════════

💮 NeBlock Token (NBT) — это внутренняя валюта платформы NeBlock AI. Токены используются для покупок в магазине, оплаты дополнительных запросов, безлимитов и Премиум-режимов.

ОСНОВНЫЕ ХАРАКТЕРИСТИКИ:
• Тикер: NBT
• Эмодзи: 💮
• Курс: динамический, обновляется каждые 4 часа
• Не продаётся за реальные деньги
• Можно только заработать внутри платформы
• Нельзя вывести или обменять на реальные деньги

КАК ФОРМИРУЕТСЯ КУРС NBT:
Курс зависит от нескольких рыночных факторов:
1. Количество токенов в обороте — чем больше токенов, тем выше курс (дефляционная модель)
2. Активность пользователей — чем активнее, тем выше спрос и курс
3. Сжигание токенов — налоги с переводов сжигаются, уменьшая предложение
4. Рыночная волатильность — случайные колебания ±8% каждый цикл
5. Историческая волатильность — анализ колебаний за 30 дней

ГДЕ ПОСМОТРЕТЬ КУРС:
• Кнопка "💮 Курс NBT" в главном меню
• Команда /tokenrate
• В профиле пользователя
• Курс отображается в долларах США (USD)
• Доступна история курса за 7 дней

═══════════════════════
❓ КАК ЗАРАБОТАТЬ 💮 NBT?
═══════════════════════

Существует несколько способов заработка токенов. Вы можете комбинировать их для максимальной выгоды:

1. ЕЖЕДНЕВНЫЙ БОНУС:
• {DAILY_BONUS_MIN}-{DAILY_BONUS_MAX} 💮 каждый день
• Нажмите кнопку "💰 Заработать" → "🎁 Ежедневный бонус"
• Бонус можно получить только один раз в сутки
• Серия ежедневных бонусов увеличивается (стрик)
• Чем дольше серия — тем больше бонусов вы накопили
• Сброс серии происходит при пропуске дня

2. РЕФЕРАЛЬНАЯ ПРОГРАММА:
• Пригласите друга по вашей уникальной реферальной ссылке
• Вы получаете +{REFERRAL_BONUS} 💮 за каждого приглашённого
• Приглашённый друг получает +{INVITED_BONUS} 💮 при первом запуске
• Ссылка доступна в разделе "💰 Заработать" → "👥 Реферальная ссылка"
• Количество рефералов не ограничено
• Рефералы отображаются в профиле

3. СТАРТОВЫЙ БОНУС:
• {START_BONUS} 💮 начисляется автоматически при первом запуске бота
• Не требует никаких действий
• Достаточно просто начать пользоваться ботом

4. ПРОМОКОДЫ:
• Следите за новостями и акциями в канале
• Вводите промокоды в разделе "🎟 Промокод"
• Промокоды создаёт администратор
• Каждый промокод можно использовать только один раз
• Некоторые промокоды имеют ограничение по количеству использований

5. ПЕРЕВОДЫ ОТ ДРУГИХ ПОЛЬЗОВАТЕЛЕЙ:
• Другие пользователи могут отправить вам 💮
• Используйте команду /transfer для отправки
• При получении перевода приходит уведомление

6. СПЕЦИАЛЬНЫЕ АКЦИИ:
• Временные акции и раздачи
• Сезонные ивенты
• Конкурсы и розыгрыши
• Следите за обновлениями в /changelog

═══════════════════════
❓ КАК РАБОТАЮТ СКИДКИ?
═══════════════════════

Система скидок делает покупки в магазине значительно выгоднее. Скидки генерируются автоматически и применяются ко всем пользователям.

ОБНОВЛЕНИЕ СКИДОК:
• Автоматически каждые 2 дня
• Точное время обновления: 9:00 по московскому времени (МСК)
• Скидки применяются автоматически в магазине
• Не нужно вводить промокоды — цена со скидкой отображается сразу

ТИПЫ СКИДОК (от частых к редким):

🟢 ОБЫЧНАЯ СКИДКА (5-25%) — шанс 40%
Самая частая скидка. Появляется на случайные товары.
Может быть на любой товар в магазине.

🔴 СУПЕР-СКИДКА (30-50%) — шанс 20%
Повышенная скидка. Очень выгодное предложение!
Обычно на популярные товары.

📦 СКИДКА НА НАБОР (15-35%) — шанс 12%
Скидка на большие пакеты запросов.
Экономия при оптовой покупке.

⚡ ФЛЕШ-СКИДКА (40-70%) — шанс 8%
Редкая скидка. Действует всего 24 часа.
Нужно успеть купить до истечения срока!

💎 ПРЕМИУМ-СКИДКА (10-30%) — шанс 5%
Скидка на Премиум-режимы.
Редкая возможность сэкономить на Премиуме.

🌟 ЛЕГЕНДАРНАЯ СКИДКА (100%) — шанс 0.5%
Скидка 100%! Товар полностью бесплатно!
Шанс выпадения: 1 раз на 200 обновлений.
Действует всего 3 часа.
Самая редкая и желанная скидка!

💡 СОВЕТ: Проверяйте скидки перед каждой покупкой! Используйте /discounts.

═══════════════════════
❓ ЧТО ТАКОЕ ПРЕМИУМ?
═══════════════════════

Премиум — это режим, который полностью отключает все лимиты. С Премиумом вы можете задавать неограниченное количество вопросов и генерировать неограниченное количество изображений.

💎 ПРЕМИУМ ЛС (ЛИЧНЫЕ СООБЩЕНИЯ):
• Безлимит текстовых запросов
• Безлимит генерации фото
• Действует только в личных сообщениях с ботом
• Не распространяется на чаты

💎 ПРЕМИУМ ЧАТ (ГРУППЫ):
• Безлимит текста и фото для ВСЕХ участников чата
• Покупает владелец чата
• Действует на всех участников одновременно

СРОКИ ПРЕМИУМА:
• 1 день — для тестирования или разового использования
• 7 дней — для активного использования в течение недели
• Навсегда — единоразовая покупка, безлимит навсегда

💡 Премиум навсегда — самая выгодная покупка! Окупается за 2-3 недели активного использования.

═══════════════════════
❓ КАК РАБОТАЮТ ПЕРЕВОДЫ?
═══════════════════════

Вы можете отправлять 💮 NBT другим пользователям платформы. Переводы работают как в личных сообщениях, так и в чатах.

КАК ОТПРАВИТЬ ПЕРЕВОД:
• В ЛС: /transfer ID КОЛИЧЕСТВО (например: /transfer 1671403667 100)
• В ЧАТЕ: ответьте на сообщение пользователя и напишите /transfer КОЛИЧЕСТВО
• Через кнопку "💸 Перевод" в главном меню

⚠️ ВНИМАНИЕ! Проверяйте UserID получателя перед отправкой!
Если вы отправите токены на неверный ID — вернуть их НЕВОЗМОЖНО.
Транзакции в блокчейне NeBlock необратимы.

ЛИМИТЫ ПЕРЕВОДОВ:
• Минимальная сумма: {MIN_TRANSFER} 💮
• Максимальная сумма за раз: {MAX_TRANSFER} 💮
• Максимальная сумма в день: {DAILY_TRANSFER_LIMIT} 💮

НАЛОГИ НА ПЕРЕВОДЫ:
Налог зависит от суммы перевода. Чем больше сумма — тем выше процент.
Собранные налоги сжигаются, что повышает курс 💮 для всех держателей!

• 1-199 💮 — без налога (0%)
• 200-499 💮 — налог 3% (малый перевод)
• 500-999 💮 — налог 5% (средний перевод)
• 1,000-2,499 💮 — налог 8% (крупный перевод)
• 2,500-4,999 💮 — налог 12% (очень крупный)
• 5,000-10,000 💮 — налог 15% (максимальный)

ПРИМЕРЫ:
• Отправка 100 💮 → получатель получит 100 💮 (без налога)
• Отправка 300 💮 → получатель получит 291 💮 (налог 9 💮)
• Отправка 1,000 💮 → получатель получит 920 💮 (налог 80 💮)
• Отправка 5,000 💮 → получатель получит 4,250 💮 (налог 750 💮)

ВАЖНО:
• Налог списывается с отправителя
• Получатель получает сумму за вычетом налога
• Налоги сжигаются и повышают курс 💮
• Нельзя отправить больше чем есть на балансе
• Нельзя отправить самому себе
• Переводы логируются и сохраняются

═══════════════════════
❓ КТО МОЖЕТ ПОКУПАТЬ ДЛЯ ЧАТА?
═══════════════════════

Покупки для чата может совершать только владелец чата. Это сделано для безопасности и контроля расходов.

КАК ЭТО РАБОТАЕТ:
• Владелец чата определяется командой /chatowner
• Первый кто использует /chatowner автоматически становится владельцем
• Владелец покупает запросы через /chatshop
• Купленные запросы применяются ко ВСЕМ участникам чата
• Запросы для чата сгорают в 00:00 МСК каждый день
• Премиум чата отключает лимиты для всех участников

КАК СТАТЬ ВЛАДЕЛЬЦЕМ:
• Используйте команду /chatowner в чате
• Вы будете добавлены в список владельцев
• Может быть несколько владельцев

═══════════════════════
❓ БОТ ПОМНИТ ИСТОРИЮ?
═══════════════════════

Да! Текстовая модель NeBlock AI V2 учитывает контекст диалога:
• Можно задавать уточняющие вопросы
• Бот помнит о чём вы говорили ранее в этом диалоге
• Контекст сохраняется в течение всей сессии
• Для сброса контекста используйте /start

═══════════════════════
❓ КАКИЕ ЯЗЫКИ ПОДДЕРЖИВАЮТСЯ?
═══════════════════════

Бот автоматически определяет язык сообщения и отвечает на нём же:
• Русский
• Английский (English)
• Немецкий (Deutsch)
• Французский (Français)
• Испанский (Español)
• Китайский (中文)
• Японский (日本語)
• И многие другие (50+ языков)

═══════════════════════
❓ ЧТО ДЕЛАТЬ ПРИ ПРОБЛЕМАХ?
═══════════════════════

Если бот не отвечает:
• Проверьте соединение с интернетом
• Попробуйте команду /start для перезапуска
• Подождите пару минут (возможна высокая нагрузка)
• Убедитесь что не исчерпан дневной лимит
• Проверьте не заблокированы ли вы (предупреждения в профиле)

Если бот отвечает с ошибкой:
• Попробуйте переформулировать вопрос
• Убедитесь что сообщение не превышает 2000 символов
• Проверьте что сообщение не содержит запрещённый контент

Если проблемы с токенами:
• Проверьте баланс в профиле
• Проверьте историю транзакций
• Убедитесь что промокод не был использован ранее

═══════════════════════
❓ ГДЕ ПОСМОТРЕТЬ ОБНОВЛЕНИЯ?
═══════════════════════

• /changelog — полная история всех версий
• Кнопка "📋 Изменения" в главном меню
• Следите за новостями в канале бота
"""

TRANSFER_INFO = f"""
💸 ПЕРЕВОДЫ 💮 NBT
━━━━━━━━━━━━━━━━━━━━

📋 КАК ПЕРЕВЕСТИ:
1. В ЛС: /transfer ID КОЛИЧЕСТВО
2. В ЧАТЕ: ответьте на сообщение и /transfer КОЛИЧЕСТВО
3. Кнопка "💸 Перевод" в меню

⚠️ ВНИМАНИЕ!
Проверяйте UserID получателя! Если отправите не тому — токены не вернуть!

📊 ЛИМИТЫ:
• Мин: {MIN_TRANSFER} 💮 | Макс за раз: {MAX_TRANSFER} 💮
• Макс в день: {DAILY_TRANSFER_LIMIT} 💮

💰 НАЛОГИ:
• 1-199 💮 — 0% | 200-499 💮 — 3%
• 500-999 💮 — 5% | 1000-2499 💮 — 8%
• 2500-4999 💮 — 12% | 5000-10000 💮 — 15%
"""

COMMANDS_LIST = """
📋 КОМАНДЫ NeBlock AI V3.1
━━━━━━━━━━━━━━━━━━━━

/start — главное меню
/shop — магазин товаров
/shopdesc — описание всех товаров
/faq — частые вопросы
/discounts — активные скидки
/tokenrate — курс 💮
/transfer — перевод 💮
/transferinfo — о переводах
/changelog — обновления
/promo — промокод
/commands — команды

👥 ДЛЯ ЧАТОВ:
/chatowner — владельцы
/chatshop — магазин чата
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

def get_transfer_tax(amount):
    for bracket in TRANSFER_TAX_BRACKETS:
        if bracket["min"] <= amount <= bracket["max"]:
            tax = int(amount * bracket["tax_percent"] / 100)
            return tax, bracket["tax_percent"], bracket["name"]
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
        active_users = sum(1 for u in users.values() if u.get("requests_today", 0) > 0)
        total_users = len(users)
        
        base_rate = 0.01
        supply_factor = max(0.3, min(3.0, 15000 / max(total_tokens, 500))) if total_tokens > 0 else 1.0
        activity_factor = 0.7 + ((active_users / max(total_users, 1)) * 0.6) if total_users > 0 else 1.0
        burn_factor = 0.8 + ((total_spent / max(total_earned, 1)) * 0.4) if total_earned > 0 else 1.0
        
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
            "total_supply": total_tokens, "market_cap": market_cap, "change_24h": change_24h, "trend": trend,
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
    if last_update:
        return datetime.fromisoformat(last_update).replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=2)
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
        [KeyboardButton("🎫 Скидки"), KeyboardButton("💮 Курс NBT")],
    ], resize_keyboard=True)

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("ℹ️ О боте", callback_data="about"), InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🧠 Модели", callback_data="models"), InlineKeyboardButton("💎 Премиум", callback_data="premium_info")],
        [InlineKeyboardButton("🎫 Скидки", callback_data="discounts_info"), InlineKeyboardButton("💮 Курс NBT", callback_data="tokenrate")],
        [InlineKeyboardButton("💸 Перевод", callback_data="transfer"), InlineKeyboardButton("📋 Команды", callback_data="commands")],
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
    
    cats = {
        "private": [("📝 Текст", "text"), ("🎨 Фото", "image"), ("⭐ Премиум", "premium")],
        "chat": [("👥 Запросы", "chat"), ("🖼️ Фото", "chat_image"), ("⭐ Премиум", "chat_premium")],
    }
    
    for label, cat in cats.get(location, cats["private"]):
        items_in_cat = False
        for item_id, item in shop_items.items():
            if item["category"] == cat and item.get("location") == location:
                if not items_in_cat:
                    keyboard.append([InlineKeyboardButton(f"── {label} ──", callback_data="none")])
                    items_in_cat = True
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
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Подтвердить перевод", callback_data=f"transfer_confirm_{to_id}_{amount}")],
        [InlineKeyboardButton("❌ Отменить", callback_data="transfer_cancel")],
    ])

def earn_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🎁 Ежедневный бонус", callback_data="daily_bonus"), InlineKeyboardButton("👥 Реферальная ссылка", callback_data="ref_link")], [InlineKeyboardButton("💸 Перевод", callback_data="transfer"), InlineKeyboardButton("🔙 Назад", callback_data="menu")]])

def limit_reached_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🛒 Купить запросы", callback_data="shop"), InlineKeyboardButton("💰 Заработать", callback_data="earn")], [InlineKeyboardButton("💎 Премиум", callback_data="premium_info")]])

async def transfer_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type
    
    to_id = None; amount = None
    
    if chat_type in ["group", "supergroup"]:
        if update.message.reply_to_message:
            to_id = update.message.reply_to_message.from_user.id
            if context.args and len(context.args) >= 1:
                try: amount = int(context.args[0])
                except: await update.message.reply_text("❌ /transfer КОЛИЧЕСТВО"); return
        else:
            await update.message.reply_text("💸 Ответьте на сообщение и /transfer КОЛИЧЕСТВО"); return
    else:
        if not context.args or len(context.args) < 2:
            await update.message.reply_text("💸 /transfer ID КОЛИЧЕСТВО\nПример: /transfer 1671403667 100\n\n⚠️ Проверяйте ID!"); return
        try: to_id = int(context.args[0]); amount = int(context.args[1])
        except: await update.message.reply_text("❌ /transfer ID КОЛИЧЕСТВО"); return
    
    if not to_id or not amount: return
    if amount < MIN_TRANSFER: await update.message.reply_text(f"❌ Мин: {MIN_TRANSFER} 💮"); return
    if amount > MAX_TRANSFER: await update.message.reply_text(f"❌ Макс: {MAX_TRANSFER} 💮"); return
    if to_id == user_id: await update.message.reply_text("❌ Нельзя себе!"); return
    
    sender = get_user(user_id)
    if sender.get("daily_transfer_total", 0) + amount > DAILY_TRANSFER_LIMIT:
        await update.message.reply_text(f"❌ Лимит дня: {DAILY_TRANSFER_LIMIT} 💮"); return
    
    tax, tax_percent, tax_name = get_transfer_tax(amount)
    if sender.get("tokens", 0) < amount: await update.message.reply_text(f"❌ Недостаточно!"); return
    
    receiver = get_user(to_id)
    if not receiver: await update.message.reply_text("❌ Получатель не найден!"); return
    
    final_amount = amount - tax
    receiver_name = receiver.get("username") or f"ID:{to_id}"
    tax_info = f"Налог: {tax} 💮 ({tax_percent}%)" if tax > 0 else "Без налога"
    
    await update.message.reply_text(
        f"{TRANSFER_WARNING}\n\n📋 ДЕТАЛИ:\n━━━━━━━━━━━━━━━━\n"
        f"👤 Получатель: {receiver_name}\n🆔 ID: {to_id}\n"
        f"💸 Сумма: {amount} 💮\n📊 {tax_info}\n"
        f"💰 Получит: {final_amount} 💮\n💳 Спишется: {amount} 💮\n\n"
        f"Подтвердите или отмените:",
        reply_markup=transfer_confirm_keyboard(to_id, amount)
    )

async def transfer_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["waiting_transfer"] = True
    await update.message.reply_text("💸 Отправьте ID и сумму:\nID КОЛИЧЕСТВО\n\n⚠️ Проверяйте ID!")

async def transfer_info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(TRANSFER_INFO)

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
        chat_premium = "💎 Активен" if is_chat_premium(update.effective_chat.id) else "Не активен"
        await update.message.reply_text(f"🧠 NeBlock AI V{BOT_VERSION} в чате!\n💬 @{context.bot.username} вопрос\n🎨 @{context.bot.username} нарисуй\n💸 Переводы!\n💎 Премиум: {chat_premium}\n👑 /chatowner | 🛒 /chatshop")
        return
    
    premium = "💎 Активен" if is_premium(user_id) else "Не активен"
    rate_data = get_token_rate(); rate = rate_data.get("rate", 0.01)
    
    await update.message.reply_text(
        f"🧠 NeBlock AI V{BOT_VERSION}\n━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💬 Текст | 🎨 Фото | 💸 Переводы\n"
        f"💎 Премиум ЛС: {premium}\n\n"
        f"💰 Баланс: {user.get('tokens', 0)} 💮 (~${user.get('tokens', 0) * rate:.2f})\n"
        f"💮 1 NBT = ${rate:.8f}\n"
        f"📊 Лимиты: {DAILY_LIMIT} вопр. + {IMAGE_DAILY_LIMIT} фото/день\n\n"
        f"👇 Выбери модель:",
        reply_markup=main_reply_keyboard()
    )

async def tokenrate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rate_data = get_token_rate(); history = load_json(TOKEN_HISTORY_FILE); shop_items = get_shop_items()
    rate = rate_data.get("rate", 0.01); supply = rate_data.get("total_supply", 0)
    market_cap = rate_data.get("market_cap", 0); updated = rate_data.get("updated_at", "")
    updated_time = datetime.fromisoformat(updated).strftime("%d.%m.%Y %H:%M") if updated else "Нет"
    
    text = (f"💮 КУРС NBT\n━━━━━━━━━━━━━━━━\n\n💰 1 NBT = ${rate:.8f}\n"
            f"💎 Кап: ${market_cap:,.2f}\n🪙 В обороте: {supply:,} NBT\n🕐 {updated_time}\n\n"
            f"📋 Цены:\n📝 +5: {shop_items.get('extra5', {}).get('price', '?')} 💮\n"
            f"⭐ Премиум: {shop_items.get('premium_day', {}).get('price', '?')} 💮\n\n📈 7д:\n")
    for date, h in sorted(history.items())[-7:]:
        text += f"{date}: ${h.get('rate', 0):.8f}\n"
    await update.message.reply_text(text)

async def discounts_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    discounts = get_discounts(); active = {k: v for k, v in discounts.items() if k not in ["last_update", "generated_at"]}
    text = f"🎫 СКИДКИ\n\n🔄 {get_next_update_time().strftime('%d.%m.%Y 9:00 МСК')}\n\n"
    if not active: text += "Нет."
    else:
        for item_id, disc in sorted(active.items(), key=lambda x: x[1]["percent"], reverse=True):
            item = get_shop_items().get(item_id)
            if item: text += f"{disc.get('color', '🟢')} {item['icon']} {item['name']}: -{disc['percent']}%\n"
    await update.message.reply_text(text)

async def promo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["waiting_promo"] = True
    await update.message.reply_text("🎟 Отправьте промокод.")

async def changelog_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text(CHANGELOG)
async def commands_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text(COMMANDS_LIST)
async def shopdesc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("📋 /shop — магазин")

async def chatowner_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]: return
    chat_id = update.effective_chat.id; user_id = update.effective_user.id; add_chat_owner(chat_id, user_id)
    chats = load_chats(); c = chats.get(str(chat_id), {})
    owners = c.get("owners", []) if isinstance(c, dict) else c
    premium = "💎 Активен" if is_chat_premium(chat_id) else "Не активен"
    text = f"👑 Владельцы:\n"
    for i, oid in enumerate(owners, 1): text += f"{i}. ID: {oid}\n"
    text += f"\n💎 Премиум: {premium}\n/chatshop"
    await update.message.reply_text(text)

async def chatshop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]: return
    chat_id = update.effective_chat.id; user_id = update.effective_user.id; add_chat_owner(chat_id, user_id)
    if not is_chat_owner(chat_id, user_id): return
    await update.message.reply_text(f"🛒 Магазин чата\n💰 {get_tokens(user_id)} 💮", reply_markup=shop_keyboard("chat"))

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
        await update.message.reply_text(f"👤 @{un}\n💰 {u.get('tokens', 0)} 💮\n⚠️ {u.get('warnings', 0)}/5")
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
    await update.message.reply_text(f"📊 Статистика\n👥 {len(users)}\n💮 В обороте: {rate_data.get('total_supply', 0):,} NBT")

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
    if text == "💰 Заработать": await update.message.reply_text(f"💰 Заработок\n💎 {get_tokens(user_id)} 💮\n🎁 Бонус: {DAILY_BONUS_MIN}-{DAILY_BONUS_MAX}/день\n👥 Рефералы: +{REFERRAL_BONUS} 💮\n💸 Переводы", reply_markup=earn_keyboard()); return True
    if text == "💸 Перевод": await transfer_button_handler(update, context); return True
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
    
    if data.startswith("transfer_confirm_"):
        parts = data.split("_")
        if len(parts) >= 4:
            to_id = int(parts[2]); amount = int(parts[3])
            if amount < MIN_TRANSFER or amount > MAX_TRANSFER: await query.edit_message_text("❌ Ошибка суммы."); return
            if to_id == user_id: await query.edit_message_text("❌ Нельзя себе!"); return
            
            sender = get_user(user_id)
            if sender.get("daily_transfer_total", 0) + amount > DAILY_TRANSFER_LIMIT: await query.edit_message_text("❌ Лимит."); return
            
            tax, tax_percent, tax_name = get_transfer_tax(amount)
            if sender.get("tokens", 0) < amount: await query.edit_message_text("❌ Недостаточно."); return
            
            receiver = get_user(to_id)
            if not receiver: await query.edit_message_text("❌ Не найден."); return
            
            final_amount = amount - tax
            users = load_users()
            uid_from = str(user_id); uid_to = str(to_id)
            users[uid_from]["tokens"] = users[uid_from].get("tokens", 0) - amount
            users[uid_from]["spent_tokens"] = users[uid_from].get("spent_tokens", 0) + amount
            users[uid_from]["daily_transfer_total"] = users[uid_from].get("daily_transfer_total", 0) + amount
            users[uid_to]["tokens"] = users[uid_to].get("tokens", 0) + final_amount
            users[uid_to]["earned_tokens"] = users[uid_to].get("earned_tokens", 0) + final_amount
            save_users(users)
            log_transfer(user_id, to_id, amount, tax, final_amount)
            
            tax_info = f"\n📊 Налог: {tax} 💮 ({tax_percent}%)" if tax > 0 else "\n📊 Без налога"
            await query.edit_message_text(f"✅ ПЕРЕВОД ВЫПОЛНЕН!\n━━━━━━━━━━━━━━━━\n👤 {to_id}\n💸 {amount} 💮\n💰 Зачислено: {final_amount} 💮{tax_info}\n💎 Баланс: {get_tokens(user_id)} 💮")
            try:
                sn = sender.get("username") or f"ID:{user_id}"
                await context.bot.send_message(to_id, f"📨 Вам перевели 💮\n👤 @{sn}\n💰 +{final_amount} 💮\n💎 Баланс: {get_tokens(to_id)} 💮")
            except: pass
        return
    
    if data == "menu": await query.edit_message_text(f"🧠 NeBlock AI V{BOT_VERSION}\n💰 {get_tokens(user_id)} 💮", reply_markup=main_menu())
    elif data == "about": await query.edit_message_text(f"ℹ️ NeBlock AI V{BOT_VERSION}\n\n💬 Текст\n🎨 Фото\n💸 Переводы\n💮 NBT\n📚 /faq — все вопросы", reply_markup=back_button())
    elif data == "models": await query.edit_message_text(f"🧠 МОДЕЛИ\n\n💬 NeBlock AI V2 — текст\n🎨 NeBlock Images V2 — фото\n\n📚 /faq — подробнее", reply_markup=back_button())
    elif data == "tokenrate":
        rd = get_token_rate(); rate = rd.get("rate", 0.01)
        await query.edit_message_text(f"💮 NBT\n💰 1 = ${rate:.8f}\n💎 Кап: ${rd.get('market_cap', 0):,.2f}", reply_markup=back_button())
    elif data == "transfer":
        context.user_data["waiting_transfer"] = True
        await query.edit_message_text("💸 ПЕРЕВОД\n\nОтправьте ID и сумму:\nID КОЛИЧЕСТВО\n\n⚠️ Проверяйте ID!", reply_markup=back_button())
    elif data == "commands": await query.edit_message_text(COMMANDS_LIST, reply_markup=back_button())
    elif data == "changelog": await query.edit_message_text(CHANGELOG, reply_markup=back_button())
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
        await query.edit_message_text(f"📊 Статистика\n💬 {u.get('requests_today', 0)}\n🎨 {u.get('image_requests_today', 0)}\n💰 {u.get('tokens', 0)} 💮\n💸 Переводов: {u.get('daily_transfer_total', 0)}", reply_markup=back_button())
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
        if chat_type in ["group", "supergroup"] and update.message.reply_to_message:
            to_id = update.message.reply_to_message.from_user.id
            if len(parts) >= 1:
                try:
                    amount = int(parts[0])
                    context.args = [str(to_id), str(amount)]
                    await transfer_cmd(update, context)
                    return
                except: await update.message.reply_text("❌ Неверная сумма."); return
        elif len(parts) >= 2:
            try:
                to_id = int(parts[0]); amount = int(parts[1])
                context.args = [str(to_id), str(amount)]
                await transfer_cmd(update, context)
                return
            except: await update.message.reply_text("❌ ID КОЛИЧЕСТВО"); return
        else: await update.message.reply_text("❌ ID КОЛИЧЕСТВО"); return
    
    if chat_type == "private":
        if await reply_button_handler(update, context): return
    
    is_image_request = False; should_respond = False
    
    if chat_type in ["group", "supergroup"]:
        mention = f"@{bot_username}"
        text_lower = text.lower()
        if mention in text: text = text.replace(mention, "").strip(); should_respond = True
        if not should_respond:
            for kw in ["бот ", "нейробот ", "нейросеть ", "ai ", "нарисуй "]:
                if text_lower.startswith(kw): text = text[len(kw):].strip(); should_respond = True; break
        if not should_respond: return
        if text_lower.startswith("нарисуй"): text = text[7:].strip(); is_image_request = True
        if not text:
            await update.message.reply_text(f"🧠 NeBlock AI V2!\n💬 @{bot_username} вопрос\n🎨 @{bot_username} нарисуй\n💸 /transfer", reply_to_message_id=update.message.message_id)
            return
    
    user = get_user(user_id)
    if context.user_data.get("waiting_promo"): context.user_data["waiting_promo"] = False; success, result = use_promo(user_id, text); await update.message.reply_text(f"🎟 +{result} 💮!" if success else f"❌ {result}"); return
    
    if is_image_request or (chat_type == "private" and (user.get("current_model") == "image" or user.get("waiting_for_image"))):
        if chat_type == "private": users = load_users(); users[str(user_id)]["waiting_for_image"] = False; save_users(users)
        if not can_image_request(user_id, chat_type, chat_id):
            rem = image_remaining(user_id, chat_type, chat_id)
            await update.message.reply_text(f"🚫 Лимит фото!\n📊 Осталось: {rem}", reply_to_message_id=update.message.message_id if chat_type != "private" else None, reply_markup=limit_reached_keyboard() if chat_type == "private" else None); return
        msg = await update.message.reply_text("🎨 Генерирую...", reply_to_message_id=update.message.message_id if chat_type != "private" else None)
        try:
            image_bytes, error = await generate_image(text)
            if image_bytes: add_image_request(user_id, chat_type); await msg.delete(); rem = image_remaining(user_id, chat_type, chat_id); await update.message.reply_photo(photo=image_bytes, caption=f"🎨 NeBlock Images V2\n📝 {text[:200]}\n📊 Осталось: {rem}", reply_to_message_id=update.message.message_id if chat_type != "private" else None)
            else: await msg.edit_text("❌ Ошибка")
        except:
            try: await msg.delete()
            except: pass
            await update.message.reply_text("❌ Ошибка.")
        return
    
    if not can_request(user_id, chat_type, chat_id):
        rem = remaining(user_id, chat_type, chat_id)
        await update.message.reply_text(f"🚫 Лимит!\n📊 Осталось: {rem}", reply_markup=limit_reached_keyboard() if chat_type == "private" else None, reply_to_message_id=update.message.message_id if chat_type != "private" else None); return
    
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
    app.add_handler(CommandHandler("tokenrate", tokenrate_cmd))
    app.add_handler(CommandHandler("discounts", discounts_cmd))
    app.add_handler(CommandHandler("transfer", transfer_cmd))
    app.add_handler(CommandHandler("transferinfo", transfer_info_cmd))
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
