#!/usr/bin/env python3
"""
Telegram Bot Interface for Agent Orchestrator
Chat with your AI assistants through Telegram
"""

import os
import sys
import asyncio
from typing import Dict

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import Update, BotCommand
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters,
    ContextTypes
)
from loguru import logger
from dotenv import load_dotenv

from orchestrator import Orchestrator
from assistants_config import ASSISTANTS

load_dotenv()

# Store orchestrator instances per user
user_orchestrators: Dict[int, Orchestrator] = {}


def get_orchestrator(user_id: int) -> Orchestrator:
    """Get or create orchestrator for a user"""
    if user_id not in user_orchestrators:
        user_orchestrators[user_id] = Orchestrator()
    return user_orchestrators[user_id]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_text = """
👋 Привет! Я твой AI Project Manager.

Я помогу управлять твоими проектами через команду агентов:
• 👑 Chief of Staff - главный координатор
• 🎧 Deep Listening - DL проекты
• 💻 LSRC Tech - техническая разработка
• 🎬 Documentary - фильм
• 🎨 Billboards & Experiments
• 🌐 Digital Presence - сайт и соцсети

Команды:
/status - статус всех проектов
/agents - список агентов
/ask <agent> <message> - спросить конкретного агента
/reset - сбросить разговор

Или просто напиши сообщение, и я передам его Chief of Staff! ✨
"""
    await update.message.reply_text(welcome_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
📖 Как использовать:

**Обычное общение**
Просто напиши сообщение - я передам его Chief of Staff, который координирует все проекты.

**Команды**
/status - получить статус всех проектов
/agents - список всех агентов
/ask <agent> <message> - напрямую спросить специалиста
/reset - начать разговор заново

**Примеры**
• "Какие задачи на сегодня?"
• "Статус по фильму?"
• /ask lsrc_tech Какой следующий релиз?
• /ask documentary Что осталось смонтировать?
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    user_id = update.effective_user.id
    orchestrator = get_orchestrator(user_id)
    
    await update.message.reply_text("⏳ Собираю статус проектов...")
    
    try:
        status_text = orchestrator.get_all_status()
        await update.message.reply_text(f"📊 Статус проектов:\n\n{status_text}")
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")


async def agents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /agents command"""
    text = "📋 Доступные агенты:\n\n"
    
    for key, info in ASSISTANTS.items():
        role_emoji = "👑" if info["role"] == "coordinator" else "🔧"
        text += f"{role_emoji} {key}\n"
        text += f"   {info['description']}\n\n"
    
    text += "Используй: /ask <agent_key> <сообщение>"
    await update.message.reply_text(text)


async def ask_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ask command - talk directly to a specialist"""
    user_id = update.effective_user.id
    orchestrator = get_orchestrator(user_id)
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Использование: /ask <agent_key> <сообщение>\n"
            "Пример: /ask lsrc_tech Какой статус релиза?"
        )
        return
    
    agent_key = context.args[0]
    message = " ".join(context.args[1:])
    
    if agent_key not in ASSISTANTS:
        await update.message.reply_text(
            f"❌ Неизвестный агент: {agent_key}\n"
            "Используй /agents чтобы увидеть список."
        )
        return
    
    agent_name = ASSISTANTS[agent_key]["name"]
    await update.message.reply_text(f"⏳ Спрашиваю {agent_name}...")
    
    try:
        response = orchestrator.ask_specialist(agent_key, message)
        await update.message.reply_text(f"🤖 {agent_name}:\n\n{response}")
    except Exception as e:
        logger.error(f"Error asking specialist: {e}")
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /reset command"""
    user_id = update.effective_user.id
    
    if user_id in user_orchestrators:
        user_orchestrators[user_id].reset_all_threads()
        del user_orchestrators[user_id]
    
    await update.message.reply_text("🔄 Разговор сброшен! Начинаем с чистого листа.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages - send to Chief of Staff"""
    user_id = update.effective_user.id
    message = update.message.text
    
    orchestrator = get_orchestrator(user_id)
    
    await update.message.reply_text("⏳ Думаю...")
    
    try:
        response = orchestrator.ask(message)
        await update.message.reply_text(f"🤖 {response.agent_name}:\n\n{response.content}")
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")


async def set_commands(application: Application):
    """Set bot commands for the menu"""
    commands = [
        BotCommand("start", "Начать работу"),
        BotCommand("help", "Помощь"),
        BotCommand("status", "Статус всех проектов"),
        BotCommand("agents", "Список агентов"),
        BotCommand("ask", "Спросить конкретного агента"),
        BotCommand("reset", "Сбросить разговор"),
    ]
    await application.bot.set_my_commands(commands)


def main():
    """Start the bot"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not set in environment")
        print("Get a token from @BotFather on Telegram")
        return
    
    # Create application
    application = Application.builder().token(token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("agents", agents))
    application.add_handler(CommandHandler("ask", ask_agent))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Set commands on startup
    application.post_init = set_commands
    
    print("🤖 Bot starting...")
    print("Press Ctrl+C to stop")
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

