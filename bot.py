import openai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import asyncio
import logging
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Загрузка конфига
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8700124191:AAE6qSSouLjlDxPWwoFObJORMbDotsby9co")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY", "AQVNy7Dm-dvQRzejHvH0383oHTZhhW2fda95I558")
PROMPT_ID = os.getenv("PROMPT_ID", "fvt621uiq1fftiu5qomu")

# Лимиты
DAILY_LIMIT = 5
DATA_FILE = "users.json"

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

# База пользователей
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
            "last_request": None,
            "total_requests": 0,
            "reset_date": datetime.now().strftime("%Y-%m-%d"),
        }
        save_users(users)
    
    # Сброс счётчика если новый день
    today = datetime.now().strftime("%Y-%m-%d")
    if users[uid]["reset_date"] != today:
        users[uid]["requests_today"] = 0
        users[uid]["reset_date"] = today
        save_users(users)
    
    return users[uid]

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
    return user["requests_today"] < DAILY_LIMIT

def remaining(user_id):
    user = get_user(user_id)
    return max(0, DAILY_LIMIT - user["requests_today"])

# Клавиатуры
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Задать вопрос", callback_data="ask"),
         InlineKeyboardButton("ℹ️ О боте", callback_data="about")],
        [InlineKeyboardButton("👤 Личный кабинет", callback_data="profile"),
         InlineKeyboardButton("❓ Помощь", callback_data="help")],
    ])

def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="menu")]])

# Анимация загрузки
async def loading_animation(msg, stop):
    frames = [
        "⚡ Генерация... ░░░░░░░░░░",
        "⚡ Генерация... ██░░░░░░░░",
        "⚡ Генерация... ████░░░░░░",
        "⚡ Генерация... ██████░░░░",
        "⚡ Генерация... ████████░░",
        "✅ Готово! ██████████",
    ]
    i = 0
    while not stop.is_set():
        try:
            await msg.edit_text(frames[i % len(frames)])
            await asyncio.sleep(0.8)
            i += 1
        except:
            break

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🧠 *NeBlock AI V1*\n"
        "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        "⚡ Быстрые ответы\n"
        "💬 Понимание контекста\n"
        "💻 Помощь с кодом\n"
        f"📊 Лимит: {DAILY_LIMIT} запросов/день\n"
    )
    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu(), parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(text, reply_markup=main_menu(), parse_mode="Markdown")

# Кнопки
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == "profile":
        user = get_user(user_id)
        joined = datetime.fromisoformat(user["joined"]).strftime("%d.%m.%Y")
        last = "Никогда"
        if user["last_request"]:
            last = datetime.fromisoformat(user["last_request"]).strftime("%H:%M %d.%m.%Y")
        
        text = (
            "👤 *Личный кабинет*\n"
            "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            f"🆔 ID: `{user_id}`\n"
            f"📅 Присоединился: {joined}\n"
            f"📊 Запросов сегодня: {user['requests_today']}/{DAILY_LIMIT}\n"
            f"📈 Всего запросов: {user['total_requests']}\n"
            f"⏰ Осталось: {remaining(user_id)}\n"
            f"🕐 Последний запрос: {last}\n"
        )
        await query.edit_message_text(text, reply_markup=back_button(), parse_mode="Markdown")
        return
    
    pages = {
        "ask": f"✍️ *Задай вопрос*\n\nПросто напиши в чат — я отвечу!\n📊 Осталось запросов: {remaining(user_id)}",
        "about": "ℹ️ *NeBlock AI V1*\n\n🧠 Модель: NeBlock AI V1\n⚡ Быстрые и точные ответы\n💬 Понимаю контекст диалога",
        "help": f"❓ *Помощь*\n\n📝 Пиши вопрос в чат\n📊 Лимит: {DAILY_LIMIT} запросов/день\n👤 /profile — личный кабинет\n🔄 /start — главное меню",
    }
    
    if query.data in pages:
        await query.edit_message_text(pages[query.data], reply_markup=back_button(), parse_mode="Markdown")
    elif query.data == "menu":
        await start(update, context)

# Сообщения
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id
    
    if not text or len(text) > 2000:
        return
    
    # Проверка лимита
    if not can_request(user_id):
        user = get_user(user_id)
        await update.message.reply_text(
            f"🚫 *Дневной лимит исчерпан!*\n"
            f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            f"📊 Использовано: {user['requests_today']}/{DAILY_LIMIT}\n"
            f"⏰ Сброс в 00:00\n"
            f"👤 /profile — статистика",
            parse_mode="Markdown"
        )
        return
    
    user = update.effective_user.first_name or "Пользователь"
    logger.info(f"Запрос от {user} ({user_id}): {text[:60]}")
    
    # Запуск анимации
    load_msg = await update.message.reply_text(f"⚡ Генерация... (осталось: {remaining(user_id)-1})")
    stop = asyncio.Event()
    anim = asyncio.create_task(loading_animation(load_msg, stop))
    await update.message.chat.send_action("typing")
    
    try:
        response = client.responses.create(
            prompt={"id": PROMPT_ID},
            input=text,
        )
        answer = response.output_text
        
        # Учитываем запрос
        add_request(user_id)
        
        stop.set()
        await anim
        await load_msg.delete()
        
        if answer:
            # Разбивка длинных сообщений
            for i in range(0, len(answer), 4000):
                if i == 0:
                    await update.message.reply_text(
                        f"{answer[i:i+4000]}\n\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
                        f"📊 Осталось: {remaining(user_id)}/{DAILY_LIMIT}"
                    )
                else:
                    await update.message.reply_text(answer[i:i+4000])
        else:
            await update.message.reply_text("🤷 Не удалось сгенерировать ответ")
            
    except Exception as e:
        stop.set()
        await anim
        error = str(e)
        logger.error(f"Ошибка: {error[:100]}")
        
        if "timeout" in error.lower():
            await load_msg.edit_text("⏰ Превышено время ожидания")
        else:
            await load_msg.edit_text(f"❌ Ошибка: {error[:100]}")

# /profile
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    joined = datetime.fromisoformat(user["joined"]).strftime("%d.%m.%Y")
    last = "Никогда"
    if user["last_request"]:
        last = datetime.fromisoformat(user["last_request"]).strftime("%H:%M %d.%m.%Y")
    
    text = (
        "👤 *Личный кабинет*\n"
        "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🆔 ID: `{user_id}`\n"
        f"📅 Присоединился: {joined}\n"
        f"📊 Запросов сегодня: {user['requests_today']}/{DAILY_LIMIT}\n"
        f"📈 Всего запросов: {user['total_requests']}\n"
        f"⏰ Осталось: {remaining(user_id)}\n"
        f"🕐 Последний запрос: {last}\n"
        f"🔄 Сброс: в 00:00 МСК\n"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# Запуск
def main():
    logger.info("🧠 NeBlock AI V1 запускается...")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    
    logger.info("✅ Бот готов к работе!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
