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
# 🧠 NeBlock AI V1
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
    "extra5": {"name": "+5 запросов", "price": 10, "icon": "📦"},
    "extra10": {"name": "+10 запросов", "price": 18, "icon": "📦"},
    "unlimited_1h": {"name": "Безлимит 1 час", "price": 30, "icon": "⚡"},
    "unlimited_24h": {"name": "Безлимит 24 часа", "price": 100, "icon": "⚡"},
    "unlimited_7d": {"name": "Безлимит 7 дней", "price": 500, "icon": "🔥"},
}

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
        "requests_today": 0, "extra_requests": 0, "unlimited_until": None,
        "last_request": None, "total_requests": 0,
        "reset_date": datetime.now().strftime("%Y-%m-%d"),
        "tokens": START_BONUS, "daily_bonus_claimed": None,
        "referral_code": "".join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(8)),
        "referred_by": None, "referrals": 0, "earned_tokens": 0, "used_promos": [],
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
    if user.get("unlimited_until"):
        try:
            if datetime.now() < datetime.fromisoformat(user["unlimited_until"]): return True
        except: pass
    return user.get("requests_today", 0) < (DAILY_LIMIT + user.get("extra_requests", 0))

def remaining(user_id):
    user = get_user(user_id)
    if user.get("unlimited_until"):
        try:
            if datetime.now() < datetime.fromisoformat(user["unlimited_until"]): return "безлимит"
        except: pass
    return max(0, DAILY_LIMIT + user.get("extra_requests", 0) - user.get("requests_today", 0))

def add_extra_requests(user_id, amount):
    users = load_users()
    if str(user_id) in users:
        users[str(user_id)]["extra_requests"] = users[str(user_id)].get("extra_requests", 0) + amount
        save_users(users)

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
    if promo["max_uses"] > 0 and len(promo["used_by"]) >= promo["max_uses"]: return False, "Лимит использований исчерпан"
    if str(user_id) in promo["used_by"]: return False, "Уже использован"
    add_tokens(user_id, promo["amount"])
    promo["used_by"].append(str(user_id))
    save_promos(promos)
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
        [InlineKeyboardButton("🎟 Промокод", callback_data="promo")],
    ])

# ═══════════════════════════════════════════
# 🚀 Команды
# ═══════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    extra = user.get("extra_requests", 0)
    total = DAILY_LIMIT + extra
    
    await update.message.reply_text(
        f"🧠 NeBlock AI V1\n━━━━━━━━━━━━━━━━\n"
        f"⚡ Быстрые ответы | 💻 Помощь с кодом\n"
        f"📊 Лимит: {total} запросов/день\n"
        f"💰 Баланс: {user.get('tokens', 0)} NeBlock Tokens\n\n"
        f"👇 Просто напиши вопрос:",
        reply_markup=main_reply_keyboard()
    )

async def admin_give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args or len(context.args) < 2: return
    try:
        add_tokens(int(context.args[0]), int(context.args[1]))
        await update.message.reply_text("✅ Начислено")
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
    text = "🎟 Промокоды:\n"
    for code, data in promos.items():
        text += f"\n{code}: {data['amount']} токенов | {len(data['used_by'])}/{data['max_uses'] if data['max_uses'] > 0 else '∞'}"
    await update.message.reply_text(text)

async def admin_delete_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args: return
    promos = load_promos()
    code = context.args[0].upper()
    if code in promos: del promos[code]; save_promos(promos); await update.message.reply_text("✅ Удалён")

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    await update.message.reply_text(f"📊 Пользователей: {len(load_users())}")

# ═══════════════════════════════════════════
# 🔘 Обычные кнопки
# ═══════════════════════════════════════════

async def reply_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    if text == "📝 Задать вопрос":
        await update.message.reply_text(f"📝 Напиши вопрос в чат.\n📊 Осталось: {remaining(user_id)}")
        return True
    if text == "👤 Профиль":
        user = get_user(user_id)
        extra = user.get("extra_requests", 0)
        await update.message.reply_text(
            f"👤 Профиль\n━━━━━━━━━━━━━━━━\n"
            f"🆔 {user_id}\n💰 {user.get('tokens', 0)} токенов\n"
            f"📊 {user.get('requests_today', 0)}/{DAILY_LIMIT + extra}"
        )
        return True
    if text == "🛒 Магазин":
        await update.message.reply_text(f"🛒 Магазин\n💰 Баланс: {get_tokens(user_id)} токенов", reply_markup=shop_keyboard())
        return True
    if text == "💰 Заработать":
        await update.message.reply_text(f"💰 Заработок\n💎 Баланс: {get_tokens(user_id)}", reply_markup=earn_keyboard())
        return True
    return False

# ═══════════════════════════════════════════
# 🔘 Inline кнопки
# ═══════════════════════════════════════════

