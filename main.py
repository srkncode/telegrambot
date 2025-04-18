import os
import telegram
import json
from fastapi import FastAPI, Request

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telegram.Bot(token=BOT_TOKEN)

app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = telegram.Update.de_json(data, bot)
    if update.message:
        chat_id = update.message.chat_id
        text = update.message.text

        if text == "/start" or text == "/merhaba":
            bot.send_message(chat_id=chat_id, text="Merhaba! Ben serverless bir Telegram botuyum.")
        elif text == "/yardim":
            bot.send_message(chat_id=chat_id, text="Şu an sadece /merhaba ve /yardim komutlarını destekliyorum.")
        else:
            bot.send_message(chat_id=chat_id, text="Anlamadım.")
    return "OK"
