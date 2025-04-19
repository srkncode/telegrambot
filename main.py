import os
import logging
import asyncio
import requests
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from flask import Flask, request
import nest_asyncio
import json

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

# Cache for data
data_cache = {}
CACHE_DURATION = 300  # 5 minutes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Merhaba {user.mention_html()}! Ben bir Telegram botuyum.\n\n"
        "Kullanabileceğiniz komutlar:\n"
        "💰 /doviz - Döviz kurları\n"
        "🥇 /altin - Altın fiyatları\n"
        "🌤️ /hava [şehir] - Hava durumu\n"
        "❓ /yardim - Yardım menüsü"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "Kullanabileceğiniz komutlar:\n\n"
        "💰 /doviz - Döviz kurları\n"
        "🥇 /altin - Altın fiyatları\n"
        "🌤️ /hava [şehir] - Hava durumu\n"
        "❓ /yardim - Yardım menüsü"
    )

async def get_currency_data() -> dict:
    """Get currency data from TCMB."""
    current_time = time.time()
    
    # Check cache first
    if 'currency' in data_cache:
        cached_data, cache_time = data_cache['currency']
        if current_time - cache_time < CACHE_DURATION:
            return cached_data
    
    try:
        # TCMB API
        url = "https://www.tcmb.gov.tr/kurlar/today.xml"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            raise ValueError("Döviz kurları alınamadı")
        
        # Parse XML response
        from xml.etree import ElementTree
        root = ElementTree.fromstring(response.content)
        
        data = {
            'USD': {
                'name': 'Amerikan Doları',
                'buying': float(root.find(".//Currency[@Kod='USD']/BanknoteBuying").text),
                'selling': float(root.find(".//Currency[@Kod='USD']/BanknoteSelling").text)
            },
            'EUR': {
                'name': 'Euro',
                'buying': float(root.find(".//Currency[@Kod='EUR']/BanknoteBuying").text),
                'selling': float(root.find(".//Currency[@Kod='EUR']/BanknoteSelling").text)
            },
            'GBP': {
                'name': 'İngiliz Sterlini',
                'buying': float(root.find(".//Currency[@Kod='GBP']/BanknoteBuying").text),
                'selling': float(root.find(".//Currency[@Kod='GBP']/BanknoteSelling").text)
            }
        }
        
        # Update cache
        data_cache['currency'] = (data, current_time)
        return data
        
    except Exception as e:
        logger.error(f"Error fetching currency data: {e}")
        return None

async def get_gold_data() -> dict:
    """Get gold prices from TCMB."""
    current_time = time.time()
    
    # Check cache first
    if 'gold' in data_cache:
        cached_data, cache_time = data_cache['gold']
        if current_time - cache_time < CACHE_DURATION:
            return cached_data
    
    try:
        # TCMB API
        url = "https://www.tcmb.gov.tr/kurlar/today.xml"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            raise ValueError("Altın fiyatları alınamadı")
        
        # Parse XML response
        from xml.etree import ElementTree
        root = ElementTree.fromstring(response.content)
        
        # Get USD rate for gram gold calculation
        usd_buying = float(root.find(".//Currency[@Kod='USD']/BanknoteBuying").text)
        
        # Calculate gram gold price (1 gram = 31.1035 grams)
        gram_gold_usd = 31.1035  # 1 troy ounce in grams
        gram_gold_try = gram_gold_usd * usd_buying
        
        data = {
            'gram': {
                'name': 'Gram Altın',
                'buying': gram_gold_try,
                'selling': gram_gold_try * 1.01  # Add 1% spread
            },
            'ceyrek': {
                'name': 'Çeyrek Altın',
                'buying': gram_gold_try * 1.75,  # 1.75 grams
                'selling': gram_gold_try * 1.75 * 1.01
            },
            'yarim': {
                'name': 'Yarım Altın',
                'buying': gram_gold_try * 3.5,  # 3.5 grams
                'selling': gram_gold_try * 3.5 * 1.01
            },
            'tam': {
                'name': 'Tam Altın',
                'buying': gram_gold_try * 7,  # 7 grams
                'selling': gram_gold_try * 7 * 1.01
            }
        }
        
        # Update cache
        data_cache['gold'] = (data, current_time)
        return data
        
    except Exception as e:
        logger.error(f"Error fetching gold data: {e}")
        return None

async def get_weather(city: str) -> dict:
    """Get current weather data for a city."""
    current_time = time.time()
    cache_key = f'weather_{city}'
    
    # Check cache first
    if cache_key in data_cache:
        cached_data, cache_time = data_cache[cache_key]
        if current_time - cache_time < CACHE_DURATION:
            return cached_data
    
    try:
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            raise ValueError("OpenWeather API anahtarı bulunamadı")
            
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": f"{city},TR",  # Add TR for Turkey
            "appid": api_key,
            "units": "metric",
            "lang": "tr"
        }
        
        response = requests.get(base_url, params=params, timeout=10)
        
        if response.status_code != 200:
            error_data = response.json()
            if error_data.get('cod') == '404':
                raise ValueError(f"Şehir bulunamadı: {city}")
            else:
                raise ValueError(f"Hava durumu bilgisi alınamadı: {error_data.get('message', 'Bilinmeyen hata')}")
        
        data = response.json()
        
        # Update cache
        data_cache[cache_key] = (data, current_time)
        return data
        
    except Exception as e:
        logger.error(f"Error fetching weather data: {e}")
        return None

