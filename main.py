import os
import requests
import logging
import time
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from io import BytesIO
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Loglama ayarları
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token'ı
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "BURAYA_BOT_TOKEN_EKLE")

# Bazı BIST sembollerini tanımlayalım
BIST_SYMBOLS = {
    'akbnk': 'AKBNK.IS',
    'thyao': 'THYAO.IS',
    'eregl': 'EREGL.IS',
    'garan': 'GARAN.IS',
    'asels': 'ASELS.IS',
    'tuprs': 'TUPRS.IS',
    'sise': 'SISE.IS',
    'kchol': 'KCHOL.IS',
    'arclk': 'ARCLK.IS',
    'ykbnk': 'YKBNK.IS',
    'bimas': 'BIMAS.IS',
    'tskb': 'TSKB.IS',
    'petkm': 'PETKM.IS',
    'froto': 'FROTO.IS',
    'tcell': 'TCELL.IS',
    'halkb': 'HALKB.IS',
    'vestl': 'VESTL.IS',
    'vakbn': 'VAKBN.IS',
    'toaso': 'TOASO.IS',
    'sahol': 'SAHOL.IS',
}

# Başlangıç komutu için işleyici
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bot başladığında karşılama mesajı gönderir."""
    user = update.effective_user
    await update.message.reply_text(
        f'Merhaba {user.first_name}! Borsa İstanbul hisse analiz botuna hoş geldiniz. '
        f'Hisse bilgilerini görmek için /hisse SEMBOL komutunu kullanabilirsiniz. Örnek: /hisse akbnk'
    )

# Yardım komutu
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Yardım mesajı gönderir."""
    symbols_list = ', '.join(BIST_SYMBOLS.keys())
    help_text = f"""
*BIST Hisse Analiz Botu Komutları:*

/start - Botu başlatır
/hisse [sembol] - Belirtilen hissenin fiyat ve teknik analiz bilgilerini gösterir
/liste - Sorgulayabileceğiniz hisse sembollerini listeler
/yardim - Bu yardım mesajını gösterir

Sorgulayabileceğiniz bazı semboller: {symbols_list}

Örnek: /hisse akbnk
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

# Hisse listesini göster
async def list_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sorgulanabilecek hisse listesini gösterir"""
    symbols_list = ', '.join([f"{key} ({value.replace('.IS', '')})" for key, value in BIST_SYMBOLS.items()])
    await update.message.reply_text(
        f"*Sorgulanabilecek BIST Hisseleri:*\n\n{symbols_list}",
        parse_mode='Markdown'
    )

# Destek ve direnç bölgelerini hesaplama
def calculate_support_resistance(data, periods=14):
    """Basit bir destek ve direnç hesaplama fonksiyonu"""
    # Son dönem için destek ve direnç seviyeleri
    highs = data['High'].tail(periods)
    lows = data['Low'].tail(periods)
    close = data['Close'].iloc[-1]
    
    # Destek seviyeleri (Son dönemdeki en düşükler)
    supports = lows.nsmallest(3).values
    
    # Direnç seviyeleri (Son dönemdeki en yüksekler)
    resistances = highs.nlargest(3).values
    
    # Güncel fiyata göre destek ve dirençleri filtrele
    supports = [s for s in supports if s < close]
    resistances = [r for r in resistances if r > close]
    
    return supports, resistances

# Hisse bilgilerini göster
async def stock_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Belirtilen hissenin bilgilerini ve analizini gösterir."""
    try:
        if not context.args or len(context.args) < 1:
            await update.message.reply_text("Lütfen bir hisse sembolü belirtin. Örnek: /hisse akbnk")
            return
        
        symbol = context.args[0].lower()
        
        # Sembol kontrolü
        if symbol not in BIST_SYMBOLS:
            symbols_list = ', '.join(list(BIST_SYMBOLS.keys())[:10]) + "..."
            await update.message.reply_text(
                f"Geçersiz sembol. Sorgulanabilecek sembollerden bazıları: {symbols_list}\n"
                f"Tam liste için /liste komutunu kullanın."
            )
            return
        
        # Kullanıcıya işlemin başladığını bildir
        await update.message.reply_text(f"{symbol.upper()} hissesi için veri alınıyor...")
        
        # Yahoo Finance API'den veri çek
        ticker = yf.Ticker(BIST_SYMBOLS[symbol])
        history = ticker.history(period="6mo")
        
        if history.empty:
            await update.message.reply_text(f"{symbol.upper()} için veri bulunamadı.")
            return
        
        # Son fiyat bilgileri
        last_price = history['Close'].iloc[-1]
        prev_close = history['Close'].iloc[-2]
        change = ((last_price - prev_close) / prev_close) * 100
        
        # Destek ve direnç seviyeleri
        supports, resistances = calculate_support_resistance(history)
        
        # Basit hareketli ortalamalar
        ma50 = history['Close'].rolling(window=50).mean().iloc[-1]
        ma200 = history['Close'].rolling(window=200).mean().iloc[-1]
        
        # Trend durumu
        trend = "YUKARI" if ma50 > ma200 else "AŞAĞI"
        
        # Grafiği oluştur
        plt.figure(figsize=(10, 6))
        plt.plot(history.index, history['Close'], label='Kapanış Fiyatı')
        plt.plot(history.index, history['Close'].rolling(window=50).mean(), label='50 Günlük Ortalama', color='orange')
        plt.plot(history.index, history['Close'].rolling(window=200).mean(), label='200 Günlük Ortalama', color='red')
        
        # Destek ve dirençleri göster
        for s in supports:
            plt.axhline(y=s, color='green', linestyle='--', alpha=0.7)
        for r in resistances:
            plt.axhline(y=r, color='red', linestyle='--', alpha=0.7)
        
        plt.title(f"{symbol.upper()} - Son 6 Ay")
        plt.xlabel('Tarih')
        plt.ylabel('Fiyat (TL)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Grafiği hafızada tut ve gönder
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        
        # Mesaj metnini oluştur
        support_text = "\n".join([f"• {s:.2f} TL" for s in supports]) if supports else "Tespit edilemedi"
        resistance_text = "\n".join([f"• {r:.2f} TL" for r in resistances]) if resistances else "Tespit edilemedi"
        
        message = f"""
*{symbol.upper()} Hisse Analizi*

📊 *Son Fiyat:* {last_price:.2f} TL
📈 *Değişim:* {change:.2f}%
🔄 *Trend:* {trend}

*50 Günlük Ortalama:* {ma50:.2f} TL
*200 Günlük Ortalama:* {ma200:.2f} TL

*Destek Seviyeleri:*
{support_text}

*Direnç Seviyeleri:*
{resistance_text}

_Son güncelleme: {history.index[-1].strftime('%d.%m.%Y')}_
"""
        
        # Önce grafiği gönder
        await update.message.reply_photo(buffer, caption="Grafik yükleniyor...")
        
        # Sonra analiz sonuçlarını gönder
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Hisse bilgisi alınırken hata oluştu: {e}")
        await update.message.reply_text("Hisse bilgileri alınırken bir hata oluştu. Lütfen daha sonra tekrar deneyin.")

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
    application.add_handler(CommandHandler("hisse", stock_info))
    application.add_handler(CommandHandler("liste", list_stocks))
    application.add_handler(CommandHandler("yardim", help_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Tanımlanmamış komutları yakala
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    # Botu başlat
    application.run_polling()

if __name__ == "__main__":
    main()
