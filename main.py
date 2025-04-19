import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from flask import Flask, request
import nest_asyncio

# Enable nested asyncio support
nest_asyncio.apply()

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# Bot Token from environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")

# Create event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Create the Application
application = Application.builder().token(BOT_TOKEN).build()

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
        update = Update.de_json(request.get_json(force=True), application.bot)
        
        async def process_update():
            await application.initialize()
            await application.process_update(update)
        
        loop.run_until_complete(process_update())
        return "OK"
    return "Webhook endpoint"

async def init_webhook(url: str) -> None:
    """Initialize webhook settings."""
    await application.bot.set_webhook(url + "/webhook")
    logger.info(f"Webhook set to {url}/webhook")

async def setup():
    """Setup the bot application."""
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Set webhook if RENDER_EXTERNAL_URL is provided
    webhook_url = os.getenv("RENDER_EXTERNAL_URL")
    if webhook_url:
        await init_webhook(webhook_url)
    
    await application.initialize()
    logger.info("Bot application initialized successfully")

def main() -> None:
    """Start the bot."""
    try:
        # Setup the application
        loop.run_until_complete(setup())
        
        # Get port
        port = int(os.getenv("PORT", 10000))
        
        # Start Flask app
        logger.info(f"Starting Flask app on port {port}")
        app.run(host="0.0.0.0", port=port)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise

if __name__ == "__main__":
    main() 