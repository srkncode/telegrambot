# Diğer importlar...

# main() fonksiyonunu doğrudan çağırmayacağız
def main():
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

    return application

# Web.py'den çağrılacak fonksiyon
def run_bot():
    global bot_running
    try:
        bot_running = True
        app = main()
        app.run_polling()
    except Exception as e:
        bot_running = False
        logger.error(f"Bot çalıştırılırken hata: {e}")

if __name__ == "__main__":
    # Direkt çalıştırıldığında bot'u başlat
    application = main()
    application.run_polling()
