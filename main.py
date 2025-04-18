import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Logging ayarları
logging.basicConfig(level=logging.INFO)

# Flask app
app = Flask(__name__)

# Telegram token
TOKEN = '8010269348:AAHz7SpGXCgXDaY4e46KFHgWJQDePInQAkI'

# Telegram bot uygulaması
application = Application.builder().token(TOKEN).build()

# /start komutu
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

# Başlangıç
if __name__ == '__main__':
    application.bot.set_webhook("https://telegrambot-gp4i.onrender.com/webhook")
    logging.info("Webhook ayarlandı ✅")
    app.run(host='0.0.0.0', port=10000)
