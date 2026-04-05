import os, requests, time
from flask import Flask
from threading import Thread
from telegram import Bot
from telegram.ext import Updater, CommandHandler

# Render ayakta tutma
app = Flask(__name__)
@app.route('/')
def home(): return "OK", 200

TOKEN = "8621050385:AAESXIZLT6HbS3CGeT-sT-HJcgvFuJF8ff0"
IRVUS_CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"

def fiyat(update, context):
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{IRVUS_CA}").json()
        f = r['pairs'][0]['priceUsd']
        update.message.reply_text(f"💎 **$IRVUS:** `${f}`")
    except:
        update.message.reply_text("❌ Hata")

if __name__ == '__main__':
    # Web sunucusu
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    
    # EN ESKI VE EN GARANTI YONTEM (Sürüm hatasını baypas eder)
    from telegram.ext import Updater
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("fiyat", fiyat))
    dp.add_handler(CommandHandler("p", fiyat))
    
    print(">>> BOT ILKEL MODDA BASLADI")
    updater.start_polling(drop_pending_updates=True)
    updater.idle()
    