async def doviz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send currency information."""
    try:
        currency_data = await get_currency_data()
        
        if not currency_data:
            await update.message.reply_text(
                "Döviz kurları şu anda alınamıyor. Lütfen birkaç dakika sonra tekrar deneyin."
            )
            return
            
        message = "💰 Güncel Döviz Kurları:\n\n"
        
        for code, data in currency_data.items():
            message += (
                f"{data['name']} ({code}):\n"
                f"Alış: {data['buying']:.4f} TL\n"
                f"Satış: {data['selling']:.4f} TL\n\n"
            )
        
        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Currency error: {e}")
        await update.message.reply_text(
            "Döviz kurları alınırken bir hata oluştu. Lütfen daha sonra tekrar deneyin."
        )

async def altin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send gold prices."""
    try:
        gold_data = await get_gold_data()
        
        if not gold_data:
            await update.message.reply_text(
                "Altın fiyatları şu anda alınamıyor. Lütfen birkaç dakika sonra tekrar deneyin."
            )
            return
            
        message = "🥇 Güncel Altın Fiyatları:\n\n"
        
        for code, data in gold_data.items():
            message += (
                f"{data['name']}:\n"
                f"Alış: {data['buying']:.2f} TL\n"
                f"Satış: {data['selling']:.2f} TL\n\n"
            )
        
        message += "ℹ️ Not: Fiyatlar yaklaşık değerlerdir ve güncel piyasa koşullarına göre değişebilir."
        
        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Gold error: {e}")
        await update.message.reply_text(
            "Altın fiyatları alınırken bir hata oluştu. Lütfen daha sonra tekrar deneyin."
        )

async def hava(update: Update, context: ContextTypes.DEFAULT_TYPE, city: str = None) -> None:
    """Send current weather information for a Turkish city."""
    if not city and context.args:
        city = " ".join(context.args)
    
    if not city:
        await update.message.reply_text("Lütfen bir şehir adı girin. Örnek: /hava Istanbul")
        return

    try:
        weather_data = await get_weather(city)
        
        if not weather_data:
            await update.message.reply_text(
                "Hava durumu bilgisi şu anda alınamıyor. Lütfen birkaç dakika sonra tekrar deneyin."
            )
            return
            
        temp = weather_data["main"]["temp"]
        feels_like = weather_data["main"]["feels_like"]
        temp_min = weather_data["main"]["temp_min"]
        temp_max = weather_data["main"]["temp_max"]
        humidity = weather_data["main"]["humidity"]
        description = weather_data["weather"][0]["description"].capitalize()
        wind_speed = weather_data["wind"]["speed"]
        
        message = (
            f"🌤️ {city} için anlık hava durumu:\n\n"
            f"🌡️ Sıcaklık: {temp}°C\n"
            f"🤔 Hissedilen: {feels_like}°C\n"
            f"⬆️ En yüksek: {temp_max}°C\n"
            f"⬇️ En düşük: {temp_min}°C\n"
            f"💧 Nem: {humidity}%\n"
            f"💨 Rüzgar: {wind_speed} m/s\n"
            f"📝 Durum: {description}"
        )
        
        await update.message.reply_text(message)
    except ValueError as e:
        await update.message.reply_text(str(e))
    except Exception as e:
        logger.error(f"Weather error: {e}")
        await update.message.reply_text(
            "Hava durumu bilgisi alınırken bir hata oluştu. Lütfen daha sonra tekrar deneyin."
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages."""
    text = update.message.text.lower().strip()
    
    if text.startswith("doviz"):
        await doviz(update, context)
    elif text.startswith("altin"):
        await altin(update, context)
    elif text.startswith("hava"):
        # Remove "hava " prefix and process as weather command
        city = text[5:].strip()
        await hava(update, context, city)
    else:
        # Echo other messages
        await update.message.reply_text(
            "Kullanabileceğiniz komutlar:\n\n"
            "💰 doviz - Döviz kurları\n"
            "🥇 altin - Altın fiyatları\n"
            "🌤️ hava [şehir] - Hava durumu\n"
            "❓ yardim - Yardım menüsü"
        )

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
    application.add_handler(CommandHandler("yardim", help_command))
    application.add_handler(CommandHandler("doviz", doviz))
    application.add_handler(CommandHandler("altin", altin))
    application.add_handler(CommandHandler("hava", hava))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

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