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
# 🧠 NeBlock AI V2.7 - Конфигурация
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
ADMIN_IDS = [1671403667]
START_BONUS = 50
DAILY_BONUS_MIN = 5
DAILY_BONUS_MAX = 15
REFERRAL_BONUS = 25
INVITED_BONUS = 10
BOT_VERSION = "2.7"

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

Версия 2.7 (21.07.2026)
• Улучшенный динамический курс 💮
• История курса за 7 дней
• Рыночная капитализация
• Индекс волатильности
• Тренд курса (рост/падение)

Версия 2.6 (21.07.2026)
• Динамический курс токена
• Цены в NBT
• Токеномика

Версия 2.0 (15.07.2026)
• Две модели V2
• Премиум и магазин
"""

FAQ_TEXT = f"""
📚 ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ
━━━━━━━━━━━━━━━━━━━━

❓ Что такое 💮 NeBlock Token (NBT)?
Внутренняя валюта платформы с динамическим курсом.
Курс обновляется раз в сутки и зависит от:
• Количества токенов в обороте
• Активности пользователей
• Рыночной волатильности

❓ Где посмотреть курс?
💮 /tokenrate — текущий курс, капитализация, история

❓ Какие лимиты?
• ЛС: {DAILY_LIMIT} текстовых + {IMAGE_DAILY_LIMIT} фото/день
• Чаты: {CHAT_DAILY_LIMIT} текстовых + {CHAT_IMAGE_LIMIT} фото/день
"""

DISCOUNT_TYPES = {
    "regular": {"name": "Обычная скидка", "min": 5, "max": 25, "color": "🟢", "chance": 40, "icon": "🏷️"},
    "super": {"name": "Супер-скидка", "min": 30, "max": 50, "color": "🔴", "chance": 20, "icon": "🔥"},
    "flash": {"name": "Флеш-скидка", "min": 40, "max": 70, "color": "⚡", "chance": 8, "icon": "⏰"},
    "bundle": {"name": "Скидка на набор", "min": 15, "max": 35, "color": "📦", "chance": 12, "icon": "🎁"},
    "premium_discount": {"name": "Премиум-скидка", "min": 10, "max": 30, "color": "👑", "chance": 5, "icon": "💎"},
    "legendary": {"name": "ЛЕГЕНДАРНАЯ СКИДКА", "min": 100, "max": 100, "color": "🌟", "chance": 0.5, "icon": "💫"},
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("NeBlockAI")

client = openai.OpenAI(
    api_key=YANDEX_API_KEY, base_url="https://ai.api.cloud.yandex.net/v1",
    project=YANDEX_FOLDER, timeout=60.0,
)

# ═══════════════════════════════════════════
# 💮 УЛУЧШЕННЫЙ ДИНАМИЧЕСКИЙ КУРС ТОКЕНА
# ═══════════════════════════════════════════

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f: return json.load(f)
    return {}

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f: json.dump(data, f, indent=2, ensure_ascii=False)

def load_users(): return load_json(DATA_FILE)
def save_users(users): save_json(DATA_FILE, users)

def get_token_rate():
    """Улучшенный курс токена с историей и рыночными метриками"""
    rate_data = load_json(TOKEN_RATE_FILE)
    history = load_json(TOKEN_HISTORY_FILE)
    today = datetime.now().strftime("%Y-%m-%d")
    
    if rate_data.get("date") != today:
        users = load_users()
        total_tokens = sum(u.get("tokens", 0) for u in users.values())
        total_earned = sum(u.get("earned_tokens", 0) for u in users.values())
        total_spent = sum(u.get("spent_tokens", 0) for u in users.values())
        active_users = sum(1 for u in users.values() if u.get("requests_today", 0) > 0)
        total_users = len(users)
        
        # 1. Базовый курс
        base_rate = 0.01
        
        # 2. Фактор предложения (дефляция)
        if total_tokens > 0:
            supply_factor = max(0.3, min(3.0, 15000 / max(total_tokens, 500)))
        else:
            supply_factor = 1.0
        
        # 3. Фактор активности (чем активнее — тем выше курс)
        if total_users > 0:
            activity_ratio = active_users / max(total_users, 1)
            activity_factor = 0.7 + (activity_ratio * 0.6)
        else:
            activity_factor = 1.0
        
        # 4. Коэффициент сжигания (чем больше потрачено — тем выше курс)
        if total_earned > 0:
            burn_ratio = total_spent / max(total_earned, 1)
            burn_factor = 0.8 + (burn_ratio * 0.4)
        else:
            burn_factor = 1.0
        
        # 5. Волатильность на основе истории
        volatility = 1.0
        if history:
            rates = [h.get("rate", base_rate) for h in history.values() if h.get("rate")]
            if len(rates) > 1:
                avg_rate = sum(rates) / len(rates)
                std_dev = math.sqrt(sum((r - avg_rate) ** 2 for r in rates) / len(rates))
                volatility = 1.0 + (std_dev / max(avg_rate, 0.0001)) * 0.5
        
        # 6. Случайный рыночный шум ±10%
        market_noise = random.uniform(0.90, 1.10)
        
        # 7. Итоговый курс
        rate = round(base_rate * supply_factor * activity_factor * burn_factor * volatility * market_noise, 8)
        rate = max(0.0001, min(1.0, rate))
        
        # 8. Рыночная капитализация
        market_cap = round(total_tokens * rate, 2)
        
        # 9. Изменение за 24 часа
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_rate = history.get(yesterday, {}).get("rate", rate)
        change_24h = round(((rate - yesterday_rate) / max(yesterday_rate, 0.0001)) * 100, 2)
        
        # 10. Тренд
        if change_24h > 0.5:
            trend = "📈 Рост"
        elif change_24h < -0.5:
            trend = "📉 Падение"
        else:
            trend = "📊 Стабильно"
        
        rate_data = {
            "date": today,
            "rate": rate,
            "total_supply": total_tokens,
            "total_earned": total_earned,
            "total_spent": total_spent,
            "market_cap": market_cap,
            "change_24h": change_24h,
            "trend": trend,
            "active_users": active_users,
            "total_users": total_users,
            "supply_factor": round(supply_factor, 4),
            "activity_factor": round(activity_factor, 4),
            "burn_factor": round(burn_factor, 4),
            "volatility_index": round(volatility, 4),
            "updated_at": datetime.now().isoformat(),
        }
        save_json(TOKEN_RATE_FILE, rate_data)
        
        # Сохраняем в историю
        history[today] = {
            "rate": rate,
            "supply": total_tokens,
            "market_cap": market_cap,
            "change_24h": change_24h,
        }
        # Оставляем только последние 30 дней
        if len(history) > 30:
            history = dict(sorted(history.items())[-30:])
        save_json(TOKEN_HISTORY_FILE, history)
        
        logger.info(f"💮 Курс обновлён: 1 NBT = ${rate:.8f} | Кап: ${market_cap:.2f} | Изм: {change_24h:+.2f}%")
    
    return rate_data

def get_item_price(item_id):
    rate_data = get_token_rate()
    rate = rate_data.get("rate", 0.01)
    base_usd = BASE_PRICES_USD.get(item_id, 10)
    token_price = max(1, int(base_usd / 100 / rate))
    return token_price

def get_shop_items():
    items = {}
    for item_id, item in SHOP_ITEMS_BASE.items():
        dynamic_price = get_item_price(item_id)
        items[item_id] = {**item, "price": dynamic_price}
    return items

SHOP_ITEMS_BASE = {
    "extra5": {"name": "+5 запросов", "price": 10, "icon": "📝", "category": "text", "desc": "5 текстовых запросов.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "private"},
    "extra10": {"name": "+10 запросов", "price": 18, "icon": "📝", "category": "text", "desc": "10 текстовых запросов.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "private"},
    "extra50": {"name": "+50 запросов", "price": 80, "icon": "📝", "category": "text", "desc": "50 запросов.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "private"},
    "unlimited_1h": {"name": "Безлимит текст 1ч", "price": 30, "icon": "♾️", "category": "text", "desc": "Безлимит на 1 час.", "warning": "⚠️ Действует 1 час.", "location": "private"},
    "unlimited_24h": {"name": "Безлимит текст 24ч", "price": 100, "icon": "♾️", "category": "text", "desc": "Безлимит на 24 часа.", "warning": "⚠️ Действует 24 часа.", "location": "private"},
    "unlimited_7d": {"name": "Безлимит текст 7д", "price": 500, "icon": "♾️", "category": "text", "desc": "Безлимит на 7 дней.", "warning": "⚠️ Действует 7 дней.", "location": "private"},
    "image1": {"name": "1 генерация фото", "price": 15, "icon": "🎨", "category": "image", "desc": "1 генерация.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "private"},
    "image5": {"name": "5 генераций фото", "price": 60, "icon": "🎨", "category": "image", "desc": "5 генераций.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "private"},
    "image20": {"name": "20 генераций фото", "price": 200, "icon": "🎨", "category": "image", "desc": "20 генераций.", "warning": "⚠️ Сгорают в 00:00 МСК.", "location": "private"},
    "image_unlimited_1h": {"name": "Безлимит фото 1ч", "price": 50, "icon": "♾️", "category": "image", "desc": "Безлимит фото на 1 час.", "warning": "⚠️ Действует 1 час.", "location": "private"},
    "premium_day": {"name": "Премиум ЛС 1 день", "price": 200, "icon": "⭐", "category": "premium", "desc": "Безлимит на 24ч.", "warning": "⚠️ 24 часа. Только ЛС.", "location": "private"},
    "premium_week": {"name": "Премиум ЛС 7 дней", "price": 1000, "icon": "⭐", "category": "premium", "desc": "Безлимит на 7 дней.", "warning": "⚠️ 7 дней. Только ЛС.", "location": "private"},
    "premium_forever": {"name": "Премиум ЛС навсегда", "price": 2500, "icon": "👑", "category": "premium", "desc": "Безлимит навсегда.", "warning": "⚠️ Только ЛС. Бессрочно.", "location": "private"},
    "chat_extra10": {"name": "+10 запросов в чатах", "price": 15, "icon": "👥", "category": "chat", "desc": "10 запросов для всех.", "warning": "⚠️ Сгорают в 00:00. Владелец.", "location": "chat"},
    "chat_extra50": {"name": "+50 запросов в чатах", "price": 60, "icon": "👥", "category": "chat", "desc": "50 запросов для всех.", "warning": "⚠️ Сгорают в 00:00. Владелец.", "location": "chat"},
    "chat_unlimited_1h": {"name": "Безлимит чат 1ч", "price": 40, "icon": "♾️", "category": "chat", "desc": "Безлимит для всех на 1ч.", "warning": "⚠️ 1 час. Владелец.", "location": "chat"},
    "chat_unlimited_24h": {"name": "Безлимит чат 24ч", "price": 150, "icon": "♾️", "category": "chat", "desc": "Безлимит для всех на 24ч.", "warning": "⚠️ 24 часа. Владелец.", "location": "chat"},
    "chat_image5": {"name": "5 фото в чатах", "price": 50, "icon": "🖼️", "category": "chat_image", "desc": "5 фото для всех.", "warning": "⚠️ Сгорают в 00:00. Владелец.", "location": "chat"},
    "chat_image20": {"name": "20 фото в чатах", "price": 180, "icon": "🖼️", "category": "chat_image", "desc": "20 фото для всех.", "warning": "⚠️ Сгорают в 00:00. Владелец.", "location": "chat"},
    "chat_premium_day": {"name": "Премиум чат 1 день", "price": 300, "icon": "⭐", "category": "chat_premium", "desc": "Безлимит для всех на 24ч.", "warning": "⚠️ 24 часа. Владелец.", "location": "chat"},
    "chat_premium_week": {"name": "Премиум чат 7 дней", "price": 1500, "icon": "⭐", "category": "chat_premium", "desc": "Безлимит для всех на 7д.", "warning": "⚠️ 7 дней. Владелец.", "location": "chat"},
    "chat_premium_forever": {"name": "Премиум чат навсегда", "price": 3500, "icon": "👑", "category": "chat_premium", "desc": "Безлимит навсегда.", "warning": "⚠️ Владелец. Бессрочно.", "location": "chat"},
}

def load_promos(): return load_json(PROMO_FILE)
def save_promos(promos): save_json(PROMO_FILE, promos)
def load_chats(): return load_json(CHATS_FILE)
def save_chats(chats): save_json(CHATS_FILE, chats)
def load_discounts(): return load_json(DISCOUNTS_FILE)
def save_discounts(discounts): save_json(DISCOUNTS_FILE, discounts)

def generate_discounts():
    all_items = list(SHOP_ITEMS_BASE.keys())
    discounts = {"generated_at": datetime.now().isoformat()}
    used_items = set()
    
    legendary_roll = random.uniform(0, 100)
    if legendary_roll < DISCOUNT_TYPES["legendary"]["chance"]:
        item_id = random.choice(all_items)
        original = get_item_price(item_id)
        discounts[item_id] = {
            "percent": 100, "original": original, "new_price": 0,
            "type": "legendary", "type_name": "ЛЕГЕНДАРНАЯ СКИДКА",
            "color": "🌟", "icon": "💫",
            "expires": (datetime.now() + timedelta(hours=3)).isoformat(),
            "special": True
        }
        used_items.add(item_id)
    
    available_types = []
    for dtype, dconfig in DISCOUNT_TYPES.items():
        if dtype == "legendary": continue
        if random.randint(1, 100) <= dconfig["chance"]: available_types.append(dtype)
    if not available_types: available_types = ["regular"]
    
    num_discounts = random.randint(3, 5)
    
    for _ in range(num_discounts):
        if len(used_items) >= len(all_items): break
        disc_type = random.choice(available_types)
        dconfig = DISCOUNT_TYPES[disc_type]
        available_items = [item for item in all_items if item not in used_items]
        if not available_items: break
        item_id = random.choice(available_items)
        used_items.add(item_id)
        percent = random.randint(dconfig["min"], dconfig["max"])
        original = get_item_price(item_id)
        new_price = max(1, int(original * (1 - percent / 100)))
        expires = None
        if disc_type == "flash": expires = (datetime.now() + timedelta(hours=24)).isoformat()
        discounts[item_id] = {
            "percent": percent, "original": original, "new_price": new_price,
            "type": disc_type, "type_name": dconfig["name"], "color": dconfig["color"],
            "icon": dconfig["icon"], "expires": expires,
        }
    
    return discounts

def get_discounts():
    discounts = load_discounts()
    last_update = discounts.get("last_update", "")
    now = datetime.now()
    
    if discounts:
        to_delete = []
        for item_id, disc in discounts.items():
            if item_id in ["last_update", "generated_at"]: continue
            if disc.get("expires") and now > datetime.fromisoformat(disc["expires"]): to_delete.append(item_id)
        for item_id in to_delete: del discounts[item_id]
        if to_delete: save_discounts(discounts)
    
    if last_update:
        last_date = datetime.fromisoformat(last_update)
        next_update = last_date.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=2)
        if now >= next_update:
            new_discounts = generate_discounts()
            new_discounts["last_update"] = now.strftime("%Y-%m-%d")
            save_discounts(new_discounts)
            return new_discounts
    else:
        new_discounts = generate_discounts()
        new_discounts["last_update"] = now.strftime("%Y-%m-%d")
        save_discounts(new_discounts)
        return new_discounts
    
    if not discounts or "last_update" not in discounts:
        discounts = generate_discounts()
        discounts["last_update"] = now.strftime("%Y-%m-%d")
        save_discounts(discounts)
    
    return discounts

def get_next_update_time():
    now = datetime.now()
    discounts = load_discounts()
    last_update = discounts.get("last_update", "")
    if last_update:
        last_date = datetime.fromisoformat(last_update)
        return last_date.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=2)
    next_update = now.replace(hour=9, minute=0, second=0, microsecond=0)
    if now >= next_update: next_update += timedelta(days=2)
    return next_update

def get_discounted_price(item_id):
    discounts = get_discounts()
    shop_items = get_shop_items()
    if item_id in discounts and item_id not in ["last_update", "generated_at"]:
        disc = discounts[item_id]
        if disc.get("expires") and datetime.now() > datetime.fromisoformat(disc["expires"]):
            return shop_items[item_id]["price"], 0, None
        return disc["new_price"], disc["percent"], disc
    return shop_items[item_id]["price"], 0, None

def get_user(user_id):
    users = load_users(); uid = str(user_id)
    defaults = {
        "joined": datetime.now().isoformat(), "username": None,
        "requests_today": 0, "extra_requests": 0,
        "image_requests_today": 0, "extra_image_requests": 0,
        "chat_requests_today": 0, "extra_chat_requests": 0,
        "chat_image_requests_today": 0, "extra_chat_image_requests": 0,
        "unlimited_until": None, "image_unlimited_until": None,
        "chat_unlimited_until": None, "chat_image_unlimited_until": None,
        "premium_until": None, "chat_premium_until": None,
        "last_request": None, "total_requests": 0, "total_images": 0,
        "reset_date": datetime.now().strftime("%Y-%m-%d"),
        "tokens": START_BONUS, "daily_bonus_claimed": None,
        "daily_bonus_streak": 0, "last_bonus_date": None,
        "referral_code": "".join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(8)),
        "referred_by": None, "referrals": 0, "earned_tokens": 0, "spent_tokens": 0,
        "used_promos": [], "waiting_for_image": False, "current_model": "text",
        "warnings": 0, "muted_until": None, "banned": False,
    }
    if uid not in users: users[uid] = defaults.copy(); save_users(users)
    else:
        for key, value in defaults.items():
            if key not in users[uid]: users[uid][key] = value
        save_users(users)
    today = datetime.now().strftime("%Y-%m-%d")
    if users[uid].get("reset_date") != today:
        for field in ["requests_today", "extra_requests", "image_requests_today", "extra_image_requests", "chat_requests_today", "extra_chat_requests", "chat_image_requests_today", "extra_chat_image_requests"]:
            users[uid][field] = 0
        users[uid]["reset_date"] = today; save_users(users)
    return users[uid]

def is_premium(user_id):
    user = get_user(user_id); premium = user.get("premium_until")
    if premium:
        try:
            if datetime.now() < datetime.fromisoformat(premium): return True
        except: pass
    return False

def is_chat_premium(chat_id):
    chats = load_chats(); chat_data = chats.get(str(chat_id), {})
    if isinstance(chat_data, list): return False
    premium = chat_data.get("premium_until")
    if premium:
        try:
            if datetime.now() < datetime.fromisoformat(premium): return True
        except: pass
    return False

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
    user = get_user(user_id)
    if chat_type == "private" and user.get("unlimited_until"):
        try:
            if datetime.now() < datetime.fromisoformat(user["unlimited_until"]): return True
        except: pass
    if chat_type in ["group", "supergroup"] and user.get("chat_unlimited_until"):
        try:
            if datetime.now() < datetime.fromisoformat(user["chat_unlimited_until"]): return True
        except: pass
    if chat_type in ["group", "supergroup"]: return user.get("chat_requests_today", 0) < (CHAT_DAILY_LIMIT + user.get("extra_chat_requests", 0))
    return user.get("requests_today", 0) < (DAILY_LIMIT + user.get("extra_requests", 0))

def can_image_request(user_id, chat_type="private", chat_id=None):
    if chat_type == "private" and is_premium(user_id): return True
    if chat_type in ["group", "supergroup"] and chat_id and is_chat_premium(chat_id): return True
    user = get_user(user_id)
    if chat_type == "private" and user.get("image_unlimited_until"):
        try:
            if datetime.now() < datetime.fromisoformat(user["image_unlimited_until"]): return True
        except: pass
    if chat_type in ["group", "supergroup"] and user.get("chat_image_unlimited_until"):
        try:
            if datetime.now() < datetime.fromisoformat(user["chat_image_unlimited_until"]): return True
        except: pass
    if chat_type in ["group", "supergroup"]: return user.get("chat_image_requests_today", 0) < (CHAT_IMAGE_LIMIT + user.get("extra_chat_image_requests", 0))
    return user.get("image_requests_today", 0) < (IMAGE_DAILY_LIMIT + user.get("extra_image_requests", 0))

def remaining(user_id, chat_type="private", chat_id=None):
    if chat_type == "private" and is_premium(user_id): return "премиум"
    if chat_type in ["group", "supergroup"] and chat_id and is_chat_premium(chat_id): return "премиум"
    user = get_user(user_id)
    if chat_type == "private" and user.get("unlimited_until"):
        try:
            if datetime.now() < datetime.fromisoformat(user["unlimited_until"]): return "безлимит"
        except: pass
    if chat_type in ["group", "supergroup"] and user.get("chat_unlimited_until"):
        try:
            if datetime.now() < datetime.fromisoformat(user["chat_unlimited_until"]): return "безлимит"
        except: pass
    if chat_type in ["group", "supergroup"]: return max(0, CHAT_DAILY_LIMIT + user.get("extra_chat_requests", 0) - user.get("chat_requests_today", 0))
    return max(0, DAILY_LIMIT + user.get("extra_requests", 0) - user.get("requests_today", 0))

def image_remaining(user_id, chat_type="private", chat_id=None):
    if chat_type == "private" and is_premium(user_id): return "премиум"
    if chat_type in ["group", "supergroup"] and chat_id and is_chat_premium(chat_id): return "премиум"
    user = get_user(user_id)
    if chat_type == "private" and user.get("image_unlimited_until"):
        try:
            if datetime.now() < datetime.fromisoformat(user["image_unlimited_until"]): return "безлимит"
        except: pass
    if chat_type in ["group", "supergroup"] and user.get("chat_image_unlimited_until"):
        try:
            if datetime.now() < datetime.fromisoformat(user["chat_image_unlimited_until"]): return "безлимит"
        except: pass
    if chat_type in ["group", "supergroup"]: return max(0, CHAT_IMAGE_LIMIT + user.get("extra_chat_image_requests", 0) - user.get("chat_image_requests_today", 0))
    return max(0, IMAGE_DAILY_LIMIT + user.get("extra_image_requests", 0) - user.get("image_requests_today", 0))

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
    promo = promos[code]
    if promo["max_uses"] > 0 and len(promo["used_by"]) >= promo["max_uses"]: return False, "Лимит"
    if str(user_id) in promo["used_by"]: return False, "Уже использован"
    add_tokens(user_id, promo["amount"]); promo["used_by"].append(str(user_id)); save_promos(promos)
    return True, promo["amount"]

def moderate_content(text):
    for pattern in COMPILED_SEVERE:
        if pattern.search(text): return False, "severe", "Запрещённый контент"
    for pattern in COMPILED_BLOCKED:
        if pattern.search(text): return False, "normal", "Запрещённый контент"
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
    user = get_user(user_id)
    if user.get("banned"): return True
    muted = user.get("muted_until")
    if muted:
        try:
            if datetime.now() < datetime.fromisoformat(muted): return True
        except: pass
    return False

def warn_user(user_id, severity="normal"):
    users = load_users(); uid = str(user_id)
    if severity == "severe": users[uid]["banned"] = True; users[uid]["muted_until"] = (datetime.now() + timedelta(days=7)).isoformat(); save_users(users); return True, "Заблокирован на 7 дней"
    users[uid]["warnings"] = users[uid].get("warnings", 0) + 1
    if users[uid]["warnings"] >= 5: users[uid]["banned"] = True; users[uid]["muted_until"] = (datetime.now() + timedelta(days=3)).isoformat(); save_users(users); return True, "Заблокирован на 3 дня"
    elif users[uid]["warnings"] >= 3: users[uid]["muted_until"] = (datetime.now() + timedelta(hours=6)).isoformat(); save_users(users); return True, "Заблокирован на 6 часов"
    save_users(users); return False, f"Предупреждение {users[uid]['warnings']}/5"

def is_chat_owner(chat_id, user_id):
    chats = load_chats(); chat_data = chats.get(str(chat_id), {})
    if isinstance(chat_data, list): return str(user_id) in chat_data
    return str(user_id) in chat_data.get("owners", [])

def add_chat_owner(chat_id, user_id):
    chats = load_chats(); cid = str(chat_id)
    if cid not in chats or isinstance(chats[cid], list): chats[cid] = {"owners": chats.get(cid, []), "premium_until": None}
    if str(user_id) not in chats[cid]["owners"]: chats[cid]["owners"].append(str(user_id)); save_chats(chats)

async def generate_image(prompt):
    try:
        response = client.images.generate(model=IMAGE_MODEL, prompt=prompt, size="1024x1024")
        return base64.b64decode(response.data[0].b64_json), None
    except Exception as e: return None, str(e)

def main_reply_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("💬 NeBlock AI V2"), KeyboardButton("🎨 NeBlock Images V2")],
        [KeyboardButton("👤 Профиль"), KeyboardButton("🛒 Магазин")],
        [KeyboardButton("💰 Заработать"), KeyboardButton("📚 FAQ")],
        [KeyboardButton("🎫 Скидки"), KeyboardButton("💮 Курс NBT")],
    ], resize_keyboard=True)

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("ℹ️ О боте", callback_data="about"), InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🧠 Модели", callback_data="models"), InlineKeyboardButton("💎 Премиум", callback_data="premium_info")],
        [InlineKeyboardButton("🎫 Скидки", callback_data="discounts_info"), InlineKeyboardButton("💮 Курс NBT", callback_data="tokenrate")],
    ])

def back_button(): return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="menu")]])

def shop_keyboard(location="private"):
    keyboard = []
    discounts = get_discounts()
    shop_items = get_shop_items()
    
    active_discounts = {k: v for k, v in discounts.items() if k not in ["last_update", "generated_at"]}
    if active_discounts:
        legendary = any(d.get("type") == "legendary" for d in active_discounts.values())
        banner = "🌟 ЛЕГЕНДАРНАЯ СКИДКА! 🌟" if legendary else "🎫 Скидки"
        keyboard.append([InlineKeyboardButton(banner, callback_data="discounts_info")])
    
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
                price, percent, disc_info = get_discounted_price(item_id)
                if percent > 0 and disc_info:
                    if disc_info.get("type") == "legendary":
                        price_text = f"🌟 БЕСПЛАТНО! -100%"
                    else:
                        price_text = f"{disc_info.get('color', '🟢')} {price} 💮 -{percent}%"
                else:
                    price_text = f"{price} 💮"
                keyboard.append([InlineKeyboardButton(f"{item['icon']} {item['name']} — {price_text}", callback_data=f"buy_{item_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="menu")])
    return InlineKeyboardMarkup(keyboard)

def confirm_keyboard(item_id):
    return InlineKeyboardMarkup([[InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_{item_id}"), InlineKeyboardButton("❌ Отмена", callback_data="shop")]])

def earn_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🎁 Ежедневный бонус", callback_data="daily_bonus"), InlineKeyboardButton("👥 Реферальная ссылка", callback_data="ref_link")], [InlineKeyboardButton("🔙 Назад", callback_data="menu")]])

def limit_reached_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🛒 Купить запросы", callback_data="shop"), InlineKeyboardButton("💰 Заработать", callback_data="earn")], [InlineKeyboardButton("💎 Премиум", callback_data="premium_info")]])

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
                try: await context.bot.send_message(int(u_id), f"🎉 Новый реферал!\n💰 +{REFERRAL_BONUS} 💮")
                except: pass
                break
    
    if chat_type in ["group", "supergroup"]:
        chat_premium = "💎 Активен" if is_chat_premium(update.effective_chat.id) else "Не активен"
        await update.message.reply_text(f"🧠 NeBlock AI V{BOT_VERSION} в чате!\n💬 @{context.bot.username} вопрос\n🎨 @{context.bot.username} нарисуй описание\n💎 Премиум: {chat_premium}\n👑 /chatowner | 🛒 /chatshop")
        return
    
    premium = "💎 Активен" if is_premium(user_id) else "Не активен"
    rate_data = get_token_rate()
    rate = rate_data.get("rate", 0.01)
    trend = rate_data.get("trend", "📊 Стабильно")
    
    await update.message.reply_text(
        f"🧠 NeBlock AI V{BOT_VERSION}\n━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💬 NeBlock AI V2 — текст\n🎨 NeBlock Images V2 — фото\n"
        f"💎 Премиум ЛС: {premium}\n\n"
        f"💰 Баланс: {user.get('tokens', 0)} 💮\n"
        f"💮 1 NBT = ${rate:.8f} {trend}\n"
        f"📊 Лимиты: {DAILY_LIMIT} вопр. + {IMAGE_DAILY_LIMIT} фото/день\n\n"
        f"👇 Выбери модель:",
        reply_markup=main_reply_keyboard()
    )

async def tokenrate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rate_data = get_token_rate()
    history = load_json(TOKEN_HISTORY_FILE)
    shop_items = get_shop_items()
    
    rate = rate_data.get("rate", 0.01)
    supply = rate_data.get("total_supply", 0)
    earned = rate_data.get("total_earned", 0)
    spent = rate_data.get("total_spent", 0)
    market_cap = rate_data.get("market_cap", 0)
    change_24h = rate_data.get("change_24h", 0)
    trend = rate_data.get("trend", "📊 Стабильно")
    active_users = rate_data.get("active_users", 0)
    total_users = rate_data.get("total_users", 0)
    supply_factor = rate_data.get("supply_factor", 1.0)
    activity_factor = rate_data.get("activity_factor", 1.0)
    burn_factor = rate_data.get("burn_factor", 1.0)
    volatility_index = rate_data.get("volatility_index", 1.0)
    updated = rate_data.get("updated_at", "")
    
    if updated:
        updated_time = datetime.fromisoformat(updated).strftime("%d.%m.%Y %H:%M МСК")
    else:
        updated_time = "Неизвестно"
    
    change_emoji = "📈" if change_24h > 0 else "📉" if change_24h < 0 else "📊"
    
    text = (
        f"💮 КУРС NeBlock Token (NBT)\n━━━━━━━━━━━━━━━━\n\n"
        f"💰 1 NBT = ${rate:.8f} USD\n"
        f"{trend} Изменение за 24ч: {change_24h:+.2f}% {change_emoji}\n\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📊 РЫНОЧНЫЕ ДАННЫЕ\n"
        f"💎 Рыночная капитализация: ${market_cap:,.2f}\n"
        f"🪙 Токенов в обороте: {supply:,} NBT\n"
        f"💸 Заработано всего: {earned:,} NBT\n"
        f"🔥 Потрачено всего: {spent:,} NBT\n\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📈 ФАКТОРЫ КУРСА\n"
        f"📊 Фактор предложения: {supply_factor}\n"
        f"👥 Фактор активности: {activity_factor}\n"
        f"🔥 Фактор сжигания: {burn_factor}\n"
        f"📉 Индекс волатильности: {volatility_index}\n\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"👥 Пользователей: {total_users} (активных: {active_users})\n"
        f"🕐 Обновлён: {updated_time}\n"
        f"🔄 Следующее обновление: завтра в 00:00 МСК\n\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📋 ПРИМЕРЫ ЦЕН:\n"
        f"📝 +5 запросов: {shop_items.get('extra5', {}).get('price', '?')} 💮\n"
        f"🎨 1 фото: {shop_items.get('image1', {}).get('price', '?')} 💮\n"
        f"⭐ Премиум день: {shop_items.get('premium_day', {}).get('price', '?')} 💮\n"
        f"👑 Премиум навсегда: {shop_items.get('premium_forever', {}).get('price', '?')} 💮\n\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💡 Чем больше токенов в обороте — тем выше курс.\n"
        f"💡 Чем активнее пользователи — тем выше курс.\n"
        f"💡 Чем больше тратят — тем выше курс.\n"
        f"💡 Курс обновляется ежедневно в 00:00 МСК."
    )
    
    # Добавляем историю если есть
    if len(history) > 1:
        text += "\n\n📈 ИСТОРИЯ КУРСА (7 дней)\n━━━━━━━━━━━━━━━━\n"
        history_items = sorted(history.items())[-7:]
        for date, hdata in history_items:
            hrate = hdata.get("rate", 0)
            hchange = hdata.get("change_24h", 0)
            change_str = f"{hchange:+.2f}%" if hchange != 0 else "0%"
            text += f"{date}: ${hrate:.8f} ({change_str})\n"
    
    await update.message.reply_text(text)

async def discounts_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    discounts = get_discounts()
    active = {k: v for k, v in discounts.items() if k not in ["last_update", "generated_at"]}
    next_update = get_next_update_time()
    shop_items = get_shop_items()
    
    text = "🎫 СКИДКИ\n━━━━━━━━━━━━━━━━\n\n"
    text += f"🔄 Обновление: {next_update.strftime('%d.%m.%Y в 9:00 МСК')}\n\n"
    
    if not active: text += "Нет активных скидок.\n"
    else:
        legendary = any(d.get("type") == "legendary" for d in active.values())
        if legendary: text += "🌟 ЛЕГЕНДАРНАЯ СКИДКА 100%! (3 часа) 🌟\n\n"
        for item_id, disc in sorted(active.items(), key=lambda x: x[1]["percent"], reverse=True):
            item = shop_items.get(item_id)
            if not item: continue
            text += f"{disc.get('color', '🟢')} {item['icon']} {item['name']}: -{disc['percent']}%\n"
            text += f"💵 {disc['original']} → 🔥 {disc['new_price']} 💮\n\n"
    
    await update.message.reply_text(text)

async def changelog_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(CHANGELOG)

async def chatowner_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.effective_chat.type
    if chat_type not in ["group", "supergroup"]: return
    chat_id = update.effective_chat.id; user_id = update.effective_user.id; add_chat_owner(chat_id, user_id)
    chats = load_chats(); chat_data = chats.get(str(chat_id), {})
    owners = chat_data.get("owners", []) if isinstance(chat_data, dict) else chat_data
    premium = "💎 Активен" if is_chat_premium(chat_id) else "Не активен"
    text = f"👑 Владельцы:\n"
    for i, oid in enumerate(owners, 1): text += f"{i}. ID: {oid}\n"
    text += f"\n💎 Премиум: {premium}\n/chatshop"
    await update.message.reply_text(text)

async def chatshop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.effective_chat.type
    if chat_type not in ["group", "supergroup"]: return
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
        user = get_user(int(context.args[0]))
        if user.get("tokens", 0) < amount: return
        users = load_users(); users[uid]["tokens"] = users[uid].get("tokens", 0) - amount
        users[uid]["spent_tokens"] = users[uid].get("spent_tokens", 0) + amount; save_users(users)
        await update.message.reply_text(f"✅ -{amount} 💮")
    except: pass

async def admin_resetuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args: return
    try:
        uid = str(int(context.args[0])); users = load_users()
        if uid in users:
            users[uid]["requests_today"] = 0; users[uid]["extra_requests"] = 0
            users[uid]["image_requests_today"] = 0; users[uid]["extra_image_requests"] = 0
            users[uid]["warnings"] = 0; users[uid]["muted_until"] = None; users[uid]["banned"] = False
            save_users(users); await update.message.reply_text("✅ Сброшен")
    except: pass

async def admin_setpremium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args or len(context.args) < 2: return
    try:
        uid = str(int(context.args[0])); days = int(context.args[1]); users = load_users()
        if uid in users:
            existing = users[uid].get("premium_until")
            base_time = datetime.fromisoformat(existing) if existing and datetime.now() < datetime.fromisoformat(existing) else datetime.now()
            users[uid]["premium_until"] = (base_time + timedelta(days=days)).isoformat()
            save_users(users); await update.message.reply_text(f"✅ Премиум {days}д")
    except: pass

async def admin_userinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args: return
    try:
        user_id = int(context.args[0]); user = get_user(user_id)
        username = user.get("username") or "Не указан"
        await update.message.reply_text(f"👤 @{username}\n💰 {user.get('tokens', 0)} 💮\n⚠️ {user.get('warnings', 0)}/5")
    except: pass

async def admin_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    users = load_users()
    by_tokens = sorted(users.items(), key=lambda x: x[1].get("tokens", 0), reverse=True)[:10]
    text = "🏆 ТОП 💮\n\n"
    for i, (uid, data) in enumerate(by_tokens, 1):
        name = f"@{data['username']}" if data.get("username") else f"ID:{uid}"
        text += f"{i}. {name} — {data.get('tokens', 0)} 💮\n"
    await update.message.reply_text(text)

async def admin_cleardiscounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    save_discounts({"last_update": datetime.now().strftime("%Y-%m-%d")})
    await update.message.reply_text("✅ Скидки очищены")

async def admin_create_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args or len(context.args) < 2: return
    create_promo(context.args[0].upper(), int(context.args[1]), int(context.args[2]) if len(context.args) > 2 else 0)
    await update.message.reply_text(f"✅ Промокод {context.args[0].upper()} создан!")

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
    users = load_users()
    rate_data = get_token_rate()
    await update.message.reply_text(
        f"📊 Статистика\n👥 {len(users)}\n"
        f"💬 {sum(u.get('total_requests', 0) for u in users.values())}\n"
        f"🎨 {sum(u.get('total_images', 0) for u in users.values())}\n"
        f"💮 В обороте: {rate_data.get('total_supply', 0):,} NBT\n"
        f"💱 Курс: ${rate_data.get('rate', 0.01):.8f}"
    )

async def admin_forcediscounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    new_discounts = generate_discounts()
    new_discounts["last_update"] = datetime.now().strftime("%Y-%m-%d")
    save_discounts(new_discounts)
    await update.message.reply_text("✅ Скидки обновлены!")

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
        user = get_user(user_id); joined = datetime.fromisoformat(user.get("joined", "")).strftime("%d.%m.%Y")
        last = "Никогда"
        if user.get("last_request"): last = datetime.fromisoformat(user["last_request"]).strftime("%d.%m.%Y в %H:%M")
        current_model = "💬 NeBlock AI V2" if user.get("current_model") == "text" else "🎨 NeBlock Images V2"
        premium = "💎 Активен" if is_premium(user_id) else "Не активен"
        rate_data = get_token_rate(); rate = rate_data.get("rate", 0.01)
        usd_value = user.get("tokens", 0) * rate
        
        def fmt(until_str):
            if not until_str: return "Не активен"
            try:
                if datetime.now() < datetime.fromisoformat(until_str):
                    diff = datetime.fromisoformat(until_str) - datetime.now(); d, h = diff.days, diff.seconds // 3600
                    return f"Активен ({d}д {h}ч)" if d > 0 else f"Активен ({h}ч)"
            except: pass
            return "Не активен"
        
        await update.message.reply_text(
            f"👤 Профиль V{BOT_VERSION}\n━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🆔 {user_id}\n📅 {joined}\n🔮 {current_model}\n💎 Премиум: {premium}\n\n"
            f"💰 Баланс: {user.get('tokens', 0)} 💮 (~${usd_value:.2f})\n"
            f"💮 Курс: 1 NBT = ${rate:.8f}\n"
            f"💎 Заработано: {user.get('earned_tokens', 0)} | 💸 Потрачено: {user.get('spent_tokens', 0)}\n\n"
            f"💬 ЛС: {user.get('requests_today', 0)}/{DAILY_LIMIT + user.get('extra_requests', 0)} | {fmt(user.get('unlimited_until'))}\n"
            f"🎨 Фото: {user.get('image_requests_today', 0)}/{IMAGE_DAILY_LIMIT + user.get('extra_image_requests', 0)} | {fmt(user.get('image_unlimited_until'))}\n"
            f"👥 Чаты: {user.get('chat_requests_today', 0)}/{CHAT_DAILY_LIMIT + user.get('extra_chat_requests', 0)} | {fmt(user.get('chat_unlimited_until'))}\n"
            f"🛡 {user.get('warnings', 0)}/5 | 👥 {user.get('referrals', 0)}\n🕐 {last}",
            reply_markup=main_menu()
        )
        return True
    if text == "🛒 Магазин": await update.message.reply_text(f"🛒 Магазин (ЛС)\n💰 {get_tokens(user_id)} 💮\n💮 /tokenrate — курс", reply_markup=shop_keyboard("private")); return True
    if text == "💰 Заработать": await update.message.reply_text(f"💰 Заработок\n💎 {get_tokens(user_id)} 💮\n🎁 Бонус: {DAILY_BONUS_MIN}-{DAILY_BONUS_MAX}/день\n👥 Рефералы: +{REFERRAL_BONUS} тебе, +{INVITED_BONUS} другу", reply_markup=earn_keyboard()); return True
    if text == "📚 FAQ": await update.message.reply_text(FAQ_TEXT); return True
    if text == "🎫 Скидки": await discounts_cmd(update, context); return True
    if text == "💮 Курс NBT": await tokenrate_cmd(update, context); return True
    return False

async def inline_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer(); user_id = query.from_user.id; data = query.data
    shop_items = get_shop_items()
    
    if data == "none": return
    if data == "menu": await query.edit_message_text(f"🧠 NeBlock AI V{BOT_VERSION}\n💰 {get_tokens(user_id)} 💮", reply_markup=main_menu())
    elif data == "about": await query.edit_message_text(f"ℹ️ NeBlock AI V{BOT_VERSION}\n\n💬 Текст\n🎨 Фото\n👥 Чаты\n💮 NBT\n🎫 Скидки", reply_markup=back_button())
    elif data == "models": await query.edit_message_text(f"🧠 МОДЕЛИ\n\n💬 NeBlock AI V2\n🎨 NeBlock Images V2\n\n💮 /tokenrate — курс NBT", reply_markup=back_button())
    elif data == "tokenrate":
        rate_data = get_token_rate()
        rate = rate_data.get("rate", 0.01)
        supply = rate_data.get("total_supply", 0)
        market_cap = rate_data.get("market_cap", 0)
        change_24h = rate_data.get("change_24h", 0)
        trend = rate_data.get("trend", "📊 Стабильно")
        await query.edit_message_text(
            f"💮 КУРС NBT\n━━━━━━━━━━━━━━━━\n\n"
            f"💰 1 NBT = ${rate:.8f}\n{trend} {change_24h:+.2f}%\n"
            f"💎 Капитализация: ${market_cap:,.2f}\n"
            f"🪙 В обороте: {supply:,} NBT\n\n"
            f"📋 Цены:\n"
            f"📝 +5 запросов: {shop_items.get('extra5', {}).get('price', '?')} 💮\n"
            f"⭐ Премиум день: {shop_items.get('premium_day', {}).get('price', '?')} 💮\n\n"
            f"💡 /tokenrate — подробнее",
            reply_markup=back_button()
        )
    elif data == "changelog": await query.edit_message_text(CHANGELOG, reply_markup=back_button())
    elif data == "discounts_info":
        discounts = get_discounts(); active = {k: v for k, v in discounts.items() if k not in ["last_update", "generated_at"]}
        text = "🎫 СКИДКИ\n\n"
        if not active: text += "Нет активных скидок."
        else:
            for item_id, disc in sorted(active.items(), key=lambda x: x[1]["percent"], reverse=True):
                item = shop_items.get(item_id)
                if not item: continue
                if disc.get("type") == "legendary":
                    text += f"🌟 {item['icon']} {item['name']}\n💫 БЕСПЛАТНО!\n\n"
                else:
                    text += f"{disc.get('color', '🟢')} {item['icon']} {item['name']}\n🔥 -{disc['percent']}% = {disc['new_price']} 💮\n\n"
        await query.edit_message_text(text, reply_markup=back_button())
    elif data == "premium_info": await query.edit_message_text(f"💎 Премиум\n\nЛС: {shop_items.get('premium_day', {}).get('price', '?')}/{shop_items.get('premium_week', {}).get('price', '?')}/{shop_items.get('premium_forever', {}).get('price', '?')} 💮", reply_markup=back_button())
    elif data == "stats":
        user = get_user(user_id)
        await query.edit_message_text(f"📊 Статистика\n💬 {user.get('requests_today', 0)}\n🎨 {user.get('image_requests_today', 0)}\n💰 {user.get('tokens', 0)} 💮", reply_markup=back_button())
    elif data == "shop": await query.edit_message_text(f"🛒 Магазин\n💰 {get_tokens(user_id)} 💮", reply_markup=shop_keyboard("private"))
    elif data == "earn": await query.edit_message_text(f"💰 Заработок\n💎 {get_tokens(user_id)} 💮", reply_markup=earn_keyboard())
    elif data == "promo": context.user_data["waiting_promo"] = True; await query.edit_message_text("🎟 Отправь промокод.", reply_markup=back_button())
    elif data == "faq": await query.edit_message_text(FAQ_TEXT, reply_markup=back_button())
    elif data == "daily_bonus":
        user = get_user(user_id); today = datetime.now().strftime("%Y-%m-%d")
        if user.get("daily_bonus_claimed") == today: await query.answer("❌ Уже забирали!", show_alert=True)
        else:
            bonus = random.randint(DAILY_BONUS_MIN, DAILY_BONUS_MAX); users = load_users(); uid = str(user_id)
            users[uid]["daily_bonus_claimed"] = today
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            users[uid]["daily_bonus_streak"] = users[uid].get("daily_bonus_streak", 0) + 1 if users[uid].get("last_bonus_date") == yesterday else 1
            users[uid]["last_bonus_date"] = today; save_users(users); add_tokens(user_id, bonus)
            await query.answer(f"🎉 +{bonus} 💮!", show_alert=True)
            await query.edit_message_text(f"🎁 +{bonus} 💮\n💰 {get_tokens(user_id)} 💮", reply_markup=back_button())
    elif data == "ref_link":
        user = get_user(user_id); bot_username = (await context.bot.get_me()).username
        await query.edit_message_text(f"👥 https://t.me/{bot_username}?start=ref_{user.get('referral_code', '')}\n💰 +{REFERRAL_BONUS} 💮 тебе\n🎁 +{INVITED_BONUS} 💮 другу", reply_markup=back_button())
    elif data.startswith("confirm_"):
        item_id = data.replace("confirm_", ""); item = shop_items.get(item_id)
        if not item: return
        price, percent, disc_info = get_discounted_price(item_id)
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
            chats = load_chats(); hours_map = {"chat_premium_day": 24, "chat_premium_week": 168, "chat_premium_forever": 876000}
            for cid, cdata in chats.items():
                if isinstance(cdata, dict) and str(user_id) in cdata.get("owners", []): chats[cid]["premium_until"] = (datetime.now() + timedelta(hours=hours_map[item_id])).isoformat(); save_chats(chats); break
        save_users(users)
        disc_text = f"\n🎫 -{percent}%" if percent > 0 else ""
        if disc_info and disc_info.get("type") == "legendary": disc_text = "\n🌟 ЛЕГЕНДАРНАЯ СКИДКА!"
        await query.answer(f"✅ {item['name']}!", show_alert=True)
        await query.edit_message_text(f"✅ {item['name']}{disc_text}\n💰 Потрачено: {price} 💮\n💎 Остаток: {get_tokens(user_id)} 💮", reply_markup=back_button())
    elif data.startswith("buy_"):
        item_id = data.replace("buy_", ""); item = shop_items.get(item_id)
        if not item: return
        price, percent, disc_info = get_discounted_price(item_id)
        tokens = get_tokens(user_id); can = "✅ Хватает" if tokens >= price else "❌ Не хватает"
        disc_text = ""
        if percent > 0 and disc_info:
            if disc_info.get("type") == "legendary":
                disc_text = "\n\n🌟 ЛЕГЕНДАРНАЯ СКИДКА 100%!\n💫 БЕСПЛАТНО!"
            else:
                disc_text = f"\n\n{disc_info.get('color', '🟢')} -{percent}%\n💵 {disc_info['original']} → 🔥 {price} 💮"
        await query.edit_message_text(f"🛒 {item['icon']} {item['name']}\n📝 {item['desc']}\n⚠️ {item.get('warning', '')}{disc_text}\n\n💎 Баланс: {tokens} 💮\n{can}", reply_markup=confirm_keyboard(item_id))

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤔 Неизвестная команда.\n/start — меню.")

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
    
    if chat_type == "private":
        if await reply_button_handler(update, context): return
    
    is_image_request = False
    should_respond = False
    
    if chat_type in ["group", "supergroup"]:
        mention = f"@{bot_username}"
        text_lower = text.lower()
        
        if mention in text:
            text = text.replace(mention, "").strip()
            should_respond = True
        
        if not should_respond:
            keywords = ["бот ", "нейробот ", "нейросеть ", "ai ", "нарисуй "]
            for kw in keywords:
                if text_lower.startswith(kw):
                    text = text[len(kw):].strip()
                    should_respond = True
                    break
        
        if not should_respond: return
        
        if text_lower.startswith("нарисуй"):
            text = text[7:].strip()
            is_image_request = True
        
        if not text:
            await update.message.reply_text(f"🧠 NeBlock AI V2!\n💬 @{bot_username} вопрос\n🎨 @{bot_username} нарисуй описание", reply_to_message_id=update.message.message_id)
            return
    
    user = get_user(user_id)
    if context.user_data.get("waiting_promo"): context.user_data["waiting_promo"] = False; success, result = use_promo(user_id, text); await update.message.reply_text(f"🎟 +{result} 💮!" if success else f"❌ {result}"); return
    
    if is_image_request or (chat_type == "private" and (user.get("current_model") == "image" or user.get("waiting_for_image"))):
        if chat_type == "private":
            users = load_users(); users[str(user_id)]["waiting_for_image"] = False; save_users(users)
        
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
    app.add_handler(CommandHandler("changelog", changelog_cmd))
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
    app.add_handler(CallbackQueryHandler(inline_button_handler))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    print("✅ Бот запущен!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
