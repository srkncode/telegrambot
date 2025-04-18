from flask import Flask, request
import telegram
import os
import requests  # requests modülünü ekledik

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Render'da ayarlayacağınız ortam değişkeni
bot = telegram.Bot(token=BOT_TOKEN)

# Webhook ayarlama fonksiyonu
def set_telegram_webhook():
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', '')}/webhook"
    if not webhook_url.startswith("https://"):
        print("Webhook URL'si HTTPS ile başlamıyor, Render'da çalıştığından emin olun")
        return
    
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
            json={
                "url": webhook_url,
                "drop_pending_updates": True,
                "allowed_updates": ["message"]
            }
        )
        print("Webhook ayarlandı:", response.json())
    except Exception as e:
        print(f"Webhook ayarlanırken hata oluştu: {e}")

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
                elif text == "/setwebhook" and str(chat_id) == os.environ.get("ADMIN_CHAT_ID", ""):
                    set_telegram_webhook()
                    bot.send_message(chat_id=chat_id, text="Webhook yeniden ayarlandı!")
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
    # Uygulama başlarken webhook'u ayarla (sadece Render ortamında)
    if os.environ.get('RENDER'):
        set_telegram_webhook()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
