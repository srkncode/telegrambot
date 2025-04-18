import os
import asyncio
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

app = Flask(__name__)
bot = Bot(token=TOKEN)


# Asenkron mesaj işleme
async def handle_message(chat_id, text):
    await bot.send_message(chat_id=chat_id, text=f"Gelen mesaj: {text}")


# Senkron ortamda async fonksiyon çalıştırıcı
def run_async(func, *args, **kwargs):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(func(*args, **kwargs))
    else:
        return asyncio.ensure_future(func(*args, **kwargs))


@app.route('/')
def index():
    return "Bot çalışıyor!", 200


@app.route('/webhook', methods=['GET', 'POST'])
def telegram_webhook():
    if request.method == 'GET':
        return "Webhook aktif", 200

    try:
        update = Update.de_json(request.get_json(force=True), bot)

        if update.message:
            chat_id = update.message.chat.id
            text = update.message.text
            run_async(handle_message, chat_id, text)

        return "OK", 200
    except Exception as e:
        print(f"Hata oluştu: {e}")
        return "Hata", 500


# Webhook ayarlama (yalnızca deploy sırasında çalışır)
if __name__ == "__main__":
    bot.delete_webhook()
    set_result = bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    print("Webhook ayarlandı:", set_result)
