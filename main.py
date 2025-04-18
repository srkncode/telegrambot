from flask import Flask, request
import telegram
import os

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Render'da ayarlayacağınız ortam değişkeni
bot = telegram.Bot(token=BOT_TOKEN)

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    if request.method == 'POST':
        try:
            update = telegram.Update.de_json(request.get_json(), bot)
            if update.message:
                chat_id = update.message.chat_id
                text = update.message.text

                if text == "/start" or text == "/merhaba":
                    bot.send_message(chat_id=chat_id, text="Merhaba! Artık Render'da çalışıyorum!")
                elif text == "/yardim":
                    bot.send_message(chat_id=chat_id, text="Render üzerinde çalışan botum. Desteklediğim komutlar: /merhaba, /yardim")
                else:
                    bot.send_message(chat_id=chat_id, text="Bu komutu anlamadım.")

            return "OK", 200
        except Exception as e:
            print(f"Hata oluştu: {e}")
            return "Hata", 500
    return "OK", 200

@app.route('/')
def home():
    return "Telegram Bot Render'da Çalışıyor!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
