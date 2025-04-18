import os
import requests
import time
import json
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Loglama ayarları
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token'ını buraya ekleyin
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "BURAYA_BOT_TOKEN_EKLE")

# News API için API anahtarı (https://newsapi.org/ adresinden ücretsiz alabilirsiniz)
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "BURAYA_NEWS_API_KEY_EKLE")

# Başlangıç komutu için işleyici
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bot başladığında karşılama mesajı gönderir."""
    user = update.effective_user
    await update.message.reply_text(
        f'Merhaba {user.first_name}! Haber botuna hoş geldiniz. '
        f'Son haberleri görmek için /haberler komutunu kullanabilirsiniz.'
    )

# Haber alma fonksiyonu
async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Haberleri alıp kullanıcıya gönderir."""
    try:
        # Varsayılan olarak Türkiye haberlerini al
        url = f"https://newsapi.org/v2/top-headlines?country=tr&apiKey={NEWS_API_KEY}"
        
        # Eğer kullanıcı bir kategori belirttiyse
        if context.args and len(context.args) > 0:
            category = context.args[0].lower()
            valid_categories = ['business', 'entertainment', 'general', 'health', 'science', 'sports', 'technology']
            
            if category in valid_categories:
                url = f"https://newsapi.org/v2/top-headlines?country=tr&category={category}&apiKey={NEWS_API_KEY}"
                await update.message.reply_text(f"{category.capitalize()} kategorisindeki son haberler:")
            else:
                await update.message.reply_text(
                    f"Geçersiz kategori. Lütfen şu kategorilerden birini seçin: {', '.join(valid_categories)}"
                )
                return
        else:
            await update.message.reply_text("İşte günün öne çıkan haberleri:")
        
        response = requests.get(url)
        news = response.json()
        
        if news["status"] == "ok" and news["articles"]:
            # En fazla 5 haber gönder
            for article in news["articles"][:5]:
                news_title = article["title"]
                news_description = article.get("description", "Açıklama yok")
                news_url = article["url"]
                
                message = f"📰 *{news_title}*\n\n{news_description}\n\n🔗 [Haberin devamı için tıklayın]({news_url})"
                await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text("Üzgünüm, şu anda haber bulunamadı.")
    except Exception as e:
        logger.error(f"Haber alınırken hata oluştu: {e}")
        await update.message.reply_text("Haberler alınırken bir hata oluştu. Lütfen daha sonra tekrar deneyin.")

# Yardım komutu
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Yardım mesajı gönderir."""
    help_text = """
*Haber Botu Komutları:*

/start - Botu başlatır
/haberler - Genel güncel haberleri gösterir
/haberler [kategori] - Belirli bir kategorideki haberleri gösterir
  Kategoriler: business, entertainment, general, health, science, sports, technology
/yardim - Bu yardım mesajını gösterir

Örnek: /haberler sports
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

# Tanımlanmamış mesajlara cevap ver
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bilinmeyen komutlara yanıt verir."""
    await update.message.reply_text(
        "Üzgünüm, bu komutu anlamadım. Yardım için /yardim yazabilirsiniz."
    )

def main() -> None:
    """Botu başlatır."""
    # Uygulama oluştur
    application = Application.builder().token(TOKEN).build()

    # Komut işleyicilerini ekle
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("haberler", get_news))
    application.add_handler(CommandHandler("yardim", help_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Tanımlanmamış komutları yakala
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    # Botu başlat
    application.run_polling()

if __name__ == "__main__":
    main()
