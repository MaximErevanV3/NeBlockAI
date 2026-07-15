import openai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import logging
import os
import json
import random
import asyncio
from datetime import datetime, timedelta

# ═══════════════════════════════════════════
# 🧠 NeBlock AI V1 - Конфигурация
# ═══════════════════════════════════════════

TELEGRAM_TOKEN = "8700124191:AAE6qSSouLjlDxPWwoFObJORMbDotsby9co"
YANDEX_API_KEY = "AQVNy7Dm-dvQRzejHvH0383oHTZhhW2fda95I558"
PROMPT_ID = "fvt621uiq1fftiu5qomu"
DAILY_LIMIT = 5
DATA_FILE = "users.json"
PROMO_FILE = "promos.json"
ADMIN_IDS = [1671403667]
START_BONUS = 50
DAILY_BONUS_MIN = 5
DAILY_BONUS_MAX = 15
REFERRAL_BONUS = 25
INVITED_BONUS = 10

SHOP_ITEMS = {
    "extra5": {"name": "+5 запросов", "price": 10, "icon": "📦", "desc": "Добавляет 5 запросов к текущему лимиту на сегодня"},
    "extra10": {"name": "+10 запросов", "price": 18, "icon": "📦", "desc": "Добавляет 10 запросов к текущему лимиту на сегодня"},
    "unlimited_1h": {"name": "Безлимит 1 час", "price": 30, "icon": "⚡", "desc": "Безлимитные запросы на 1 час"},
    "unlimited_24h": {"name": "Безлимит 24 часа", "price": 100, "icon": "⚡", "desc": "Безлимитные запросы на 24 часа"},
    "unlimited_7d": {"name": "Безлимит 7 дней", "price": 500, "icon": "🔥", "desc": "Безлимитные запросы на 7 дней"},
}

# Анимация - каждая фаза показывается 1.5 секунды (полный цикл ~6 секунд)
ANIMATION_PHASES = [
    "🤔 Анализирую запрос\n█░░░░░░░░░ 10%",
    "🔍 Ищу информацию\n██░░░░░░░░ 20%",
    "⚡ Обрабатываю данные\n████░░░░░░ 40%",
    "🧠 Нейросеть думает\n██████░░░░ 60%",
    "📝 Формирую ответ\n████████░░ 80%",
    "✅ Завершаю генерацию\n██████████ 100%",
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("NeBlockAI")

client = openai.OpenAI(
    api_key=YANDEX_API_KEY,
    base_url="https://ai.api.cloud.yandex.net/v1",
    project="b1guk4h3j9t48lsjl6sq",
    timeout=30.0,
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
        "requests_today": 0,
        "extra_requests": 0,
        "unlimited_until": None,
        "last_request": None,
        "total_requests": 0,
        "reset_date": datetime.now().strftime("%Y-%m-%d"),
        "tokens": START_BONUS,
        "daily_bonus_claimed": None,
        "referral_code": "".join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(8)),
        "referred_by": None,
        "referrals": 0,
        "earned_tokens": 0,
        "used_promos": [],
    }
    
    if uid not in users:
        users[uid] = defaults.copy()
        save_users(users)
    else:
        updated = False
        for key, value in defaults.items():
            if key not in users[uid]:
                users[uid][key] = value
                updated = True
        if updated:
            save_users(users)
    
    today = datetime.now().strftime("%Y-%m-%d")
    if users[uid].get("reset_date") != today:
        users[uid]["requests_today"] = 0
        users[uid]["extra_requests"] = 0
        users[uid]["reset_date"] = today
        save_users(users)
    
    return users[uid]

def add_request(user_id):
    users = load_users()
    uid = str(user_id)
    if uid in users:
        users[uid]["requests_today"] = users[uid].get("requests_today", 0) + 1
        users[uid]["total_requests"] = users[uid].get("total_requests", 0) + 1
        users[uid]["last_request"] = datetime.now().isoformat()
        save_users(users)

