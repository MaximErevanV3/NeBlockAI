import openai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import logging
import os
import json
import random
from datetime import datetime, timedelta

# ═══════════════════════════════════════════
# 🧠 NeBlock AI V1 - Конфигурация
# ═══════════════════════════════════════════

TELEGRAM_TOKEN = "8700124191:AAE6qSSouLjlDxPWwoFObJORMbDotsby9co"
YANDEX_API_KEY = "AQVNy7Dm-dvQRzejHvH0383oHTZhhW2fda95I558"
PROMPT_ID = "fvt621uiq1fftiu5qomu"
DAILY_LIMIT = 5
DATA_FILE = "users.json"
ADMIN_IDS = [1671403667]
START_BONUS = 50
DAILY_BONUS_MIN = 5
DAILY_BONUS_MAX = 15
REFERRAL_BONUS = 25
INVITED_BONUS = 10

SHOP_ITEMS = {
    "extra5": {"name": "+5 запросов", "price": 10, "icon": "📦", "desc": "Добавляет 5 запросов к дневному лимиту"},
    "extra10": {"name": "+10 запросов", "price": 18, "icon": "📦", "desc": "Добавляет 10 запросов к дневному лимиту"},
    "unlimited_1h": {"name": "Безлимит 1 час", "price": 30, "icon": "⚡", "desc": "Безлимитные запросы на 1 час"},
    "unlimited_24h": {"name": "Безлимит 24 часа", "price": 100, "icon": "⚡", "desc": "Безлимитные запросы на 24 часа"},
    "unlimited_7d": {"name": "Безлимит 7 дней", "price": 500, "icon": "🔥", "desc": "Безлимитные запросы на 7 дней"},
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

def load_users():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

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
    }
    
    if uid not in users:
        users[uid] = defaults.copy()
        save_users(users)
    else:
        for key, value in defaults.items():
            if key not in users[uid]:
                users[uid][key] = value
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

def add_tokens(user_id, amount):
    users = load_users()
    uid = str(user_id)
    if uid in users:
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

# ═══════════════════════════════════════════
# 🎛 Клавиатуры
# ═══════════════════════════════════════════

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Задать вопрос", callback_data="ask"),
         InlineKeyboardButton("ℹ️ О боте", callback_data="about")],
        [InlineKeyboardButton("👤 Личный кабинет", callback_data="profile"),
         InlineKeyboardButton("🛒 Магазин", callback_data="shop")],
        [InlineKeyboardButton("💰 Заработать токены", callback_data="earn"),
         InlineKeyboardButton("📚 FAQ", callback_data="faq")],
    ])

def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="menu")]])

def shop_keyboard():
    keyboard = []
    for item_id, item in SHOP_ITEMS.items():
        keyboard.append([InlineKeyboardButton(
            f"{item['icon']} {item['name']} — {item['price']} токенов",
            callback_data=f"buy_{item_id}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="menu")])
    return InlineKeyboardMarkup(keyboard)

def confirm_keyboard(item_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Подтвердить покупку", callback_data=f"confirm_{item_id}")],
        [InlineKeyboardButton("❌ Отмена", callback_data="shop")],
    ])

def earn_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 Ежедневный бонус", callback_data="daily_bonus")],
        [InlineKeyboardButton("👥 Реферальная ссылка", callback_data="ref_link")],
        [InlineKeyboardButton("🔙 Назад", callback_data="menu")],
    ])

# ═══════════════════════════════════════════
# 🚀 Команда /start
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
                        await context.bot.send_message(
                            int(u_id),
                            f"🎉 Новый пользователь по твоей ссылке!\n💰 +{REFERRAL_BONUS} NeBlock Tokens"
                        )
                    except:
                        pass
                break
    
    text = (
        f"🧠 NeBlock AI V1\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"⚡ Быстрые и точные ответы\n"
        f"💻 Помощь с программированием\n"
        f"📚 Объяснение сложных тем\n"
        f"🌐 Поддержка всех языков\n\n"
        f"📊 Дневной лимит: {DAILY_LIMIT} запросов\n"
        f"💰 Твой баланс: {user.get('tokens', 0)} токенов\n\n"
        f"👇 Выбери действие или просто напиши вопрос:"
    )
    await update.message.reply_text(text, reply_markup=main_menu())

