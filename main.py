import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from flask import Flask, request
from functools import partial

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# Global variable for the bot application
application = None

# Bot Token
BOT_TOKEN = "8010269348:AAHz7SpGXCgXDaY4e46KFHgWJQDePInQAkI"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Merhaba {user.mention_html()}! Ben bir Telegram botuyum."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Yardım için buradayım!")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    await update.message.reply_text(update.message.text)

@app.route("/", methods=["GET"])
def index():
    return "Bot çalışıyor!"

@app.route("/webhook", methods=["POST"])
def webhook():
    """Handle incoming webhook updates."""
    if request.method == "POST":
        # Get the update data
        update = Update.de_json(request.get_json(force=True), application.bot)
        
        # Create an async function to process the update
        async def process_update():
            await application.process_update(update)
        
        # Run the async function
        asyncio.run(process_update())
        return "OK"
    return "Webhook endpoint"

async def init_webhook(app_instance: Application, webhook_url: str) -> None:
    """Initialize webhook settings."""
    await app_instance.bot.set_webhook(webhook_url + "/webhook")
    logger.info(f"Webhook set to {webhook_url}/webhook")

async def setup_application():
    """Setup the bot application."""
    global application
    
    # Get environment variables
    token = BOT_TOKEN
    
    if not token:
        logger.error("No bot token provided!")
        return None

    # Create the Application
    application = Application.builder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Set webhook if RENDER_EXTERNAL_URL is provided
    webhook_url = os.getenv("RENDER_EXTERNAL_URL")
    if webhook_url:
        await init_webhook(application, webhook_url)
    
    return application

def main() -> None:
    """Start the bot."""
    # Setup the application
    asyncio.run(setup_application())
    
    # Get port
    port = int(os.getenv("PORT", 10000))
    
    # Start Flask app
    logger.info(f"Starting Flask app on port {port}")
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    main() 