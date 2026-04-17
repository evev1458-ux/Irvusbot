import os
import asyncio
import logging
import threading
import nest_asyncio
from flask import Flask
from telegram.ext import Application
from bot import register_handlers
from chain_monitor import ChainMonitor

nest_asyncio.apply()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app_flask = Flask(__name__)
@app_flask.route('/')
def health(): return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host='0.0.0.0', port=port)

async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN bulunamadı!")
        return

    threading.Thread(target=run_flask, daemon=True).start()

    app = Application.builder().token(token).build()
    register_handlers(app)
    
    monitor = ChainMonitor(app)
    
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        
        # Alım takibini başlat
        monitor_task = asyncio.create_task(monitor.start())
        
        logger.info("✅ Bot ve İzleme Motoru Aktif!")
        try:
            await asyncio.Event().wait()
        finally:
            monitor_task.cancel()
            await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
    