# ═══════════════════════════════════════════
# 🔘 Обработчик кнопок
# ═══════════════════════════════════════════

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    logger.info(f"Кнопка: {data} | Пользователь: {user_id}")
    
    # 🔙 Назад в меню
    if data == "menu":
        user = get_user(user_id)
        text = (
            f"🧠 NeBlock AI V1\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📊 Лимит: {DAILY_LIMIT} запросов/день\n"
            f"💰 Баланс: {user.get('tokens', 0)} токенов\n\n"
            f"👇 Выбери действие:"
        )
        await query.edit_message_text(text, reply_markup=main_menu())
        return
    
    # 📝 Задать вопрос
    if data == "ask":
        text = (
            f"📝 Задай свой вопрос\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"Просто напиши в чат что угодно.\n"
            f"Я отвечу быстро и по делу.\n\n"
            f"📊 Осталось запросов: {remaining(user_id)}"
        )
        await query.edit_message_text(text, reply_markup=back_button())
        return
    
    # ℹ️ О боте
    if data == "about":
        text = (
            f"ℹ️ О NeBlock AI\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🧠 Модель: NeBlock AI V1\n"
            f"⚡ Быстрые ответы\n"
            f"💬 Понимание контекста\n"
            f"🌐 Все языки\n"
            f"💰 Внутренняя экономика"
        )
        await query.edit_message_text(text, reply_markup=back_button())
        return
    
    # 👤 Личный кабинет
    if data == "profile":
        user = get_user(user_id)
        joined = datetime.fromisoformat(user.get("joined", datetime.now().isoformat())).strftime("%d.%m.%Y")
        last = "Никогда"
        if user.get("last_request"):
            last = datetime.fromisoformat(user["last_request"]).strftime("%H:%M %d.%m.%Y")
        
        unlimited = "Не активен"
        if user.get("unlimited_until"):
            try:
                until = datetime.fromisoformat(user["unlimited_until"])
                if datetime.now() < until:
                    diff = until - datetime.now()
                    h = diff.seconds // 3600
                    m = (diff.seconds % 3600) // 60
                    unlimited = f"Активен (ещё {h}ч {m}м)"
            except:
                pass
        
        text = (
            f"👤 Личный кабинет\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🆔 ID: {user_id}\n"
            f"📅 Регистрация: {joined}\n"
            f"💰 Баланс: {user.get('tokens', 0)} токенов\n"
            f"💎 Заработано: {user.get('earned_tokens', 0)}\n"
            f"📊 Запросов сегодня: {user.get('requests_today', 0)}/{DAILY_LIMIT + user.get('extra_requests', 0)}\n"
            f"📈 Всего запросов: {user.get('total_requests', 0)}\n"
            f"⚡ Безлимит: {unlimited}\n"
            f"👥 Рефералов: {user.get('referrals', 0)}\n"
            f"🕐 Последний запрос: {last}"
        )
        await query.edit_message_text(text, reply_markup=back_button())
        return
    
    # 🛒 Магазин
    if data == "shop":
        text = (
            f"🛒 Магазин NeBlock\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"💰 Баланс: {get_tokens(user_id)} токенов\n\n"
            f"Выбери товар:"
        )
        await query.edit_message_text(text, reply_markup=shop_keyboard())
        return
    
    # 💰 Заработок
    if data == "earn":
        text = (
            f"💰 Заработок токенов\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"💎 Баланс: {get_tokens(user_id)} токенов\n\n"
            f"🎁 Ежедневный бонус: {DAILY_BONUS_MIN}-{DAILY_BONUS_MAX} токенов\n"
            f"👥 Рефералы: +{REFERRAL_BONUS} тебе, +{INVITED_BONUS} другу\n"
            f"🎯 Стартовый бонус: {START_BONUS} токенов"
        )
        await query.edit_message_text(text, reply_markup=earn_keyboard())
        return
    
    # 📚 FAQ
    if data == "faq":
        text = (
            f"📚 Частые вопросы\n"
            f"━━━━━━━━━━━━━━━━\n\n"
            f"❓ Что такое NeBlock AI?\n"
            f"ИИ-бот в Telegram. Отвечает на вопросы, пишет код, объясняет темы.\n\n"
            f"❓ Почему лимит 5 запросов?\n"
            f"Чтобы не перегружать нейросеть и сохранять быстрые ответы для всех.\n\n"
            f"❓ Что такое NeBlock Tokens?\n"
            f"Внутренняя валюта бота для покупок в Магазине. Не продаётся за деньги.\n\n"
            f"❓ Как заработать токены?\n"
            f"Ежедневный бонус, реферальная программа, стартовый бонус.\n\n"
            f"❓ Когда сбрасывается лимит?\n"
            f"Каждый день в 00:00 по московскому времени.\n\n"
            f"❓ Бот помнит контекст?\n"
            f"Да, можно вести диалог и задавать уточняющие вопросы.\n\n"
            f"❓ Какие языки понимает?\n"
            f"Автоматически определяет язык и отвечает на нём же."
        )
        await query.edit_message_text(text, reply_markup=back_button())
        return
    
    # 🎁 Ежедневный бонус
    if data == "daily_bonus":
        user = get_user(user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        
        if user.get("daily_bonus_claimed") == today:
            await query.answer("❌ Вы уже забирали ежедневный бонус сегодня!\n🔄 Возвращайтесь завтра в 00:00 МСК.", show_alert=True)
            return
        
        bonus = random.randint(DAILY_BONUS_MIN, DAILY_BONUS_MAX)
        users = load_users()
        users[str(user_id)]["daily_bonus_claimed"] = today
        save_users(users)
        add_tokens(user_id, bonus)
        
        await query.answer(f"🎉 Поздравляем! Вы получили +{bonus} NeBlock Tokens!", show_alert=True)
        text = (
            f"🎁 Ежедневный бонус\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"✅ Получено: +{bonus} токенов\n"
            f"💰 Текущий баланс: {get_tokens(user_id)} токенов\n\n"
            f"🔄 Приходите завтра за новым бонусом!"
        )
        await query.edit_message_text(text, reply_markup=back_button())
        return
    
    # 👥 Реферальная ссылка
    if data == "ref_link":
        user = get_user(user_id)
        bot_username = (await context.bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start=ref_{user.get('referral_code', '')}"
        
        text = (
            f"👥 Реферальная программа\n"
            f"━━━━━━━━━━━━━━━━\n\n"
            f"🔗 Твоя ссылка:\n{ref_link}\n\n"
            f"💰 Ты получишь: +{REFERRAL_BONUS} токенов\n"
            f"🎁 Друг получит: +{INVITED_BONUS} токенов\n"
            f"👥 Приглашено: {user.get('referrals', 0)}"
        )
        await query.edit_message_text(text, reply_markup=back_button())
        return
    
    # 🛍 Подтверждение покупки
    if data.startswith("confirm_"):
        item_id = data.replace("confirm_", "")
        item = SHOP_ITEMS.get(item_id)
        
        if not item:
            return
        
        tokens = get_tokens(user_id)
        
        if tokens < item["price"]:
            await query.answer(f"❌ Недостаточно токенов!\n💎 Нужно: {item['price']}\n💰 У вас: {tokens}", show_alert=True)
            return
        
        # Списываем токены
        remove_tokens(user_id, item["price"])
        users = load_users()
        uid = str(user_id)
        
        if item_id == "extra5":
            users[uid]["extra_requests"] = users[uid].get("extra_requests", 0) + 5
        elif item_id == "extra10":
            users[uid]["extra_requests"] = users[uid].get("extra_requests", 0) + 10
        elif item_id == "unlimited_1h":
            users[uid]["unlimited_until"] = (datetime.now() + timedelta(hours=1)).isoformat()
        elif item_id == "unlimited_24h":
            users[uid]["unlimited_until"] = (datetime.now() + timedelta(hours=24)).isoformat()
        elif item_id == "unlimited_7d":
            users[uid]["unlimited_until"] = (datetime.now() + timedelta(days=7)).isoformat()
        
        save_users(users)
        
        await query.answer(f"✅ Покупка успешна! {item['name']} активирован!", show_alert=True)
        text = (
            f"✅ Покупка успешна!\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🛒 Товар: {item['name']}\n"
            f"📝 Описание: {item['desc']}\n"
            f"💰 Потрачено: {item['price']} токенов\n"
            f"💎 Остаток: {get_tokens(user_id)} токенов\n\n"
            f"🔙 Вернуться в магазин:"
        )
        await query.edit_message_text(text, reply_markup=back_button())
        return
    
    # 🛍 Выбор товара (показ подтверждения)
    if data.startswith("buy_"):
        item_id = data.replace("buy_", "")
        item = SHOP_ITEMS.get(item_id)
        
        if not item:
            return
        
        tokens = get_tokens(user_id)
        
        text = (
            f"🛒 Подтверждение покупки\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"Товар: {item['icon']} {item['name']}\n"
            f"Описание: {item['desc']}\n"
            f"Цена: {item['price']} токенов\n"
            f"Ваш баланс: {tokens} токенов\n\n"
            f"{'✅ Достаточно средств' if tokens >= item['price'] else '❌ Недостаточно средств!'}\n\n"
            f"Подтвердите покупку:"
        )
        await query.edit_message_text(text, reply_markup=confirm_keyboard(item_id))
        return

# ═══════════════════════════════════════════
# 💬 Обработчик сообщений
# ═══════════════════════════════════════════

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    logger.info(f"Сообщение от {user_id}: {text[:50]}")
    
    if not can_request(user_id):
        user = get_user(user_id)
        text = (
            f"🚫 Лимит исчерпан!\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📊 Использовано: {user.get('requests_today', 0)}/{DAILY_LIMIT + user.get('extra_requests', 0)}\n"
            f"💰 Баланс: {user.get('tokens', 0)} токенов\n\n"
            f"🛒 Купи доп запросы в Магазине\n"
            f"🔄 Сброс в 00:00 МСК"
        )
        await update.message.reply_text(text)
        return
    
    msg = await update.message.reply_text("⚡ Генерирую ответ...")
    
    try:
        response = client.responses.create(
            prompt={"id": PROMPT_ID},
            input=text,
        )
        answer = response.output_text
        
        add_request(user_id)
        
        await msg.delete()
        
        if answer:
            rem = remaining(user_id)
            footer = f"\n\n━━━━━━━━━━━━━━━━\n📊 Осталось: {rem}"
            
            for i in range(0, len(answer), 4000):
                chunk = answer[i:i+4000]
                if i == 0:
                    await update.message.reply_text(chunk + footer)
                else:
                    await update.message.reply_text(chunk)
        else:
            await update.message.reply_text("🤷 Не удалось сгенерировать ответ. Попробуй переформулировать вопрос.")
            
    except Exception as e:
        try:
            await msg.delete()
        except:
            pass
        
        error = str(e)
        logger.error(f"Ошибка: {error[:100]}")
        
        if "timeout" in error.lower():
            await update.message.reply_text("⏰ Нейросеть не успела ответить. Попробуй ещё раз.")
        else:
            await update.message.reply_text("❌ Произошла ошибка. Попробуй позже.")

# ═══════════════════════════════════════════
# 🚀 Запуск
# ═══════════════════════════════════════════

def main():
    print("╔════════════════════════════════╗")
    print("║     🧠 NeBlock AI V1          ║")
    print("║     Бот запускается...        ║")
    print("╚════════════════════════════════╝")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    logger.info("✅ Бот готов к работе!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
