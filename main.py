import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler
from requests.adapters import HTTPAdapter
from urllib3 import PoolManager

# Flask uygulaması
app = Flask(__name__)

# Telegram bot ayarları
TOKEN = 'YOUR_BOT_TOKEN'  # Telegram bot tokenınızı buraya ekleyin

# Telegram bot için özel bağlantı havuzu sınıfı
class CustomAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        self.pool_connections = 10  # Bağlantı sayısını artır
        self.pool_maxsize = 10      # Maksimum bağlantı sayısını artır
        super().__init__(*args, **kwargs)

# Telegram bot uygulaması ve session için adapter ayarı
application = Application.builder().token(TOKEN).build()
application.bot.session.mount('https://', CustomAdapter())
application.bot.session.mount('http://', CustomAdapter())

# Webhook'u ayarlama
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        json_str = request.get_data().decode('UTF-8')
        update = Update.de_json(json_str, application.bot)
        application.process_update(update)
        return 'OK'
    except Exception as e:
        logging.error(f"Webhook işleme hatası: {e}")
        return 'Error', 500

# Basit bir komut örneği
async def start(update: Update, context):
    await update.message.reply_text("Merhaba! Benim botum!")

# Komut handler'ını oluştur
start_handler = CommandHandler('start', start)
application.add_handler(start_handler)

# Uygulama başlatma
if __name__ == '__main__':
    # Webhook için URL'yi Telegram API'ye ayarlıyoruz
    application.bot.set_webhook("https://yourdomain.com/webhook")  # Webhook URL'sini kendi domain adresinizle değiştirin
    logging.info("Webhook ayarlandı ve bot çalışıyor!")
    app.run(host='0.0.0.0', port=10000)
