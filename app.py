import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Render ayakta tutma sunucusu
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS AKTIF", 200

# BOT AYARLARI
TOKEN = "8621050385:AAESXIZLT6HbS3CGeT-sT-HJcgvFuJF8ff0"
IRVUS_CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"

# Fiyat Çekme Fonksiyonu
async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{IRVUS_CA}", timeout=8).json()
        f = r['pairs'][0]['priceUsd']
        await update.message.reply_text(f"💎 **$IRVUS Fiyat:** `${f}`", parse_mode='Markdown')
    except Exception as e:
        print(f"Hata: {e}")
        await update.message.reply_text("❌ Fiyat şu an çekilemedi.")

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    # Web sunucusunu başlat
    Thread(target=run_web, daemon=True).start()
    
    # Botu en sade şekilde kur
    print(">>> BOT DINLEMEYE BASLADI")
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Sadece fiyat komutları
    application.add_handler(CommandHandler(["fiyat", "p", "price"], fiyat))
    
    # Botu çalıştır
    application.run_polling(drop_pending_updates=True)
    