def can_request(user_id):
    user = get_user(user_id)
    unlimited = user.get("unlimited_until")
    if unlimited:
        try:
            until = datetime.fromisoformat(unlimited)
            if datetime.now() < until:
                return True
        except:
            pass
    return user.get("requests_today", 0) < (DAILY_LIMIT + user.get("extra_requests", 0))

def remaining(user_id):
    user = get_user(user_id)
    unlimited = user.get("unlimited_until")
    if unlimited:
        try:
            until = datetime.fromisoformat(unlimited)
            if datetime.now() < until:
                return "безлимит"
        except:
            pass
    return max(0, DAILY_LIMIT + user.get("extra_requests", 0) - user.get("requests_today", 0))

def add_extra_requests(user_id, amount):
    users = load_users()
    uid = str(user_id)
    if uid in users:
        users[uid]["extra_requests"] = users[uid].get("extra_requests", 0) + amount
        save_users(users)

def add_tokens(user_id, amount):
    users = load_users()
    uid = str(user_id)
    if uid not in users:
        get_user(user_id)
        users = load_users()
    users[uid]["tokens"] = users[uid].get("tokens", 0) + amount
    users[uid]["earned_tokens"] = users[uid].get("earned_tokens", 0) + amount
    save_users(users)

def remove_tokens(user_id, amount):
    users = load_users()
    uid = str(user_id)
    if uid in users:
        users[uid]["tokens"] = users[uid].get("tokens", 0) - amount
        save_users(users)

def get_tokens(user_id):
    return get_user(user_id).get("tokens", 0)

def create_promo(code, amount, max_uses=0):
    promos = load_promos()
    promos[code.upper()] = {"amount": amount, "max_uses": max_uses, "used_by": [], "created": datetime.now().isoformat()}
    save_promos(promos)

def use_promo(user_id, code):
    promos = load_promos()
    code = code.upper()
    if code not in promos: return False, "Промокод не найден"
    promo = promos[code]
    if promo["max_uses"] > 0 and len(promo["used_by"]) >= promo["max_uses"]: return False, "Лимит использований исчерпан"
    if str(user_id) in promo["used_by"]: return False, "Вы уже использовали этот промокод"
    add_tokens(user_id, promo["amount"])
    promo["used_by"].append(str(user_id))
    save_promos(promos)
    users = load_users()
    uid = str(user_id)
    if "used_promos" not in users[uid]: users[uid]["used_promos"] = []
    users[uid]["used_promos"].append(code)
    save_users(users)
    return True, promo["amount"]

# ═══════════════════════════════════════════
# 🎛 Клавиатуры
# ═══════════════════════════════════════════

def main_reply_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📝 Задать вопрос"), KeyboardButton("👤 Профиль")],
        [KeyboardButton("🛒 Магазин"), KeyboardButton("💰 Заработать")],
    ], resize_keyboard=True)

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎟 Промокод", callback_data="promo"),
         InlineKeyboardButton("📚 FAQ", callback_data="faq")],
        [InlineKeyboardButton("ℹ️ О боте", callback_data="about")],
    ])

def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="menu")]])

def shop_keyboard():
    keyboard = []
    for item_id, item in SHOP_ITEMS.items():
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
        [InlineKeyboardButton("💰 Заработать токены", callback_data="earn")],
        [InlineKeyboardButton("🎟 Ввести промокод", callback_data="promo")],
    ])

# ═══════════════════════════════════════════
# 🎬 Анимация с ожиданием
# ═══════════════════════════════════════════

