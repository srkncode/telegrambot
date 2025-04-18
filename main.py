import telebot
import os
from flask import Flask, request
import threading

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route("/")
def index():
    return "Telegram botu çalışıyor!"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Merhaba! Web servis üzerinden çalışıyorum.")

@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    bot.reply_to(message, f"Sen dedin ki (web): {message.text}")

def run_flask():
    app.run(host="0.0.0.0", port=80)

def run_bot():
    bot.polling(none_stop=True)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    bot_thread = threading.Thread(target=run_bot)

    flask_thread.start()
    bot_thread.start()

    flask_thread.join()
    bot_thread.join()
