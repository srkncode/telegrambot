from flask import Flask, request
import asyncio
import os
import requests
from telegram import Bot, Update
from telegram.constants import ParseMode

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)

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

# Tek endpoint: hem GET hem POST
@app.route('/webhook', methods=['GET', 'POST'])
def telegram_webhook():
    if request.method == 'GET':
        return "Bu endpoint sadece Telegram sunucularından POST istekleri kabul eder", 200

    try:
        update = Update.de_json(request.get_json(force=True), bot)

        if update.message:
            chat_id = update.message.chat.id
            text = update.message.text

            asyncio.run(handle_message(chat_id, text))

        return "OK", 200
    except Exception as e:
        print(f"Hata oluştu: {e}")
        return "Hata", 500

# async mesaj işleyici
async def handle_message(chat_id, text):
    if text in ["/start", "/merhaba"]:
        await bot.send_message(chat_id=chat_id, text="Merhaba! Artık Render'da çalışıyorum!")
    elif text == "/yardim":
        await bot.send_message(chat_id=chat_id, text="Render üzerinde çalışan botum. Desteklediğim komutlar: /merhaba, /yardim")
    elif text == "/setwebhook" and str(chat_id) == os.environ.get("ADMIN_CHAT_ID", ""):
        set_telegram_webhook()
        await bot.send_message(chat_id=chat_id, text="Webhook yeniden ayarlandı!")
    else:
        await bot.send_message(chat_id=chat_id, text="Bu komutu anlamadım.")

# Başlangıçta webhook'u ayarla
with app.app_context():
    set_telegram_webhook()
