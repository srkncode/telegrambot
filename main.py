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
import json
from bs4 import BeautifulSoup
import http.client

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

# BIST symbol mappings for TradingView
BIST_SYMBOL_MAPPINGS = {
    'HEKTS': 'BIST:HEKTS',  # Halk Enerji
    'SASA': 'BIST:SASA',    # Sasa
    'KCHOL': 'BIST:KCHOL',  # Koç Holding
    'GARAN': 'BIST:GARAN',  # Garanti Bankası
    'AKBNK': 'BIST:AKBNK',  # Akbank
    'ISCTR': 'BIST:ISCTR',  # İş Bankası
    'THYAO': 'BIST:THYAO',  # Türk Hava Yolları
    'EREGL': 'BIST:EREGL',  # Ereğli Demir Çelik
    'TUPRS': 'BIST:TUPRS',  # Tüpraş
    'ASELS': 'BIST:ASELS',  # Aselsan
    'KRDMD': 'BIST:KRDMD',  # Kardemir
    'PETKM': 'BIST:PETKM',  # Petkim
    'TCELL': 'BIST:TCELL',  # Turkcell
    'VESTL': 'BIST:VESTL',  # Vestel
    'BIMAS': 'BIST:BIMAS',  # BİM
    'MGROS': 'BIST:MGROS',  # Migros
    'ARCLK': 'BIST:ARCLK',  # Arçelik
    'FROTO': 'BIST:FROTO',  # Ford Otosan
    'ULKER': 'BIST:ULKER',  # Ülker
    'PGSUS': 'BIST:PGSUS',  # Pegasus
}

# Cryptocurrency mappings
CRYPTO_MAPPINGS = {
    'BTC': 'BINANCE:BTCUSDT',  # Bitcoin
    'ETH': 'BINANCE:ETHUSDT',  # Ethereum
    'XRP': 'BINANCE:XRPUSDT',  # Ripple
    'ADA': 'BINANCE:ADAUSDT',  # Cardano
    'DOGE': 'BINANCE:DOGEUSDT',  # Dogecoin
    'SOL': 'BINANCE:SOLUSDT',  # Solana
    'DOT': 'BINANCE:DOTUSDT',  # Polkadot
    'AVAX': 'BINANCE:AVAXUSDT',  # Avalanche
    'MATIC': 'BINANCE:MATICUSDT',  # Polygon
    'LINK': 'BINANCE:LINKUSDT',  # Chainlink
}

def validate_symbol(symbol: str) -> str:
    """Validate and format symbol for both BIST and cryptocurrency."""
    symbol = symbol.upper().strip()
    
    # Check if symbol is in BIST mappings
    if symbol in BIST_SYMBOL_MAPPINGS:
        return BIST_SYMBOL_MAPPINGS[symbol]
    
    # Check if symbol is in crypto mappings
    if symbol in CRYPTO_MAPPINGS:
        return CRYPTO_MAPPINGS[symbol]
    
    # Basic validation for BIST symbols
    if not symbol.isalpha():
        raise ValueError("Hisse senedi sembolü sadece harflerden oluşmalıdır.")
    
    if len(symbol) < 3 or len(symbol) > 5:
        raise ValueError("Hisse senedi sembolü 3-5 karakter uzunluğunda olmalıdır.")
    
    raise ValueError(f"Hisse senedi bulunamadı: {symbol}")

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

