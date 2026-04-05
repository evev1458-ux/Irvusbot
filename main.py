import os
import logging
import aiohttp
import requests
import io
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler

# --- AYARLAR (Kendi Token'ını Buraya Yaz) ---
TOKEN = "8621050385:AAESXIZLT6HbS3CGeT-sT-HJcgvFuJF8ff0"
IRVUS_CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
HF_API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

app = Flask('')
@app.route('/')
def home(): return "Bot Aktif!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- FİYAT VERİSİ ÇEKME ---
async def get_dex_price():
    url = f"https://api.dexscreener.com/latest/dex/tokens/{IRVUS_CA}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("pairs"):
                    return data["pairs"][0]
    return None

# --- KOMUT: /fiyat ---
async def fiyat_gonder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await get_dex_price()
    if data:
        price = data.get("priceUsd", "0")
        change = data.get("priceChange", {}).get("h24", "0")
        dex_url = data.get("url")
        
        text = f"💎 **Irvus Token ($IRVUS)**\n\n💵 **Fiyat:** `${float(price):.8f}`\n📈 **24s Değişim:** %{change}"
        
        # Buton Oluşturma
        keyboard = [[InlineKeyboardButton("📊 DexScreener Grafiği", url=dex_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup, disable_web_page_preview=True)
    else:
        await update.message.reply_text("❌ Fiyat verisi şu an çekilemiyor.")

# --- KOMUT: /ciz ---
async def ciz_gonder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("⚠️ Lütfen çizmek istediğiniz şeyi yazın. Örn: `/ciz kedi`", parse_mode="Markdown")
        return

    msg = await update.message.reply_text("🎨 Çiziyorum, lütfen bekleyin...")
    
    try:
        # Hugging Face üzerinden resim oluşturma
        response = requests.post(HF_API_URL, json={"inputs": prompt})
        image_bytes = response.content
        
        await update.message.reply_photo(photo=io.BytesIO(image_bytes), caption=f"✨ `{prompt}`")
        await msg.delete()
    except:
        await msg.edit_text("❌ Çizim yapılamadı, servis meşgul olabilir.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot aktif! 🚀\n/fiyat - Güncel fiyat\n/ciz [kelime] - Resim çizer")

if __name__ == '__main__':
    Thread(target=run_web_server).start()
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("fiyat", fiyat_gonder))
    application.add_handler(CommandHandler("ciz", ciz_gonder))
    application.add_handler(MessageHandler(filters.Regex(r"(?i)fiyat"), fiyat_gonder))
    
    application.run_polling()
    
