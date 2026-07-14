
import openai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import asyncio
import logging
import os
import json
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Загрузка конфига
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8700124191:AAE6qSSouLjlDxPWwoFObJORMbDotsby9co")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY", "AQVNy7Dm-dvQRzejHvH0383oHTZhhW2fda95I558")
PROMPT_ID = os.getenv("PROMPT_ID", "fvt621uiq1fftiu5qomu")

# Конфигурация
DAILY_LIMIT = 5
DATA_FILE = "users.json"
ADMIN_IDS = [1671403667]
START_BONUS = 50
DAILY_BONUS_MIN = 5
DAILY_BONUS_MAX = 15
REFERRAL_BONUS = 25
INVITED_BONUS = 10

# Магазин
SHOP_ITEMS = {
    "extra5": {"name": "+5 запросов", "price": 10, "desc": "Дополнительные запросы на сегодня"},
    "extra10": {"name": "+10 запросов", "price": 18, "desc": "Дополнительные запросы на сегодня"},
    "unlimited_1h": {"name": "Безлимит 1 час", "price": 30, "desc": "Неограниченные запросы на 1 час"},
    "unlimited_24h": {"name": "Безлимит 24 часа", "price": 100, "desc": "Неограниченные запросы на 24 часа"},
    "unlimited_7d": {"name": "Безлимит 7 дней", "price": 500, "desc": "Неограниченные запросы на неделю"},
}

# FAQ текст
FAQ_TEXT = """
ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ

Что такое NeBlock AI?
NeBlock AI — это Telegram бот с искусственным интеллектом. Он отвечает на вопросы, помогает с кодом, объясняет сложные темы и ведёт диалог.

Как пользоваться ботом?
Просто напиши свой вопрос в чат. Бот ответит автоматически. Никаких сложных команд не нужно.

Почему лимит 5 запросов в день?
Лимит установлен чтобы не перегружать нейросеть объёмными вопросами и обеспечить стабильную работу для всех пользователей. Каждый запрос обрабатывается на сервере, и слишком большая нагрузка может замедлить ответы.

Как увеличить лимит?
Купи дополнительные запросы или безлимитный режим в Магазине за токены. Токены можно заработать: ежедневный бонус, реферальная программа, админские награды.

Как получить токены?
- Ежедневный бонус: 5-15 токенов каждый день
- Реферальная программа: +25 токенов за приглашённого друга
- Стартовый бонус: 50 токенов при регистрации
- Админ может начислить токены за активность

Что такое реферальная программа?
Ты получаешь уникальную ссылку. Отправь её другу. Когда друг запустит бота по твоей ссылке, ты получишь +25 токенов, а друг +10 токенов.

Когда сбрасывается лимит?
Каждый день в 00:00 по московскому времени. Дополнительные запросы тоже сбрасываются.

Бот помнит историю диалога?
Да, бот учитывает контекст разговора. Можешь задавать уточняющие вопросы.

Какие темы можно обсуждать?
Любые: программирование, математика, физика, языки, история, креатив, бизнес. Бот не обсуждает политику и не даёт вредных советов.

Что делать если бот не отвечает?
1. Проверь интернет
2. Попробуй /start
3. Подожди пару минут
4. Напиши администратору

Как связаться с разработчиком?
Через GitHub: https://github.com/MaximErevanV3/NeBlockAI

Можно ли использовать бота бесплатно?
Да, 5 запросов в день бесплатно. Для большего количества нужны токены.

Бот работает круглосуточно?
Да, бот работает на сервере и доступен в любое время.

Мои данные в безопасности?
Бот хранит только статистику запросов и баланс токенов. Личные переписки не сохраняются.

Как удалить историю?
Используй кнопку "Очистить историю" в главном меню или напиши /start для сброса.

Бот понимает другие языки?
Да, бот автоматически определяет язык и отвечает на нём же.

Можно ли переводить токены другим пользователям?
Пока такой функции нет. Токены можно только заработать или получить от админа.

Что будет если закончатся токены?
Ты всё равно сможешь использовать 5 бесплатных запросов в день. Токены нужны только для дополнительных возможностей.

Как часто обновляется бот?
Разработчик регулярно добавляет новые функции. Следи за обновлениями в GitHub.
"""

# Логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NeBlockAI")

# Клиент
client = openai.OpenAI(
    api_key=YANDEX_API_KEY,
    base_url="https://ai.api.cloud.yandex.net/v1",
    project="b1guk4h3j9t48lsjl6sq",
    timeout=25.0,
)

# ==================== БАЗА ДАННЫХ ====================

