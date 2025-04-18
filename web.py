if __name__ == "__main__":
    # Bot'u import et
    import main
    
    # Bot'u ayrı bir thread'de başlat
    bot_thread = threading.Thread(target=main.run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Flask uygulamasını çalıştır
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
