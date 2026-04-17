import os
import sys
import signal
import asyncio
import logging
import threading
from flask import Flask
from waitress import serve as waitress_serve
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# Dosya yolları için
sys.path.insert(0, os.path.dirname(__file__))
from database import get_all_group_chat_ids, get_tokens, get_group
from tracker import tracking_loop

# Loglama Ayarı
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# Flask Health Check (Render için)
health_app = Flask(__name__)
@health_app.route("/")
def health(): return "OK", 200

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    waitress_serve(health_app, host="0.0.0.0", port=port)

# Bot Komutları ve Mesaj Yönetimi (Burayı mevcut komutlarınla doldurabilirsin)
# ... (Önceki main.py'deki komut handlerların burada olmalı) ...

def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN BULUNAMADI!")
        return

    # 1. Health Server'ı ayrı kolda başlat
    threading.Thread(target=run_health_server, daemon=True).start()

    # 2. Application kur
    app = Application.builder().token(BOT_TOKEN).build()

    # 3. Handlerları ekle (Burada senin mevcut handlerların olmalı)
    # app.add_handler(CommandHandler("start", start_command)) vs.

    # 4. Takip Döngüsünü Başlat
    async def post_init(application):
        asyncio.create_task(tracking_loop(application.bot, get_all_group_chat_ids))
        logger.info("✅ Takip görevi arka planda başlatıldı.")

    app.post_init = post_init

    logger.info("🤖 Bot başlatılıyor...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
    
