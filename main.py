import os
import ipaddress
from functools import wraps
from flask import Flask, request, abort
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

app = Flask(__name__)

# Configurations
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "default_secret_change_me")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")

# Initialize bot
bot = Bot(token=BOT_TOKEN)
updater = Updater(bot=bot, use_context=True)
dispatcher = updater.dispatcher

# Decorator for IP whitelisting
def telegram_ip_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.path == '/webhook':
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            if client_ip:
                client_ip = client_ip.split(',')[0].strip()
                if not any(ipaddress.ip_address(client_ip) in ipaddress.ip_network(net) for net in ['149.154.160.0/20', '91.108.4.0/22']):
                    app.logger.warning(f"Unauthorized IP attempt: {client_ip}")
                    abort(403)
        return f(*args, **kwargs)
    return decorated_function

def initialize_webhook():
    if not BOT_TOKEN:
        app.logger.error("BOT_TOKEN environment variable is missing!")
        return

    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', '')}/webhook"
    
    try:
        updater.bot.set_webhook(
            url=webhook_url,
            secret_token=WEBHOOK_SECRET,
            drop_pending_updates=True,
            allowed_updates=['message', 'callback_query']
        )
        app.logger.info("Webhook successfully set")
    except Exception as e:
        app.logger.error(f"Webhook setup failed: {str(e)}")

@app.route('/')
def home():
    return "Telegram Bot Active", 200

@app.route('/webhook', methods=['POST'])
@telegram_ip_required
def webhook():
    if request.headers.get('X-Telegram-Bot-Api-Secret-Token') != WEBHOOK_SECRET:
        abort(401)

    try:
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
        return "OK", 200
    except Exception as e:
        app.logger.error(f"Error processing update: {str(e)}")
        return "Internal Server Error", 500

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Merhaba! Ben Render'da çalışan bir botum 🤖")

def help_command(update: Update, context: CallbackContext):
    update.message.reply_text("Desteklenen komutlar:\n/start - Botu başlat\n/yardim - Yardım menüsü")

def merhaba(update: Update, context: CallbackContext):
    update.message.reply_text("Selam! Nasılsın? 😊")

def restart(update: Update, context: CallbackContext):
    if str(update.message.chat_id) == ADMIN_CHAT_ID:
        initialize_webhook()
        update.message.reply_text("🔄 Webhook yeniden ayarlandı")

# Handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("yardim", help_command))
dispatcher.add_handler(CommandHandler("merhaba", merhaba))
dispatcher.add_handler(CommandHandler("restart", restart))

if __name__ == '__main__':
    if os.environ.get('RENDER'):
        initialize_webhook()
    
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
