import telebot
import os

# Ortam değişkenlerinden API token'ını al
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Bot nesnesini oluştur
bot = telebot.TeleBot(BOT_TOKEN)

# /start komutunu işleyen fonksiyon
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Merhaba! Bu basit bir Telegram botudur.")

# Gelen tüm metin mesajlarını işleyen fonksiyon (yankı botu)
@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    bot.reply_to(message, f"Sen dedin ki: {message.text}")

# Botu sürekli dinlemeye başla
if __name__ == '__main__':
    bot.polling(none_stop=True)