def load_users():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(DATA_FILE, "w") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def get_user(user_id):
    users = load_users()
    uid = str(user_id)
    
    if uid not in users:
        users[uid] = {
            "joined": datetime.now().isoformat(),
            "requests_today": 0,
            "extra_requests": 0,
            "unlimited_until": None,
            "last_request": None,
            "total_requests": 0,
            "reset_date": datetime.now().strftime("%Y-%m-%d"),
            "tokens": START_BONUS,
            "daily_bonus_claimed": None,
            "referral_code": generate_ref_code(),
            "referred_by": None,
            "referrals": 0,
            "earned_tokens": 0,
        }
        save_users(users)
    
    today = datetime.now().strftime("%Y-%m-%d")
    if users[uid]["reset_date"] != today:
        users[uid]["requests_today"] = 0
        users[uid]["extra_requests"] = 0
        users[uid]["reset_date"] = today
        save_users(users)
    
    return users[uid]

def generate_ref_code():
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "".join(random.choice(chars) for _ in range(8))

def add_request(user_id):
    users = load_users()
    uid = str(user_id)
    if uid in users:
        users[uid]["requests_today"] += 1
        users[uid]["total_requests"] += 1
        users[uid]["last_request"] = datetime.now().isoformat()
        save_users(users)

def can_request(user_id):
    user = get_user(user_id)
    if user["unlimited_until"]:
        until = datetime.fromisoformat(user["unlimited_until"])
        if datetime.now() < until:
            return True
    return user["requests_today"] < (DAILY_LIMIT + user["extra_requests"])

def remaining(user_id):
    user = get_user(user_id)
    if user["unlimited_until"]:
        until = datetime.fromisoformat(user["unlimited_until"])
        if datetime.now() < until:
            return "безлимит"
    total_limit = DAILY_LIMIT + user["extra_requests"]
    return max(0, total_limit - user["requests_today"])

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
    user = get_user(user_id)
    return user.get("tokens", 0)

# ==================== КЛАВИАТУРЫ ====================

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Задать вопрос", callback_data="ask"),
         InlineKeyboardButton("О боте", callback_data="about")],
        [InlineKeyboardButton("Личный кабинет", callback_data="profile"),
         InlineKeyboardButton("Магазин", callback_data="shop")],
        [InlineKeyboardButton("Заработать токены", callback_data="earn"),
         InlineKeyboardButton("FAQ", callback_data="faq")],
        [InlineKeyboardButton("Помощь", callback_data="help")],
    ])

def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="menu")]])

def shop_keyboard():
    keyboard = [
        [InlineKeyboardButton("+5 запросов - 10 токенов", callback_data="buy_extra5")],
        [InlineKeyboardButton("+10 запросов - 18 токенов", callback_data="buy_extra10")],
        [InlineKeyboardButton("Безлимит 1ч - 30 токенов", callback_data="buy_unlimited_1h")],
        [InlineKeyboardButton("Безлимит 24ч - 100 токенов", callback_data="buy_unlimited_24h")],
        [InlineKeyboardButton("Безлимит 7д - 500 токенов", callback_data="buy_unlimited_7d")],
        [InlineKeyboardButton("Назад", callback_data="menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

def earn_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Забрать ежедневный бонус", callback_data="daily_bonus")],
        [InlineKeyboardButton("Моя реферальная ссылка", callback_data="ref_link")],
        [InlineKeyboardButton("Назад", callback_data="menu")],
    ])

# ==================== АНИМАЦИЯ ====================

async def loading_animation(msg, stop):
    frames = [
        "Генерация... [----------]",
        "Генерация... [##--------]",
        "Генерация... [####------]",
        "Генерация... [######----]",
        "Генерация... [########--]",
        "Готово! [##########]",
    ]
    i = 0
    while not stop.is_set():
        try:
            await msg.edit_text(frames[i % len(frames)])
            await asyncio.sleep(0.8)
            i += 1
        except:
            break

# ==================== КОМАНДЫ ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    tokens = get_tokens(user_id)
    
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
                            f"По твоей реферальной ссылке зарегистрировался новый пользователь!\n"
                            f"Начислено: +{REFERRAL_BONUS} токенов"
                        )
                    except:
                        pass
                break
    
    text = (
        "NeBlock AI V1\n"
        "----------------\n"
        "Быстрые ответы на вопросы\n"
        "Помощь с кодом и учёбой\n"
        f"Дневной лимит: {DAILY_LIMIT} запросов\n"
        f"Твой баланс: {tokens} токенов\n"
    )
    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu())
    else:
        await update.callback_query.edit_message_text(text, reply_markup=main_menu())

async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    await update.message.reply_text(get_profile_text(user_id, user))

