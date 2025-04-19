import os
import logging
import asyncio
import requests
from datetime import datetime
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

async def get_weather(city: str) -> dict:
    """Get current weather data for a city."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": f"{city},TR",  # Add TR for Turkey
        "appid": api_key,
        "units": "metric",
        "lang": "tr"
    }
    response = requests.get(base_url, params=params)
    return response.json()

async def get_forecast(city: str) -> dict:
    """Get 5-day weather forecast for a city."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    base_url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {
        "q": f"{city},TR",  # Add TR for Turkey
        "appid": api_key,
        "units": "metric",
        "lang": "tr"
    }
    response = requests.get(base_url, params=params)
    return response.json()

async def hava(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send current weather information for a Turkish city."""
    if not context.args:
        await update.message.reply_text("Lütfen bir şehir adı girin. Örnek: /hava Istanbul")
        return

    city = " ".join(context.args)
    try:
        weather_data = await get_weather(city)
        if weather_data["cod"] != 200:
            await update.message.reply_text("Şehir bulunamadı. Lütfen Türkiye'deki bir şehir adı girin.")
            return

        temp = weather_data["main"]["temp"]
        feels_like = weather_data["main"]["feels_like"]
        temp_min = weather_data["main"]["temp_min"]
        temp_max = weather_data["main"]["temp_max"]
        humidity = weather_data["main"]["humidity"]
        description = weather_data["weather"][0]["description"].capitalize()
        
        message = (
            f"🌤️ {city} için anlık hava durumu:\n\n"
            f"🌡️ Sıcaklık: {temp}°C\n"
            f"🤔 Hissedilen: {feels_like}°C\n"
            f"⬆️ En yüksek: {temp_max}°C\n"
            f"⬇️ En düşük: {temp_min}°C\n"
            f"💧 Nem: {humidity}%\n"
            f"📝 Durum: {description}"
        )
        
        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Weather error: {e}")
        await update.message.reply_text("Hava durumu bilgisi alınırken bir hata oluştu.")

async def tahmin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send 5-day weather forecast for a Turkish city."""
    if not context.args:
        await update.message.reply_text("Lütfen bir şehir adı girin. Örnek: /tahmin Istanbul")
        return

    city = " ".join(context.args)
    try:
        forecast_data = await get_forecast(city)
        if forecast_data["cod"] != "200":
            await update.message.reply_text("Şehir bulunamadı. Lütfen Türkiye'deki bir şehir adı girin.")
            return

        message = f"🌤️ {city} için 5 günlük hava tahmini:\n\n"
        
        # Group forecasts by day
        daily_forecasts = {}
        for item in forecast_data["list"]:
            date = datetime.fromtimestamp(item["dt"]).strftime("%d.%m.%Y")
            if date not in daily_forecasts:
                daily_forecasts[date] = {
                    "temp_min": float('inf'),
                    "temp_max": float('-inf'),
                    "description": item["weather"][0]["description"]
                }
            
            temp = item["main"]["temp"]
            daily_forecasts[date]["temp_min"] = min(daily_forecasts[date]["temp_min"], temp)
            daily_forecasts[date]["temp_max"] = max(daily_forecasts[date]["temp_max"], temp)

        for date, data in daily_forecasts.items():
            message += (
                f"📅 {date}:\n"
                f"⬆️ En yüksek: {data['temp_max']}°C\n"
                f"⬇️ En düşük: {data['temp_min']}°C\n"
                f"📝 Durum: {data['description'].capitalize()}\n\n"
            )
        
        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Forecast error: {e}")
        await update.message.reply_text("Hava tahmini alınırken bir hata oluştu.")

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
    application.add_handler(CommandHandler("hava", hava))
    application.add_handler(CommandHandler("tahmin", tahmin))
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