import openai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import asyncio
import logging
import os
from dotenv import load_dotenv

# Загрузка конфига
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8700124191:AAE6qSSouLjlDxPWwoFObJORMbDotsby9co")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY", "AQVNy7Dm-dvQRzejHvH0383oHTZhhW2fda95I558")
PROMPT_ID = os.getenv("PROMPT_ID", "fvt621uiq1fftiu5qomu")

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

# Клавиатуры
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Задать вопрос", callback_data="ask"),
         InlineKeyboardButton("ℹ️ О боте", callback_data="about")],
        [InlineKeyboardButton("🔄 Очистить историю", callback_data="clear"),
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
        "📚 Ответы на вопросы\n"
    )
    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu(), parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(text, reply_markup=main_menu(), parse_mode="Markdown")

# Кнопки
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    pages = {
        "ask": "✍️ *Задай вопрос*\n\nПросто напиши в чат — я отвечу!",
        "about": "ℹ️ *NeBlock AI V1*\n\n🧠 Модель: NeBlock AI V1\n☁️ Хостинг: Yandex Cloud\n⚡ Быстрые и точные ответы",
        "clear": "✅ История диалога очищена!",
        "help": "❓ *Помощь*\n\n📝 Пиши вопрос в чат\n🔄 /start — главное меню\n🧹 /clear — очистить историю",
    }
    
    if query.data in pages:
        await query.edit_message_text(pages[query.data], reply_markup=back_button(), parse_mode="Markdown")
    elif query.data == "menu":
        await start(update, context)

# Сообщения
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if not text or len(text) > 2000:
        return
    
    user = update.effective_user.first_name or "Пользователь"
    logger.info(f"Запрос от {user}: {text[:60]}")
    
    # Запуск анимации
    load_msg = await update.message.reply_text("⚡ Генерация...")
    stop = asyncio.Event()
    anim = asyncio.create_task(loading_animation(load_msg, stop))
    await update.message.chat.send_action("typing")
    
    try:
        response = client.responses.create(
            prompt={"id": PROMPT_ID},
            input=text,
        )
        answer = response.output_text
        
        stop.set()
        await anim
        await load_msg.delete()
        
        if answer:
            # Разбивка длинных сообщений
            for i in range(0, len(answer), 4000):
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

# Запуск
def main():
    logger.info("🧠 NeBlock AI V1 запускается...")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    
    logger.info("✅ Бот готов к работе!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