def get_profile_text(user_id, user):
    joined = datetime.fromisoformat(user["joined"]).strftime("%d.%m.%Y")
    last = "Никогда"
    if user["last_request"]:
        last = datetime.fromisoformat(user["last_request"]).strftime("%H:%M %d.%m.%Y")
    
    unlimited = "Не активен"
    if user["unlimited_until"]:
        until = datetime.fromisoformat(user["unlimited_until"])
        if datetime.now() < until:
            unlimited = f"Активен до {until.strftime('%H:%M %d.%m')}"
    
    total_limit = DAILY_LIMIT + user["extra_requests"]
    
    return (
        "Личный кабинет\n"
        "----------------\n"
        f"ID: {user_id}\n"
        f"Присоединился: {joined}\n"
        f"Баланс: {user['tokens']} токенов\n"
        f"Заработано всего: {user.get('earned_tokens', 0)} токенов\n"
        f"Запросов сегодня: {user['requests_today']}/{total_limit}\n"
        f"Всего запросов: {user['total_requests']}\n"
        f"Безлимит: {unlimited}\n"
        f"Рефералов: {user.get('referrals', 0)}\n"
        f"Последний запрос: {last}\n"
    )

async def shop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    tokens = get_tokens(user_id)
    text = f"Магазин NeBlock\n----------------\nТвой баланс: {tokens} токенов\n"
    await update.message.reply_text(text, reply_markup=shop_keyboard())

async def faq_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(FAQ_TEXT)

async def give_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Нет доступа.")
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Использование: /give ID КОЛИЧЕСТВО")
        return
    
    target_id = int(args[0])
    amount = int(args[1])
    add_tokens(target_id, amount)
    
    await update.message.reply_text(f"Начислено {amount} токенов пользователю {target_id}")
    try:
        await context.bot.send_message(target_id, f"Админ начислил тебе {amount} токенов!")
    except:
        pass

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Нет доступа.")
        return
    
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Использование: /broadcast ТЕКСТ")
        return
    
    users = load_users()
    sent = 0
    for uid in users:
        try:
            await context.bot.send_message(int(uid), f"Рассылка от NeBlock AI:\n\n{text}")
            sent += 1
        except:
            pass
    
    await update.message.reply_text(f"Рассылка отправлена {sent} пользователям")

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Нет доступа.")
        return
    
    users = load_users()
    total_users = len(users)
    total_requests = sum(u.get("total_requests", 0) for u in users.values())
    total_tokens = sum(u.get("tokens", 0) for u in users.values())
    
    await update.message.reply_text(
        f"Статистика бота\n"
        f"----------------\n"
        f"Пользователей: {total_users}\n"
        f"Всего запросов: {total_requests}\n"
        f"Токенов в обороте: {total_tokens}\n"
    )

