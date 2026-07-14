import openai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import asyncio
import logging
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Конфиг из переменных окружения (безопасно!)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8700124191:AAE6qSSouLjlDxPWwoFObJORMbDotsby9co")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY", "AQVNy7Dm-dvQRzejHvH0383oHTZhhW2fda95I558")
PROMPT_ID = os.getenv("PROMPT_ID", "fvt621uiq1fftiu5qomu")

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Клиент Deepseek
client = openai.OpenAI(
    api_key=YANDEX_API_KEY,
    base_url="https://ai.api.cloud.yandex.net/v1",
    project="b1guk4h3j9t48lsjl6sq",
    timeout=30.0,
)

# Клавиатуры
def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Задать вопрос", callback_data="ask"),
         InlineKeyboardButton("ℹ️ О боте", callback_data="about")],
        [InlineKeyboardButton("🔄 Очистить историю", callback_data="clear"),
         InlineKeyboardButton("❓ Помощь", callback_data="help")],
    ])

def get_back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Назад", callback_data="menu")]
    ])

# Анимация загрузки
async def show_loading_animation(message, stop_event):
    frames = [
        "⚡ *Генерирую ответ* ░░░░░░░░░░ 0%",
        "⚡ *Генерирую ответ* ██░░░░░░░░ 20%",
        "⚡ *Генерирую ответ* ████░░░░░░ 40%",
        "⚡ *Генерирую ответ* ██████░░░░ 60%",
        "⚡ *Генерирую ответ* ████████░░ 80%",
        "✅ *Готово!* ██████████ 100%",
    ]
    
    frame_idx = 0
    while not stop_event.is_set():
        try:
            await message.edit_text(frames[frame_idx % len(frames)], parse_mode="Markdown")
            await asyncio.sleep(1.0)
            frame_idx += 1
        except:
            break

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🧠 *Neblock AI*\n"
        "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        "⚡ Deepseek V4 Flash\n"
        "💬 Контекстные ответы\n"
        "💻 Пишет код\n"
        "📚 Помощь в учёбе\n"
        "🖥️ Работает на VPS 24/7\n"
    )
    
    if update.message:
        await update.message.reply_text(text, reply_markup=get_main_keyboard(), parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    pages = {
        "ask": "✍️ *Задай вопрос*\n\nНапиши в чат что угодно:\n• Код\n• Объяснение\n• Задачи\n• Перевод",
        "about": "ℹ️ *Neblock AI*\n\n🧠 Deepseek V4 Flash\n☁️ Yandex Cloud\n🖥️ VPS Server\n⚡ 24/7 Online",
        "clear": "✅ *Готово!*\nИстория очищена.",
        "help": "❓ *Помощь*\n\nПиши в чат - бот ответит\n/start - меню\n/clear - очистка",
    }
    
    if query.data in pages:
        await query.edit_message_text(pages[query.data], reply_markup=get_back_keyboard(), parse_mode="Markdown")
    elif query.data == "menu":
        await start(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if not text or len(text) > 2000:
        return
    
    user = update.effective_user.username or update.effective_user.id
    logger.info(f"Запрос от @{user}: {text[:50]}...")
    
    loading_msg = await update.message.reply_text("⚡ *Запускаю нейросеть*...", parse_mode="Markdown")
    stop_animation = asyncio.Event()
    animation_task = asyncio.create_task(show_loading_animation(loading_msg, stop_animation))
    
    await update.message.chat.send_action("typing")
    
    try:
        response = client.responses.create(
            prompt={"id": PROMPT_ID},
            input=text,
        )
        answer = response.output_text
        
        stop_animation.set()
        await animation_task
        await loading_msg.delete()
        
        if answer:
            for i in range(0, len(answer), 4000):
                await update.message.reply_text(answer[i:i+4000])
        else:
            await update.message.reply_text("🤷 Модель не дала ответа")
            
    except Exception as e:
        stop_animation.set()
        await animation_task
        
        error = str(e)
        logger.error(f"Ошибка: {error[:100]}")
        
        if "timeout" in error.lower():
            await loading_msg.edit_text("⏰ *Таймаут*", parse_mode="Markdown")
        else:
            await loading_msg.edit_text(f"❌ *Ошибка*\n`{error[:100]}`", parse_mode="Markdown")

# Запуск
def main():
    logger.info("=" * 30)
    logger.info("🧠 Neblock AI запускается на VPS")
    logger.info("=" * 30)
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("✅ Бот запущен!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
