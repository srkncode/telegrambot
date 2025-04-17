import json
import os
import telegram
import functions_framework

BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Ortam değişkenini al
bot = telegram.Bot(token=BOT_TOKEN)

@functions_framework.http
def telegram_webhook(request):
    if request.method == 'POST':
        try:
            update = telegram.Update.de_json(request.get_json(), bot)
            if update.message:
                chat_id = update.message.chat_id
                text = update.message.text

                if text == "/start" or text == "/merhaba":
                    bot.send_message(chat_id=chat_id, text="Merhaba! Ben serverless bir Telegram botuyum.")
                elif text == "/yardim":
                    bot.send_message(chat_id=chat_id, text="Şu an sadece /merhaba ve /yardim komutlarını destekliyorum.")
                else:
                    bot.send_message(chat_id=chat_id, text="Anlamadım.")

            return "OK", 200
        except Exception as e:
            print(f"Hata oluştu: {e}")
            return "Hata", 500
    return "OK", 200