import os
import logging
import aiohttp
import requests
import io
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler

# --- AYARLAR ---
TOKEN = "8621050385:AAESXIZLT6HbS3CGeT-sT-HJcgvFuJF8ff0"
IRVUS_CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"

# HUGGING FACE AYARLARI
HF_TOKEN = "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"
# Daha stabil bir model seçtik
HF_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
HF_HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

app = Flask('')
@app.route('/')
def home(): return "Bot Aktif!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- FİYAT FONKSİYONU (Daha detaylı hata raporu ile) ---
async def get_dex_price():
    url = f"https://api.dexscreener.com/latest/dex/tokens/{IRVUS_CA}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("pairs"):
                        return data["pairs"][0]
        return "NO_PAIR"
    except Exception as e:
        return str(e)

async def fiyat_gonder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = await get_dex_price()
    if isinstance(res, dict):
        price = res.get("priceUsd", "0")
        change = res.get("priceChange", {}).get("h24", "0")
        dex_url = res.get("url")
        text = f"💎 **Irvus Token ($IRVUS)**\n\n💵 **Fiyat:** `${float(price):.10f}`\n📈 **24s Değişim:** %{change}"
        keyboard = [[InlineKeyboardButton("📊 DexScreener Grafiği", url=dex_url)]]
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)
    else:
        await update.message.reply_text(f"❌ Veri Hatası: {res}")

# --- ÇİZİM FONKSİYONU (Daha detaylı hata raporu ile) ---
async def ciz_gonder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("⚠️ Örn: `/ciz cat in space`")
        return

    msg = await update.message.reply_text("🎨 Çiziliyor...")

    try:
        response = requests.post(HF_API_URL, headers=HF_HEADERS, json={"inputs": prompt}, timeout=60)
        if response.status_code == 200:
            await update.message.reply_photo(photo=io.BytesIO(response.content), caption=f"✨ `{prompt}`")
            await msg.delete()
        else:
            # Burası hatayı anlamamızı sağlayacak
            error_detail = response.json() if response.content else "Bilinmeyen Hata"
            await msg.edit_text(f"❌ API Hatası ({response.status_code}): {error_detail}")
    except Exception as e:
        await msg.edit_text(f"❌ Bağlantı Hatası: {str(e)}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Bot Hazır!\n/fiyat ve /ciz komutlarını kullanabilirsin.")

if __name__ == '__main__':
    Thread(target=run_web_server).start()
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("fiyat", fiyat_gonder))
    application.add_handler(CommandHandler("ciz", ciz_gonder))
    application.run_polling()
    
