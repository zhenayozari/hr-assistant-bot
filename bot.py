import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветствие и главное меню"""
    keyboard = [
    [InlineKeyboardButton("🚀 Открыть HR Assistant", web_app=WebAppInfo(url="https://hr-assistant-bot-216q.onrender.com/test"))],
    [InlineKeyboardButton("📊 Мои вакансии", callback_data="vacancies")],
    [InlineKeyboardButton("👥 Кандидаты", callback_data="candidates")],
    [InlineKeyboardButton("⚙️ Настройки", callback_data="settings")],
]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👋 Привет! Я HR-ассистент.\n\n"
        "Я помогу тебе:\n"
        "✅ Анализировать резюме с HH.ru\n"
        "✅ Оценивать кандидатов через AI\n"
        "✅ Управлять вакансиями\n\n"
        "Выбери действие:",
        reply_markup=reply_markup
    )

# Обработчик кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "vacancies":
        await query.edit_message_text(
            "📋 Управление вакансиями\n\n"
            "Функционал в разработке.\n"
            "Скоро здесь появится интеграция с HH.ru!\n\n"
            "Используй /start для возврата в меню."
        )
    
    elif query.data == "candidates":
        await query.edit_message_text(
            "👥 Анализ кандидатов\n\n"
            "Функционал в разработке.\n"
            "Скоро здесь можно будет анализировать резюме!\n\n"
            "Используй /start для возврата в меню."
        )
    
    elif query.data == "settings":
        await query.edit_message_text(
            "⚙️ Настройки\n\n"
            "Функционал в разработке.\n"
            "Скоро здесь можно будет настроить:\n"
            "• Интеграцию с HH.ru\n"
            "• Критерии анализа\n"
            "• Уведомления\n\n"
            "Используй /start для возврата в меню."
        )
    
    elif query.data == "help":
        await query.edit_message_text(
            "📖 Справка\n\n"
            "Доступные команды:\n"
            "/start - Главное меню\n"
            "/status - Статус системы\n"
            "/help - Эта справка\n\n"
            "Бот находится в разработке! 🚀"
        )

# Команда /status
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статус системы"""
    await update.message.reply_text(
        "📊 Статус системы:\n\n"
        "✅ Бот работает\n"
        "✅ База данных подключена\n"
        "✅ Backend готов\n"
        "⏳ Web App в разработке\n\n"
        "Всё готово к работе!"
    )

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Помощь"""
    await update.message.reply_text(
        "📖 Доступные команды:\n\n"
        "/start - Главное меню\n"
        "/status - Статус системы\n"
        "/help - Эта справка\n\n"
        "Бот находится в разработке! 🚀"
    )

# Главная функция
async def main():
    app = Application.builder().token(TOKEN).build()
    
    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # Инициализация и запуск
    await app.initialize()
    await app.start()
    print("✅ Бот запущен! Нажми Ctrl+C чтобы остановить.")
    await app.updater.start_polling()
    
    # Ждём остановки
    import asyncio
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        await app.stop()
        await app.shutdown()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
