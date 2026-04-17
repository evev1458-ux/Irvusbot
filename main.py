import os
import asyncio
import logging
from dotenv import load_dotenv
from telegram.ext import Application
from bot import register_handlers
from chain_monitor import ChainMonitor

load_dotenv()
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN environment variable eksik!")

    app = Application.builder().token(token).build()

    # Komutları kaydet
    register_handlers(app)

    # Zincir monitörünü başlat
    monitor = ChainMonitor(app)

    logger.info("Bot başlatılıyor...")

    async with app:
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        logger.info("✅ Bot çalışıyor!")

        # Monitor'ü arka planda çalıştır
        monitor_task = asyncio.create_task(monitor.start())

        try:
            await asyncio.Event().wait()  # Sonsuza kadar çalış
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass
        finally:
            monitor_task.cancel()
            await app.updater.stop()
            await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
    
