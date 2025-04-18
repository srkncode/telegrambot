import logging
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler
from telegram.ext import Dispatcher
import os

# Bot Token ve Webhook URL'yi environment'dan al
TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Botu başlat
bot = Bot(TOKEN)

# Webhook'ı sil ve yeniden kur
def setup_webhook():
    # Önceki webhook'ı sil
    bot.delete_webhook()
    # Yeni webhook'ı kur
    set_result = bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    print("Webhook ayarlandı:", set_result)

# Komutları tanımla
async def start(update: Update, context):
    chat_id = update.message.chat_id
    await update.message.reply_text("Merhaba! Bot çalışıyor!")

# Main fonksiyon
async def main():
    # Botu ayarlıyoruz
    application = Application.builder().token(TOKEN).build()
    dispatcher = Dispatcher(application)

    # Komutları işleme
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    # Webhook'u ayarla
    setup_webhook()

    # Webhook endpointini başlat
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
