import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Logging ayarları
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

TOKEN = '8010269348:AAHz7SpGXCgXDaY4e46KFHgWJQDePInQAkI'
WEBHOOK_URL = 'https://telegrambot-gp4i.onrender.com/webhook'

application = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Merhaba! Bot başarıyla çalışıyor 🚀")

application.add_handler(CommandHandler('start', start))

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

# 🔧 Webhook'u manuel olarak kurmak için
@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    success = application.bot.set_webhook(WEBHOOK_URL)
    if success:
        return f"✅ Webhook başarıyla ayarlandı: {WEBHOOK_URL}"
    else:
        return "❌ Webhook ayarlanamadı"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
