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
import pandas as pd

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

# Cache for stock data
stock_cache = {}
CACHE_DURATION = 300  # 5 minutes

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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages."""
    text = update.message.text.lower().strip()
    
    if text.startswith("hava "):
        # Remove "hava " prefix and process as weather command
        city = text[5:].strip()
        await hava(update, context, city)
    elif text.startswith("tahmin "):
        # Remove "tahmin " prefix and process as forecast command
        city = text[7:].strip()
        await tahmin(update, context, city)
    elif text.startswith("hisse "):
        # Process stock command
        symbol = text[6:].strip().upper()
        await hisse(update, context, symbol)
    else:
        # Echo other messages
        await echo(update, context)

async def hava(update: Update, context: ContextTypes.DEFAULT_TYPE, city: str = None) -> None:
    """Send current weather information for a Turkish city."""
    if not city and context.args:
        city = " ".join(context.args)
    
    if not city:
        await update.message.reply_text("Lütfen bir şehir adı girin. Örnek: hava Istanbul")
        return

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

async def tahmin(update: Update, context: ContextTypes.DEFAULT_TYPE, city: str = None) -> None:
    """Send 5-day weather forecast for a Turkish city."""
    if not city and context.args:
        city = " ".join(context.args)
    
    if not city:
        await update.message.reply_text("Lütfen bir şehir adı girin. Örnek: tahmin Istanbul")
        return

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
                    "temps": [],
                    "descriptions": set()
                }
            
            temp = item["main"]["temp"]
            daily_forecasts[date]["temps"].append(temp)
            daily_forecasts[date]["descriptions"].add(item["weather"][0]["description"])

        for date, data in daily_forecasts.items():
            # Calculate average temperature
            avg_temp = sum(data["temps"]) / len(data["temps"])
            # Get most common weather description
            main_description = max(data["descriptions"], key=data["descriptions"].count)
            
            message += (
                f"📅 {date}:\n"
                f"🌡️ Ortalama Sıcaklık: {avg_temp:.1f}°C\n"
                f"📝 Durum: {main_description.capitalize()}\n\n"
            )
        
        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Forecast error: {e}")
        await update.message.reply_text("Hava tahmini alınırken bir hata oluştu.")

async def get_bist_data(symbol: str) -> dict:
    """Get BIST stock data with caching and rate limiting."""
    current_time = time.time()
    
    # Check cache first
    if symbol in stock_cache:
        cached_data, cache_time = stock_cache[symbol]
        if current_time - cache_time < CACHE_DURATION:
            return cached_data
    
    try:
        # BIST API endpoints
        base_url = "https://www.borsaistanbul.com/api"
        
        # Get current price
        price_url = f"{base_url}/marketdata/equity/{symbol}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        price_response = requests.get(price_url, headers=headers)
        if price_response.status_code != 200:
            raise ValueError(f"Price API returned status code {price_response.status_code}")
            
        price_data = price_response.json()
        if not price_data or 'data' not in price_data:
            raise ValueError("No price data received")
            
        # Get historical data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)  # Get 60 days of data for better averages
        
        hist_url = f"{base_url}/marketdata/equity/{symbol}/historical"
        params = {
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d")
        }
        
        hist_response = requests.get(hist_url, headers=headers, params=params)
        if hist_response.status_code != 200:
            raise ValueError(f"Historical API returned status code {hist_response.status_code}")
            
        hist_data = hist_response.json()
        if not hist_data or 'data' not in hist_data:
            raise ValueError("No historical data received")
            
        # Process current data
        current_price = float(price_data['data']['last'])
        previous_close = float(price_data['data']['previousClose'])
        change_percent = float(price_data['data']['changePercent'])
        
        # Process historical data
        df = pd.DataFrame(hist_data['data'])
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Calculate moving averages
        sma_20 = df['close'].rolling(window=20).mean().iloc[-1]
        sma_50 = df['close'].rolling(window=50).mean().iloc[-1]
        
        data = {
            'current_price': current_price,
            'previous_close': previous_close,
            'change_percent': change_percent,
            'sma_20': sma_20,
            'sma_50': sma_50
        }
        
        # Update cache
        stock_cache[symbol] = (data, current_time)
        return data
        
    except Exception as e:
        logger.error(f"Error fetching stock data for {symbol}: {e}")
        return None

async def hisse(update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str = None) -> None:
    """Get stock information for BIST symbols."""
    if not symbol and context.args:
        symbol = context.args[0].upper()
    
    if not symbol:
        await update.message.reply_text("Lütfen bir hisse senedi sembolü girin. Örnek: hisse GARAN")
        return

    try:
        # Get stock data
        stock_data = await get_bist_data(symbol)
        
        if not stock_data:
            await update.message.reply_text(
                "Hisse senedi verileri şu anda alınamıyor. Lütfen birkaç dakika sonra tekrar deneyin."
            )
            return
            
        current_price = stock_data['current_price']
        previous_close = stock_data['previous_close']
        change_percent = stock_data['change_percent']
        sma_20 = stock_data['sma_20']
        sma_50 = stock_data['sma_50']
        
        # Generate analysis
        analysis = []
        if current_price > sma_20 and current_price > sma_50:
            analysis.append("📈 Kısa ve orta vadeli trend yukarı yönlü")
        elif current_price < sma_20 and current_price < sma_50:
            analysis.append("📉 Kısa ve orta vadeli trend aşağı yönlü")
        else:
            analysis.append("↔️ Trend belirsiz")
            
        if change_percent > 0:
            analysis.append(f"🟢 Günlük kazanç: %{change_percent:.2f}")
        else:
            analysis.append(f"🔴 Günlük kayıp: %{abs(change_percent):.2f}")
            
        message = (
            f"📊 {symbol} Hisse Bilgileri:\n\n"
            f"💰 Fiyat: {current_price:.2f} TL\n"
            f"📈 Kapanış: {previous_close:.2f} TL\n"
            f"📊 20 Günlük Ortalama: {sma_20:.2f} TL\n"
            f"📊 50 Günlük Ortalama: {sma_50:.2f} TL\n\n"
            f"📝 Analiz:\n" + "\n".join(analysis)
        )
        
        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Stock error: {e}")
        await update.message.reply_text(
            "Hisse senedi bilgisi alınırken bir hata oluştu. Lütfen daha sonra tekrar deneyin."
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
    application.add_handler(CommandHandler("help", help_command))
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