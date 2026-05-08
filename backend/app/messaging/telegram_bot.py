import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from app.db.database import SessionLocal
from app.db.models import Workflow
from app.api.workflows import run_workflow_bg
import logging

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am your AI Agent Orchestration bot. Send me a message, and I will route it to the active workflow.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    chat_id = update.effective_chat.id
    
    logger.info(f"Received message from Telegram: {user_message} (chat_id: {chat_id})")
    await update.message.reply_text("Agent is processing your request...")
 
    # Trigger the Customer Support workflow if active, else fallback to first active workflow
    db = SessionLocal()
    try:
        workflow = db.query(Workflow).filter(Workflow.name == "Customer Support Workflow", Workflow.active == True).first()
        if not workflow:
            workflow = db.query(Workflow).filter(Workflow.active == True).first()
        if not workflow:
            logger.warning("No active workflows found for Telegram request.")
            await update.message.reply_text("No active workflows found. Please create and save a workflow first.")
            return
 
        from app.db.models import Execution
        execution = Execution(workflow_id=workflow.id, thread_id=str(chat_id), status="running")
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        logger.info(f"Starting execution {execution.id} for workflow {workflow.id} (thread: {chat_id})")
        
        # Run workflow synchronously for Telegram response
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, run_workflow_bg, workflow.id, execution.id, user_message, str(chat_id))
        
        # After it's done, fetch result
        db.refresh(execution)
        logger.info(f"Execution {execution.id} finished with status: {execution.status}")
        
        if execution.status == "completed" and execution.result and execution.result.get("output"):
            await update.message.reply_text(execution.result["output"])
        elif execution.status == "failed":
            error_msg = execution.result.get("error", "Unknown error")
            await update.message.reply_text(f"Sorry, an error occurred: {error_msg}")
        else:
            await update.message.reply_text("Workflow completed but returned no output. Check your agent configurations.")
            
    except Exception as e:
        logger.error(f"Error handling telegram message: {e}", exc_info=True)
        await update.message.reply_text("Internal error occurred while processing your request.")
    finally:
        db.close()

def start_telegram_bot():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or token == "your_telegram_bot_token_here":
        logger.warning("TELEGRAM_BOT_TOKEN not set properly. Telegram bot will not start.")
        return

    application = ApplicationBuilder().token(token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    logger.info("Starting Telegram bot polling...")
    # Run polling in the current event loop
    application.run_polling()
