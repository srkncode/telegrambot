from flask import Flask
import threading
import subprocess
import os
import time
from telegram import Bot
from telegram.ext import Application

app = Flask(__name__)

# Global değişken - botun çalışıp çalışmadığını kontrol etmek için
bot_running = False

# Bot token'ını al
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "BURAYA_BOT_TOKEN_EKLE")

@app.route('/')
def home():
    return "Telegram Bot çalışıyor!"

@app.route('/health')
def health():
    return {"status": "up", "bot_running": bot_running}

if __name__ == "__main__":
    # Bot'u import et ve çalıştır (direkt olarak çalıştırmak yerine)
    import main
    
    # Flask uygulamasını çalıştır
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