async def get_stock_data(symbol: str) -> dict:
    """Get stock data with caching and rate limiting."""
    current_time = time.time()
    
    # Check cache first
    if symbol in stock_cache:
        cached_data, cache_time = stock_cache[symbol]
        if current_time - cache_time < CACHE_DURATION:
            return cached_data
    
    try:
        # Validate and format symbol
        formatted_symbol = validate_symbol(symbol)
        
        # TradingView configuration
        base_url = "https://www.tradingview.com"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        
        # Add retry mechanism
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                # Get current price
                url = f"{base_url}/symbols/{formatted_symbol}/"
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    break
                elif response.status_code == 429:  # Too Many Requests
                    retry_after = int(response.headers.get('Retry-After', retry_delay))
                    time.sleep(retry_after)
                    continue
                else:
                    raise ValueError(f"API yanıt kodu: {response.status_code}")
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                continue
        
        # Parse HTML response
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get current price
        price_element = soup.find('div', {'class': 'tv-symbol-price-quote__value'})
        if not price_element:
            # Try alternative class for crypto
            price_element = soup.find('div', {'class': 'tv-symbol-price-quote__value js-symbol-last'})
            if not price_element:
                raise ValueError("Fiyat bilgisi bulunamadı")
        current_price = float(price_element.text.strip().replace(',', ''))
        
        # Get previous close
        prev_close_element = soup.find('div', {'class': 'tv-symbol-price-quote__previous-close'})
        if not prev_close_element:
            # Try alternative class for crypto
            prev_close_element = soup.find('div', {'class': 'tv-symbol-price-quote__previous-close js-symbol-prev-close'})
            if not prev_close_element:
                raise ValueError("Önceki kapanış fiyatı bulunamadı")
        previous_close = float(prev_close_element.text.strip().replace(',', ''))
        
        # Calculate change percent
        change_percent = ((current_price - previous_close) / previous_close) * 100
        
        # Get historical data
        hist_url = f"{base_url}/symbols/{formatted_symbol}/historical-data/"
        hist_response = requests.get(hist_url, headers=headers, timeout=10)
        
        if hist_response.status_code != 200:
            raise ValueError(f"Geçmiş veri API yanıt kodu: {hist_response.status_code}")
            
        # Parse historical data
        hist_soup = BeautifulSoup(hist_response.text, 'html.parser')
        table = hist_soup.find('table', {'class': 'tv-data-table'})
        
        if not table:
            raise ValueError("Geçmiş veri tablosu bulunamadı")
            
        # Extract historical data
        dates = []
        closes = []
        
        rows = table.find_all('tr')[1:61]  # Get last 60 days
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                try:
                    date_str = cols[0].text.strip()
                    date = datetime.strptime(date_str, '%b %d, %Y')
                    close = float(cols[1].text.strip().replace(',', ''))
                    dates.append(date)
                    closes.append(close)
                except (ValueError, IndexError):
                    continue
        
        if not dates or not closes:
            raise ValueError("Geçmiş veri bulunamadı")
            
        # Create DataFrame
        df = pd.DataFrame({'date': dates, 'close': closes})
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
        
    except ValueError as e:
        logger.error(f"Validation error for {symbol}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error fetching stock data for {symbol}: {e}")
        return None

async def hisse(update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str = None) -> None:
    """Get stock information for BIST symbols and cryptocurrencies."""
    if not symbol and context.args:
        symbol = context.args[0].upper()
    
    if not symbol:
        await update.message.reply_text("Lütfen bir hisse senedi veya kripto para sembolü girin. Örnek: hisse GARAN veya hisse BTC")
        return

    try:
        # Get stock data
        stock_data = await get_stock_data(symbol)
        
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
            f"📊 {symbol} Bilgileri:\n\n"
            f"💰 Fiyat: {current_price:.2f} {'TL' if symbol in BIST_SYMBOL_MAPPINGS else 'USDT'}\n"
            f"📈 Kapanış: {previous_close:.2f} {'TL' if symbol in BIST_SYMBOL_MAPPINGS else 'USDT'}\n"
            f"📊 20 Günlük Ortalama: {sma_20:.2f} {'TL' if symbol in BIST_SYMBOL_MAPPINGS else 'USDT'}\n"
            f"📊 50 Günlük Ortalama: {sma_50:.2f} {'TL' if symbol in BIST_SYMBOL_MAPPINGS else 'USDT'}\n\n"
            f"📝 Analiz:\n" + "\n".join(analysis)
        )
        
        await update.message.reply_text(message)
    except ValueError as e:
        await update.message.reply_text(str(e))
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