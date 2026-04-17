import os
import asyncio
import logging
import threading
from flask import Flask
import nest_asyncio
from dotenv import load_dotenv
from telegram.ext import Application
from bot import register_handlers
from chain_monitor import ChainMonitor

# Render ve asenkron döngü hatalarını önlemek için
nest_asyncio.apply()
load_dotenv()

# --- RENDER PORT HATASI ÇÖZÜMÜ (FLASK SERVER) ---
app_flask = Flask(__name__)

@app_flask.route('/')
def health_check():
    return "Bot is alive!", 200

def run_flask():
    # Render'ın beklediği portu açıyoruz
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host='0.0.0.0', port=port)

# --- LOGLAMA ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        # Eğer render.yaml'da TELEGRAM_BOT_TOKEN yazdıysan onu da kontrol et
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            raise ValueError("BOT_TOKEN veya TELEGRAM_BOT_TOKEN bulunamadı!")

    # Flask server'ı ayrı bir kanalda (thread) başlat
    threading.Thread(target=run_flask, daemon=True).start()
    logger.info("Flask health-check server başlatıldı.")

    app = Application.builder().token(token).build()

    # Komutları kaydet
    register_handlers(app)

    # Zincir monitörünü başlat
    monitor = ChainMonitor(app)

    logger.info("Bot başlatılıyor...")

    async with app:
        await app.initialize() # Uygulamayı hazırla
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        logger.info("✅ Bot çalışıyor!")

        # Monitor'ü arka planda çalıştır
        monitor_task = asyncio.create_task(monitor.start())

        try:
            # Sonsuza kadar çalış, stop sinyali gelene kadar bekle
            stop_event = asyncio.Event()
            await stop_event.wait()
        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("Bot durduruluyor...")
        finally:
            monitor_task.cancel()
            if app.updater.running:
                await app.updater.stop()
            await app.stop()
            await app.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Kritik hata: {e}")
        
