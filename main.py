import os
import logging
import aiohttp
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler

# --- AYARLAR ---
TOKEN = "8621050385:AAESXIZLT6HbS3CGeT-sT-HJcgvFuJF8ff0"
IRVUS_CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

app = Flask('')
@app.route('/')
def home(): return "Bot Aktif!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

async def get_dex_price():
    url = f"https://api.dexscreener.com/latest/dex/tokens/{IRVUS_CA}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("pairs"):
                    return data["pairs"][0]
    return None

async def fiyat_gonder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Mesaj geldiğini loglarda görelim
    print("Fiyat sorgusu alındı!")
    data = await get_dex_price()
    if data:
        price = data.get("priceUsd", "0")
        change = data.get("priceChange", {}).get("h24", "0")
        text = f"💎 **Irvus Token ($IRVUS)**\n\n💵 Fiyat: ${float(price):.10f}\n📈 24s Değişim: %{change}\n\n🔗 [DexScreener]({data.get('url')})"
        await update.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Fiyat verisi şu an çekilemiyor.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Render üzerinde çalışan botunuz hazır! 🚀\nFiyat bakmak için /fiyat yazabilirsin.")

if __name__ == '__main__':
    Thread(target=run_web_server).start()
    application = ApplicationBuilder().token(TOKEN).build()
    
    # KOMUTLARI BURAYA EKLİYORUZ - SIRALAMA ÖNEMLİ
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("fiyat", fiyat_gonder))
    application.add_handler(MessageHandler(filters.Regex(r"(?i)fiyat"), fiyat_gonder))
    
    application.run_polling()
    
