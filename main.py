import logging
import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from requests.adapters import HTTPAdapter
from urllib3 import PoolManager

# Flask uygulaması
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Ortam değişkenlerinden token'ı al (Render için)
TOKEN = os.getenv('BOT_TOKEN')  # Render'da BOT_TOKEN olarak ayarlanmalı

# Telegram bot için özel bağlantı havuzu sınıfı
class CustomAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        self.pool_connections = 10
        self.pool_maxsize = 10
        super().__init__(*args, **kwargs)

# Telegram bot uygulaması ve session için adapter ayarı
application = Application.builder().token(TOKEN).build()
application.bot.session.mount('https://', CustomAdapter())
application.bot.session.mount('http://', CustomAdapter())

# Webhook endpoint
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        json_str = request.get_data().decode('utf-8')
        update = Update.de_json(json_str, application.bot)
        application.create_task(application.process_update(update))
        return 'OK'
    except Exception as e:
        logging.error(f"Webhook işleme hatası: {e}")
        return 'Error', 500

# /start komutu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Merhaba! Benim botum!")

# Komut handler
application.add_handler(CommandHandler("start", start))

# Ana uygulama
if __name__ == '__main__':
    # Webhook adresini dinamik olarak al (Render dışarıdan erişebilsin)
    RENDER_EXTERNAL_URL = os.getenv('RENDER_EXTERNAL_URL')  # Render'da tanımlanmalı
    if not RENDER_EXTERNAL_URL:
        raise Exception("RENDER_EXTERNAL_URL ortam değişkeni tanımlı değil!")

    # Webhook'u ayarla
    webhook_url = f"https://{RENDER_EXTERNAL_URL}/webhook"
    application.bot.set_webhook(url=webhook_url)
    logging.info(f"Webhook ayarlandı: {webhook_url}")

    # Flask servisini başlat
    app.run(host="0.0.0.0", port=10000)
