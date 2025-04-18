import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from flask import Flask, request

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
async def webhook():
    """Handle incoming webhook updates."""
    if request.method == "POST":
        await application.update_queue.put(Update.de_json(request.get_json(force=True), application.bot))
        return "OK"

def main() -> None:
    """Start the bot."""
    global application
    
    # Get environment variables
    token = BOT_TOKEN  # Use the hardcoded token
    port = int(os.getenv("PORT", 3000))
    
    if not token:
        logger.error("No bot token provided!")
        return

    # Create the Application
    application = Application.builder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Start Flask app
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    main() 