# ==================== КНОПКИ ====================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == "profile":
        user = get_user(user_id)
        await query.edit_message_text(get_profile_text(user_id, user), reply_markup=back_button())
        return
    
    if query.data == "shop":
        tokens = get_tokens(user_id)
        text = f"Магазин NeBlock\n----------------\nТвой баланс: {tokens} токенов\n"
        await query.edit_message_text(text, reply_markup=shop_keyboard())
        return
    
    if query.data == "earn":
        tokens = get_tokens(user_id)
        text = (
            "Способы заработка токенов\n"
            "----------------\n"
            f"Баланс: {tokens} токенов\n\n"
            "Ежедневный бонус: 5-15 токенов\n"
            "Реферальная программа:\n"
            f"- Ты получаешь +{REFERRAL_BONUS} токенов за друга\n"
            f"- Друг получает +{INVITED_BONUS} токенов\n"
            "Админские награды (активность, конкурсы)\n"
        )
        await query.edit_message_text(text, reply_markup=earn_keyboard(user_id))
        return
    
    if query.data == "faq":
        await query.edit_message_text(FAQ_TEXT, reply_markup=back_button())
        return
    
    if query.data == "daily_bonus":
        user = get_user(user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        
        if user.get("daily_bonus_claimed") == today:
            await query.answer("Ты уже забрал бонус сегодня! Приходи завтра.", show_alert=True)
            return
        
        bonus = random.randint(DAILY_BONUS_MIN, DAILY_BONUS_MAX)
        users = load_users()
        users[str(user_id)]["daily_bonus_claimed"] = today
        save_users(users)
        add_tokens(user_id, bonus)
        
        await query.answer(f"Получено +{bonus} токенов!", show_alert=True)
        await query.edit_message_text(
            f"Ежедневный бонус\n----------------\n"
            f"Получено: +{bonus} токенов\n"
            f"Текущий баланс: {get_tokens(user_id)} токенов\n"
            f"Приходи завтра за новым бонусом!",
            reply_markup=back_button()
        )
        return
    
    if query.data == "ref_link":
        user = get_user(user_id)
        ref_code = user["referral_code"]
        bot_username = (await context.bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start=ref_{ref_code}"
        
        await query.edit_message_text(
            f"Твоя реферальная ссылка:\n"
            f"----------------\n"
            f"{ref_link}\n\n"
            f"Приглашай друзей и получай +{REFERRAL_BONUS} токенов за каждого!\n"
            f"Твои рефералы: {user.get('referrals', 0)}",
            reply_markup=back_button()
        )
        return
    
    if query.data.startswith("buy_"):
        item_id = query.data.replace("buy_", "")
        item = SHOP_ITEMS.get(item_id)
        
        if not item:
            return
        
        tokens = get_tokens(user_id)
        
        if tokens < item["price"]:
            await query.answer(f"Недостаточно токенов! Нужно {item['price']}, у тебя {tokens}", show_alert=True)
            return
        
        remove_tokens(user_id, item["price"])
        users = load_users()
        uid = str(user_id)
        
        if item_id == "extra5":
            users[uid]["extra_requests"] += 5
        elif item_id == "extra10":
            users[uid]["extra_requests"] += 10
        elif item_id == "unlimited_1h":
            users[uid]["unlimited_until"] = (datetime.now() + timedelta(hours=1)).isoformat()
        elif item_id == "unlimited_24h":
            users[uid]["unlimited_until"] = (datetime.now() + timedelta(hours=24)).isoformat()
        elif item_id == "unlimited_7d":
            users[uid]["unlimited_until"] = (datetime.now() + timedelta(days=7)).isoformat()
        
        save_users(users)
        
        await query.answer(f"Куплено: {item['name']}!", show_alert=True)
        await query.edit_message_text(
            f"Покупка успешна!\n----------------\n"
            f"Товар: {item['name']}\n"
            f"Потрачено: {item['price']} токенов\n"
            f"Остаток: {get_tokens(user_id)} токенов",
            reply_markup=back_button()
        )
        return
    
    pages = {
        "ask": f"Задай вопрос в чат — я отвечу.\nОсталось запросов: {remaining(user_id)}",
        "about": "NeBlock AI V1\n\nМодель: NeBlock AI V1\nБыстрые и точные ответы\nПонимаю контекст диалога",
        "help": "Помощь\n\nПиши вопрос в чат\n/profile — кабинет\n/shop — магазин\n/faq — вопросы\n/start — меню",
    }
    
    if query.data in pages:
        await query.edit_message_text(pages[query.data], reply_markup=back_button())
    elif query.data == "menu":
        await start(update, context)

# ==================== СООБЩЕНИЯ ====================

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id
    
    if not text or len(text) > 2000:
        return
    
    if not can_request(user_id):
        user = get_user(user_id)
        await update.message.reply_text(
            f"Дневной лимит исчерпан!\n"
            f"----------------\n"
            f"Использовано: {user['requests_today']}/{DAILY_LIMIT + user['extra_requests']}\n"
            f"Баланс: {user['tokens']} токенов\n"
            f"Купи доп запросы в /shop\n"
            f"Сброс в 00:00 МСК"
        )
        return
    
    user_name = update.effective_user.first_name or "Пользователь"
    logger.info(f"Запрос от {user_name} ({user_id}): {text[:60]}")
    
    rem = remaining(user_id)
    rem_text = f"Осталось: {rem}" if isinstance(rem, int) else "Безлимит"
    
    load_msg = await update.message.reply_text(f"Генерация... ({rem_text})")
    stop = asyncio.Event()
    anim = asyncio.create_task(loading_animation(load_msg, stop))
    await update.message.chat.send_action("typing")
    
    try:
        response = client.responses.create(
            prompt={"id": PROMPT_ID},
            input=text,
        )
        answer = response.output_text
        
        add_request(user_id)
        
        stop.set()
        await anim
        await load_msg.delete()
        
        rem = remaining(user_id)
        rem_text = f"Осталось: {rem}" if isinstance(rem, int) else "Безлимит"
        
        if answer:
            for i in range(0, len(answer), 4000):
                chunk = answer[i:i+4000]
                if i == 0:
                    await update.message.reply_text(f"{chunk}\n\n----------------\n{rem_text}")
                else:
                    await update.message.reply_text(chunk)
        else:
            await update.message.reply_text("Не удалось сгенерировать ответ")
            
    except Exception as e:
        stop.set()
        await anim
        error = str(e)
        logger.error(f"Ошибка: {error[:100]}")
        
        if "timeout" in error.lower():
            await load_msg.edit_text("Превышено время ожидания. Попробуй ещё раз.")
        else:
            await load_msg.edit_text(f"Ошибка: {error[:100]}")

# ==================== ЗАПУСК ====================

def main():
    logger.info("NeBlock AI V1 запускается...")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("profile", profile_cmd))
    app.add_handler(CommandHandler("shop", shop_cmd))
    app.add_handler(CommandHandler("faq", faq_cmd))
    app.add_handler(CommandHandler("give", give_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    
    logger.info("Бот готов к работе!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
