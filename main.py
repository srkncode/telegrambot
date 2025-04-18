import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from requests.adapters import HTTPAdapter

# Logging
logging.basicConfig(level=logging.INFO)

# Flask uygulaması
app = Flask(__name__)

# Telegram bot ayarları
TOKEN = '8010269348:AAHz7SpGXCgXDaY4e46KFHgWJQDePInQAkI'

# Telegram bot için özel bağlantı havuzu sınıfı
class CustomAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        self.pool_connections = 10
        self.pool_maxsize = 10
        super().__init__(*args, **kwargs)

# Telegram uygulaması oluştur
application = Application.builder().token(TOKEN).build()
application.bot.session.mount('https://', CustomAdapter())
application.bot.session.mount('http://', CustomAdapter())

# Komut işleyici
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Merhaba! Bot başarıyla çalışıyor 🚀")

application.add_handler(CommandHandler('start', start))

# Webhook endpoint
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        json_str = request.get_data().decode('utf-8')
        update = Update.de_json(json_str, application.bot)
        application.process_update(update)
        return 'OK'
    except Exception as e:
        logging.error(f"Webhook işleme hatası: {e}")
        return 'Error', 500

# Uygulama başlangıcı
if __name__ == '__main__':
    application.bot.set_webhook("https://telegrambot-gp4i.onrender.com/webhook")
    logging.info("Webhook ayarlandı ✅")
    app.run(host='0.0.0.0', port=10000)
