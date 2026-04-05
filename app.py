import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Render'ın botu kapatmaması için gereken mini sunucu
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS AKTIF", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- AYARLAR ---
TOKEN = "8621050385:AAESXIZLT6HbS3CGeT-sT-HJcgvFuJF8ff0"
IRVUS_CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"

# --- KOMUTLAR ---

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{IRVUS_CA}", timeout=10).json()
        f = r['pairs'][0]['priceUsd']
        await update.message.reply_text(f"💎 **$IRVUS Fiyat:** `${f}`", parse_mode='Markdown')
    except:
        await update.message.reply_text("❌ Fiyat şu an çekilemedi.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = " ".join(context.args)
    if not p:
        return await update.message.reply_text("❌ Örn: /ciz warrior")
    
    await update.message.reply_text(f"🎨 **'{p}'** çiziliyor...")
    url = f"https://image.pollinations.ai/prompt/{p.replace(' ', '%20')}?nologo=true"
    await update.message.reply_photo(photo=url, caption=f"🖼 AI: {p}")

# --- ANA ÇALIŞTIRICI ---
if __name__ == '__main__':
    # Web sunucusunu başlat
    Thread(target=run_web, daemon=True).start()
    
    # Botu kur
    application = Application.builder().token(TOKEN).build()
    
    # Komutları ekle (fiyat için /fiyat veya /p, çizim için /ciz veya /draw)
    application.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    application.add_handler(CommandHandler(["ciz", "draw"], ciz))
    
    print(">>> BOT DINLEMEYE BASLADI")
    # Botu dinlemeye al
    application.run_polling(drop_pending_updates=True)
