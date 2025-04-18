import logging
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler
import asyncio

# Logging
logging.basicConfig(level=logging.INFO)

# Flask uygulaması
app = Flask(__name__)

# Telegram bot ayarları
TOKEN = '8010269348:AAHz7SpGXCgXDaY4e46KFHgWJQDePInQAkI'  # ← kendi tokenını buraya koy

# Telegram bot uygulamasını oluştur
application = Application.builder().token(TOKEN).build()

# /start komutu
async def start(update: Update, context):
    await update.message.reply_text("Merhaba! Bot çalışıyor 🎉")

# Komut handler ekle
application.add_handler(CommandHandler("start", start))

# Webhook endpoint
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        # asyncio.create_task kullanarak asenkron olarak işlem yapıyoruz
        asyncio.create_task(application.process_update(update))
        return 'OK'
    except Exception as e:
        logging.error(f"Webhook işleme hatası: {e}")
        return 'Error', 500

# Test için root endpoint
@app.route('/')
def index():
    return "Bot çalışıyor! ✅"

# Uygulama başlatıldığında webhook ayarla
if __name__ == '__main__':
    # Bot instance'ını oluştur
    bot = Bot(token=TOKEN)
    # Webhook URL'ini ayarla
    webhook_url = "https://telegrambot-gp4i.onrender.com/webhook"  # kendi Render URL'ine göre değiştir
    # Webhook'u ayarla
    asyncio.run(bot.set_webhook(webhook_url))
    logging.info("Webhook ayarlandı: " + webhook_url)

    # Flask uygulamasını başlat
    app.run(host='0.0.0.0', port=10000)
