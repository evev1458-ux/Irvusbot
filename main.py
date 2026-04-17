import os, asyncio, threading, nest_asyncio
from flask import Flask
from telegram.ext import Application
from bot import register_handlers
from chain_monitor import ChainMonitor

nest_asyncio.apply()
app = Flask(__name__)
@app.route('/')
def h(): return "OK", 200

async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    
    bot_app = Application.builder().token(token).build()
    register_handlers(bot_app)
    monitor = ChainMonitor(bot_app)
    
    async with bot_app:
        await bot_app.initialize(); await bot_app.start()
        asyncio.create_task(monitor.start())
        await bot_app.updater.start_polling(drop_pending_updates=True)
        await asyncio.Event().wait()

if __name__ == "__main__": asyncio.run(main())