async def inline_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if data == "menu":
        await query.edit_message_text(f"🧠 NeBlock AI V1\n💰 {get_tokens(user_id)} токенов", reply_markup=main_menu())
    elif data == "about":
        await query.edit_message_text("ℹ️ NeBlock AI V1\n⚡ Быстрые ответы", reply_markup=back_button())
    elif data == "profile":
        user = get_user(user_id)
        extra = user.get("extra_requests", 0)
        await query.edit_message_text(
            f"👤 Профиль\n🆔 {user_id}\n💰 {user.get('tokens', 0)} токенов\n📊 {user.get('requests_today', 0)}/{DAILY_LIMIT + extra}",
            reply_markup=back_button()
        )
    elif data == "shop":
        await query.edit_message_text(f"🛒 Магазин\n💰 {get_tokens(user_id)} токенов", reply_markup=shop_keyboard())
    elif data == "earn":
        await query.edit_message_text(f"💰 Заработок\n💎 {get_tokens(user_id)}", reply_markup=earn_keyboard())
    elif data == "promo":
        context.user_data["waiting_promo"] = True
        await query.edit_message_text("🎟 Отправь промокод в чат.", reply_markup=back_button())
    elif data == "faq":
        await query.edit_message_text("📚 FAQ\n\n❓ Лимит 5 запросов - чтобы не перегружать нейросеть.\n❓ Сброс в 00:00 МСК.", reply_markup=back_button())
    elif data == "daily_bonus":
        user = get_user(user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        if user.get("daily_bonus_claimed") == today:
            await query.answer("❌ Уже забирали сегодня!", show_alert=True)
        else:
            bonus = random.randint(DAILY_BONUS_MIN, DAILY_BONUS_MAX)
            users = load_users()
            users[str(user_id)]["daily_bonus_claimed"] = today
            save_users(users)
            add_tokens(user_id, bonus)
            await query.answer(f"🎉 +{bonus} токенов!", show_alert=True)
            await query.edit_message_text(f"🎁 +{bonus} токенов\n💰 Баланс: {get_tokens(user_id)}", reply_markup=back_button())
    elif data == "ref_link":
        user = get_user(user_id)
        bot_username = (await context.bot.get_me()).username
        await query.edit_message_text(f"👥 Твоя ссылка:\nhttps://t.me/{bot_username}?start=ref_{user.get('referral_code', '')}", reply_markup=back_button())
    elif data.startswith("confirm_"):
        item_id = data.replace("confirm_", "")
        item = SHOP_ITEMS.get(item_id)
        if not item: return
        tokens = get_tokens(user_id)
        if tokens < item["price"]:
            await query.answer("❌ Недостаточно токенов!", show_alert=True)
            return
        remove_tokens(user_id, item["price"])
        if item_id == "extra5": add_extra_requests(user_id, 5)
        elif item_id == "extra10": add_extra_requests(user_id, 10)
        elif item_id in ["unlimited_1h", "unlimited_24h", "unlimited_7d"]:
            hours = 1 if item_id == "unlimited_1h" else 24 if item_id == "unlimited_24h" else 168
            users = load_users()
            users[str(user_id)]["unlimited_until"] = (datetime.now() + timedelta(hours=hours)).isoformat()
            save_users(users)
        await query.answer("✅ Куплено!", show_alert=True)
        await query.edit_message_text(f"✅ {item['name']}\n💎 Остаток: {get_tokens(user_id)}", reply_markup=back_button())
    elif data.startswith("buy_"):
        item_id = data.replace("buy_", "")
        item = SHOP_ITEMS.get(item_id)
        if not item: return
        tokens = get_tokens(user_id)
        await query.edit_message_text(
            f"🛒 {item['icon']} {item['name']}\n💰 Цена: {item['price']}\n💎 Баланс: {tokens}",
            reply_markup=confirm_keyboard(item_id)
        )

# ═══════════════════════════════════════════
# 💬 Сообщения с анимацией
# ═══════════════════════════════════════════

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id
    
    if await reply_button_handler(update, context):
        return
    
    if context.user_data.get("waiting_promo"):
        context.user_data["waiting_promo"] = False
        success, result = use_promo(user_id, text)
        if success:
            await update.message.reply_text(f"🎟 +{result} токенов!\n💎 Баланс: {get_tokens(user_id)}")
        else:
            await update.message.reply_text(f"❌ {result}")
        return
    
    if not can_request(user_id):
        user = get_user(user_id)
        await update.message.reply_text(
            f"🚫 Лимит исчерпан!\n📊 {user.get('requests_today', 0)}/{DAILY_LIMIT + user.get('extra_requests', 0)}",
            reply_markup=limit_reached_keyboard()
        )
        return
    
    # Отправляем первое сообщение
    msg = await update.message.reply_text("🤔 Анализирую запрос\n█░░░░░░░░░ 10%")
    
    # Запускаем API запрос (синхронно в потоке)
    import concurrent.futures
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(lambda: client.responses.create(prompt={"id": PROMPT_ID}, input=text))
    
    # Проигрываем анимацию с задержками
    animation_steps = [
        ("🤔 Анализирую запрос", "█░░░░░░░░░ 10%", 0.7),
        ("🔍 Ищу информацию", "██░░░░░░░░ 20%", 0.7),
        ("⚡ Обрабатываю данные", "████░░░░░░ 40%", 0.8),
        ("🧠 Нейросеть думает", "██████░░░░ 60%", 0.8),
        ("📝 Формирую ответ", "████████░░ 80%", 0.8),
        ("✅ Завершаю", "██████████ 100%", 1.0),
    ]
    
    for label, bar, delay in animation_steps:
        try:
            await msg.edit_text(f"{label}\n{bar}")
            await asyncio.sleep(delay)
        except:
            break
    
    # Ждём ответ от API
    try:
        response = future.result(timeout=10)
        answer = response.output_text
    except:
        await msg.edit_text("❌ Ошибка генерации. Попробуй позже.")
        return
    
    await msg.delete()
    add_request(user_id)
    
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
        await update.message.reply_text("🤷 Пустой ответ")

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
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CallbackQueryHandler(inline_button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    print("✅ Бот запущен!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
