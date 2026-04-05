import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Render'ın botu kapatmaması için basit web sunucusu
app = Flask(__name__)
@app.route('/')
def home(): return "SISTEM AKTIF", 200

# AYARLAR
TOKEN = "8621050385:AAESXIZLT6HbS3CGeT-sT-HJcgvFuJF8ff0"
IRVUS_CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{IRVUS_CA}").json()
        f = r['pairs'][0]['priceUsd']
        await update.message.reply_text(f"💎 **$IRVUS:** `${f}`")
    except: await update.message.reply_text("❌ Fiyat hatası.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = " ".join(context.args)
    if not p: return await update.message.reply_text("❌ Örn: /ciz aslan")
    await update.message.reply_text("🎨 Çiziliyor...")
    url = f"https://image.pollinations.ai/prompt/{p.replace(' ', '%20')}?nologo=true"
    await update.message.reply_photo(photo=url, caption=f"🖼 AI: {p}")

if __name__ == '__main__':
    # Web sunucusunu başlat
    port = int(os.environ.get("PORT", 10000))
    Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    
    # Botu en temel ApplicationBuilder ile başlat (Hata riskini azaltır)
    print(">>> BOT BASLADI")
    builder = ApplicationBuilder().token(TOKEN).build()
    
    builder.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    builder.add_handler(CommandHandler(["ciz", "draw"], ciz))
    
    builder.run_polling(drop_pending_updates=True)
    