async def show_full_animation(message, api_future):
    """
    Показывает анимацию минимум один полный цикл.
    api_future - asyncio.Future с результатом API
    """
    # Показываем анимацию минимум один цикл (6 фаз * 1.5 сек = 9 секунд)
    for phase_text in ANIMATION_PHASES:
        # Проверяем, готов ли ответ от API
        if api_future.done():
            # Ответ готов, показываем последнюю фазу и выходим
            await message.edit_text("✅ Завершаю генерацию\n██████████ 100%")
            await asyncio.sleep(0.5)
            return
        
        # Показываем текущую фазу
        try:
            await message.edit_text(phase_text)
        except:
            pass
        
        # Ждём 1.5 секунды или пока API ответит
        try:
            await asyncio.wait_for(asyncio.shield(api_future), timeout=1.5)
            # API ответил во время ожидания
            await message.edit_text("✅ Завершаю генерацию\n██████████ 100%")
            await asyncio.sleep(0.5)
            return
        except asyncio.TimeoutError:
            # Продолжаем анимацию
            continue
    
    # Если API ещё не ответил, продолжаем крутить последние фазы
    while not api_future.done():
        for phase_text in ANIMATION_PHASES[-3:]:
            if api_future.done():
                break
            try:
                await message.edit_text(phase_text)
                await asyncio.wait_for(asyncio.shield(api_future), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            except:
                break
    
    # Финальная фаза
    try:
        await message.edit_text("✅ Завершаю генерацию\n██████████ 100%")
        await asyncio.sleep(0.5)
    except:
        pass

# ═══════════════════════════════════════════
# 🚀 Команды
# ═══════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if context.args and context.args[0].startswith("ref_"):
        ref_code = context.args[0].replace("ref_", "")
        users = load_users()
        uid = str(user_id)
        for u_id, u_data in users.items():
            if u_data.get("referral_code") == ref_code and u_id != uid:
                if not users[uid].get("referred_by"):
                    users[uid]["referred_by"] = u_id
                    add_tokens(int(u_id), REFERRAL_BONUS)
                    add_tokens(user_id, INVITED_BONUS)
                    users[u_id]["referrals"] = users[u_id].get("referrals", 0) + 1
                    save_users(users)
                    try:
                        await context.bot.send_message(int(u_id), f"🎉 Новый реферал!\n💰 +{REFERRAL_BONUS} NeBlock Tokens")
                    except:
                        pass
                break
    
    extra = user.get("extra_requests", 0)
    total = DAILY_LIMIT + extra
    
    text = (
        f"🧠 NeBlock AI V1\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"⚡ Быстрые ответы | 💻 Помощь с кодом\n"
        f"📊 Лимит: {total} запросов/день\n"
        f"💰 Баланс: {user.get('tokens', 0)} NeBlock Tokens\n\n"
        f"👇 Просто напиши вопрос:"
    )
    await update.message.reply_text(text, reply_markup=main_reply_keyboard())
    await update.message.reply_text("Дополнительно:", reply_markup=main_menu())

# Админ команды
async def admin_give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("/give ID КОЛИЧЕСТВО")
        return
    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
        add_tokens(target_id, amount)
        await update.message.reply_text(f"✅ Начислено {amount} токенов пользователю {target_id}")
    except:
        await update.message.reply_text("❌ Ошибка")

async def admin_create_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("/createpromo КОД КОЛИЧЕСТВО [МАКС_ИСП]")
        return
    create_promo(context.args[0].upper(), int(context.args[1]), int(context.args[2]) if len(context.args) > 2 else 0)
    await update.message.reply_text(f"✅ Промокод {context.args[0].upper()} создан!")

async def admin_promos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    promos = load_promos()
    if not promos: await update.message.reply_text("Нет активных промокодов."); return
    text = "🎟 Промокоды:\n"
    for code, data in promos.items():
        text += f"\n{code}: {data['amount']} токенов | {len(data['used_by'])}/{data['max_uses'] if data['max_uses'] > 0 else '∞'}"
    await update.message.reply_text(text)

async def admin_delete_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args: await update.message.reply_text("/deletepromo КОД"); return
    code = context.args[0].upper()
    promos = load_promos()
    if code in promos: del promos[code]; save_promos(promos); await update.message.reply_text(f"✅ Удалён")
    else: await update.message.reply_text("❌ Не найден")

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    text = " ".join(context.args)
    if not text: await update.message.reply_text("/broadcast ТЕКСТ"); return
    users = load_users()
    sent = 0
    for uid in users:
        try: await context.bot.send_message(int(uid), f"📢 {text}"); sent += 1
        except: pass
    await update.message.reply_text(f"✅ Отправлено {sent}")

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    users = load_users()
    await update.message.reply_text(
        f"📊 Статистика\n👥 Пользователей: {len(users)}\n"
        f"📝 Запросов: {sum(u.get('total_requests', 0) for u in users.values())}\n"
        f"💰 Токенов: {sum(u.get('tokens', 0) for u in users.values())}"
    )

# ═══════════════════════════════════════════
# 🔘 Обработчик обычных кнопок
# ═══════════════════════════════════════════

async def reply_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    if text == "📝 Задать вопрос":
        await update.message.reply_text(f"📝 Напиши свой вопрос в чат.\n📊 Осталось: {remaining(user_id)}")
        return True
    
    if text == "👤 Профиль":
        await update.message.reply_text(get_profile_text(user_id))
        return True
    
    if text == "🛒 Магазин":
        await update.message.reply_text(
            f"🛒 Магазин\n━━━━━━━━━━━━━━━━\n💰 Баланс: {get_tokens(user_id)} токенов\n\nВыбери товар:",
            reply_markup=shop_keyboard()
        )
        return True
    
    if text == "💰 Заработать":
        await update.message.reply_text(
            f"💰 Заработок\n━━━━━━━━━━━━━━━━\n💎 Баланс: {get_tokens(user_id)}\n\n"
            f"🎁 Бонус: {DAILY_BONUS_MIN}-{DAILY_BONUS_MAX} токенов/день\n"
            f"👥 Рефералы: +{REFERRAL_BONUS} тебе, +{INVITED_BONUS} другу",
            reply_markup=earn_keyboard()
        )
        return True
    
    return False

def get_profile_text(user_id):
    user = get_user(user_id)
    joined = datetime.fromisoformat(user.get("joined", datetime.now().isoformat())).strftime("%d.%m.%Y")
    last = "Никогда" if not user.get("last_request") else datetime.fromisoformat(user["last_request"]).strftime("%H:%M %d.%m.%Y")
    unlimited = "Не активен"
    if user.get("unlimited_until"):
        try:
            until = datetime.fromisoformat(user["unlimited_until"])
            if datetime.now() < until:
                diff = until - datetime.now()
                h = diff.seconds // 3600
                m = (diff.seconds % 3600) // 60
                unlimited = f"Активен ({h}ч {m}м)"
        except: pass
    
    extra = user.get("extra_requests", 0)
    total = DAILY_LIMIT + extra
    
    return (
        f"👤 Личный кабинет\n━━━━━━━━━━━━━━━━\n"
        f"🆔 ID: {user_id}\n📅 Регистрация: {joined}\n"
        f"💰 Баланс: {user.get('tokens', 0)} токенов\n💎 Заработано: {user.get('earned_tokens', 0)}\n"
        f"📊 Лимит: {total} (база: {DAILY_LIMIT} + доп: {extra})\n"
        f"📝 Использовано: {user.get('requests_today', 0)}/{total}\n"
        f"📈 Всего запросов: {user.get('total_requests', 0)}\n⚡ Безлимит: {unlimited}\n"
        f"👥 Рефералов: {user.get('referrals', 0)}\n🕐 Активность: {last}"
    )

# ═══════════════════════════════════════════
# 🔘 Inline кнопки
# ═══════════════════════════════════════════

async def inline_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if data == "menu":
        user = get_user(user_id)
        await query.edit_message_text(
            f"🧠 NeBlock AI V1\n━━━━━━━━━━━━━━━━\n📊 Лимит: {DAILY_LIMIT + user.get('extra_requests', 0)} запросов/день\n💰 Баланс: {user.get('tokens', 0)} токенов",
            reply_markup=main_menu()
        )
        return
    
    if data == "ask":
        await query.edit_message_text(f"📝 Напиши вопрос в чат.\n📊 Осталось: {remaining(user_id)}", reply_markup=back_button())
        return
    
    if data == "about":
        await query.edit_message_text("ℹ️ NeBlock AI V1\n━━━━━━━━━━━━━━━━\n🧠 Модель: NeBlock AI V1\n⚡ Быстрые ответы\n💬 Контекст\n🌐 Все языки", reply_markup=back_button())
        return
    
    if data == "profile":
        await query.edit_message_text(get_profile_text(user_id), reply_markup=back_button())
        return
    
    if data == "shop":
        await query.edit_message_text(f"🛒 Магазин\n━━━━━━━━━━━━━━━━\n💰 Баланс: {get_tokens(user_id)} токенов\n\nВыбери товар:", reply_markup=shop_keyboard())
        return
    
    if data == "earn":
        await query.edit_message_text(
            f"💰 Заработок\n━━━━━━━━━━━━━━━━\n💎 Баланс: {get_tokens(user_id)}\n\n"
            f"🎁 Бонус: {DAILY_BONUS_MIN}-{DAILY_BONUS_MAX} токенов/день\n👥 Рефералы: +{REFERRAL_BONUS} тебе, +{INVITED_BONUS} другу",
            reply_markup=earn_keyboard()
        )
        return
    
    if data == "promo":
        context.user_data["waiting_promo"] = True
        await query.edit_message_text("🎟 Отправь промокод в чат.", reply_markup=back_button())
        return
    
    if data == "faq":
        await query.edit_message_text(
            "📚 FAQ\n━━━━━━━━━━━━━━━━\n\n"
            "❓ Что такое NeBlock AI?\nИИ-бот в Telegram.\n\n"
            "❓ Почему лимит 5?\nЧтобы не перегружать нейросеть.\n\n"
            "❓ Доп запросы сгорают?\nДа, в 00:00 МСК.\n\n"
            "❓ Промокоды?\nВводи в разделе Промокод.\n\n"
            "❓ Сброс лимита?\nВ 00:00 МСК.",
            reply_markup=back_button()
        )
        return
    
    if data == "daily_bonus":
        user = get_user(user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        if user.get("daily_bonus_claimed") == today:
            await query.answer("❌ Вы уже забирали бонус сегодня!", show_alert=True)
            return
        bonus = random.randint(DAILY_BONUS_MIN, DAILY_BONUS_MAX)
        users = load_users()
        users[str(user_id)]["daily_bonus_claimed"] = today
        save_users(users)
        add_tokens(user_id, bonus)
        await query.answer(f"🎉 +{bonus} NeBlock Tokens!", show_alert=True)
        await query.edit_message_text(f"🎁 +{bonus} токенов\n💰 Баланс: {get_tokens(user_id)}", reply_markup=back_button())
        return
    
    if data == "ref_link":
        user = get_user(user_id)
        bot_username = (await context.bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start=ref_{user.get('referral_code', '')}"
        await query.edit_message_text(f"👥 Рефералы\n🔗 {ref_link}\n\n💰 +{REFERRAL_BONUS} тебе\n🎁 +{INVITED_BONUS} другу\n👥 Приглашено: {user.get('referrals', 0)}", reply_markup=back_button())
        return
    
    if data.startswith("confirm_"):
        item_id = data.replace("confirm_", "")
        item = SHOP_ITEMS.get(item_id)
        if not item: return
        
        tokens = get_tokens(user_id)
        if tokens < item["price"]:
            await query.answer(f"❌ Недостаточно токенов!", show_alert=True)
            return
        
        remove_tokens(user_id, item["price"])
        
        if item_id == "extra5": add_extra_requests(user_id, 5)
        elif item_id == "extra10": add_extra_requests(user_id, 10)
        elif item_id in ["unlimited_1h", "unlimited_24h", "unlimited_7d"]:
            hours = 1 if item_id == "unlimited_1h" else 24 if item_id == "unlimited_24h" else 168
            users = load_users()
            users[str(user_id)]["unlimited_until"] = (datetime.now() + timedelta(hours=hours)).isoformat()
            save_users(users)
        
        await query.answer(f"✅ Куплено!", show_alert=True)
        await query.edit_message_text(
            f"✅ Покупка успешна!\n━━━━━━━━━━━━━━━━\n🛒 {item['name']}\n💰 Потрачено: {item['price']}\n💎 Остаток: {get_tokens(user_id)}",
            reply_markup=back_button()
        )
        return
    
    if data.startswith("buy_"):
        item_id = data.replace("buy_", "")
        item = SHOP_ITEMS.get(item_id)
        if not item: return
        
        tokens = get_tokens(user_id)
        can_buy = "✅ Хватает" if tokens >= item["price"] else "❌ Не хватает"
        await query.edit_message_text(
            f"🛒 {item['icon']} {item['name']}\n📝 {item['desc']}\n💰 Цена: {item['price']}\n💎 Баланс: {tokens}\n{can_buy}",
            reply_markup=confirm_keyboard(item_id)
        )
        return

# ═══════════════════════════════════════════
# 💬 Обработчик сообщений
# ═══════════════════════════════════════════

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Обычные кнопки
    if await reply_button_handler(update, context):
        return
    
    # Промокод
    if context.user_data.get("waiting_promo"):
        context.user_data["waiting_promo"] = False
        success, result = use_promo(user_id, text)
        if success:
            await update.message.reply_text(f"🎟 Промокод {text.upper()} активирован!\n💰 +{result} токенов\n💎 Баланс: {get_tokens(user_id)}")
        else:
            await update.message.reply_text(f"❌ {result}")
        return
    
    # Лимит
    if not can_request(user_id):
        user = get_user(user_id)
        await update.message.reply_text(
            f"🚫 Лимит исчерпан!\n━━━━━━━━━━━━━━━━\n📊 {user.get('requests_today', 0)}/{DAILY_LIMIT + user.get('extra_requests', 0)}\n💰 Баланс: {user.get('tokens', 0)} токенов",
            reply_markup=limit_reached_keyboard()
        )
        return
    
    # Создаём сообщение для анимации
    msg = await update.message.reply_text("🤔 Анализирую запрос\n█░░░░░░░░░ 10%")
    
    # Создаём Future для API запроса
    loop = asyncio.get_event_loop()
    api_future = loop.create_future()
    
    # Функция для выполнения API запроса в фоне
    async def do_api_request():
        try:
            response = client.responses.create(prompt={"id": PROMPT_ID}, input=text)
            api_future.set_result(response.output_text)
        except Exception as e:
            api_future.set_exception(e)
    
    # Запускаем API запрос и анимацию параллельно
    api_task = asyncio.create_task(do_api_request())
    await show_full_animation(msg, api_future)
    
    # Ждём результат
    try:
        answer = await api_future
        add_request(user_id)
        await msg.delete()
        
        if answer:
            rem = remaining(user_id)
            user = get_user(user_id)
            used = user.get("requests_today", 0)
            total = DAILY_LIMIT + user.get("extra_requests", 0)
            footer = f"\n\n━━━━━━━━━━━━━━━━\n📊 {used}/{total} | Осталось: {rem}"
            
            for i in range(0, len(answer), 4000):
                chunk = answer[i:i+4000]
                await update.message.reply_text(chunk + footer if i == 0 else chunk)
        else:
            await update.message.reply_text("🤷 Не удалось сгенерировать ответ.")
            
    except Exception as e:
        try:
            await msg.edit_text("❌ Ошибка генерации. Попробуй позже.")
        except:
            pass
        logger.error(f"Ошибка: {str(e)[:100]}")

# ═══════════════════════════════════════════
# 🚀 Запуск
# ═══════════════════════════════════════════

def main():
    print("🧠 NeBlock AI V1")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("give", admin_give))
    app.add_handler(CommandHandler("createpromo", admin_create_promo))
    app.add_handler(CommandHandler("promos", admin_promos))
    app.add_handler(CommandHandler("deletepromo", admin_delete_promo))
    app.add_handler(CommandHandler("broadcast", admin_broadcast))
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CallbackQueryHandler(inline_button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    print("✅ Бот запущен!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
