from flask import Flask
import threading
import subprocess
import os

app = Flask(__name__)

# Ana bot dosyasını başlat
def run_bot():
    subprocess.call(["python", "main.py"])

@app.route('/')
def home():
    return "Telegram Bot çalışıyor!"

# Bot'u ayrı bir thread'de başlat
bot_thread = threading.Thread(target=run_bot)
bot_thread.daemon = True
bot_thread.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
