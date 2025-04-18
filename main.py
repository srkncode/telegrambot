import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, Dispatcher
import os

# Bot Token ve Webhook URL'yi environment'dan al
TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Botu başlat
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Webhook'ı sil ve yeniden kur
def setup_webhook():
    bot = updater.bot
    # Önceki webhook'ı sil
    bot.delete_webhook()
    # Yeni webhook'ı kur
    set_result = bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    print("Webhook ayarlandı:", set_result)

# Komutları tanımla
def start(update: Update, context):
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id, text="Merhaba! Bot çalışıyor!")

# Main fonksiyon
def main():
    # Webhook'u ayarla
    setup_webhook()

    # Komutları işleme
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    # Webhook endpointini başlat
    updater.start_webhook(listen="0.0.0.0", port=10000, url_path='webhook')
    updater.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")

if __name__ == "__main__":
    main()
