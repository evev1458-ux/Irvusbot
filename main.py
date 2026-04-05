import os
import logging
import aiohttp
import io
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler

# --- AYARLAR ---
TOKEN = "8621050385:AAESXIZLT6HbS3CGeT-sT-HJcgvFuJF8ff0"
IRVUS_CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
HF_TOKEN = "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"

# YENİ GÜNCEL ADRES (Hata veren yeri burasıyla değiştirdik)
HF_API_URL = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-2-1"
HF_HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

app = Flask('')
@app.route('/')
def home(): return "Bot Aktif!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

async def fiyat_gonder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = f"https://api.dexscreener.com/latest/dex/tokens/{IRVUS_CA}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as resp:
                data = await resp.json()
                pairs = data.get("pairs")
                if pairs:
                    pair = pairs[0]
                    price = pair.get("priceUsd", "0")
                    change = pair.get("priceChange", {}).get("h24", "0")
                    text = f"💎 **Irvus Token ($IRVUS)**\n━━━━━━━━━━━━━━━━━━━━\n💵 **Fiyat:** `${float(price):.10f}`\n📈 **24s Değişim:** `%{change}`\n━━━━━━━━━━━━━━━━━━━━"
                    keyboard = [[InlineKeyboardButton("📊 DexScreener Grafiği", url=pair.get("url"))]]
                    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)
                else:
                    await update.message.reply_text("❌ Veri bulunamadı. Likidite kontrol ediliyor...")
        except Exception as e:
            await update.message.reply_text(f"⚠️ Bağlantı hatası: {str(e)}")

async def ciz_gonder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("⚠️ Örn: `/ciz cat in space`")
        return

    msg = await update.message.reply_text("🎨 Resim çiziliyor, lütfen bekleyin...")
    
    async with aiohttp.ClientSession() as session:
        try:
            # Yeni Router URL'sini kullanıyoruz
            async with session.post(HF_API_URL, headers=HF_HEADERS, json={"inputs": prompt}, timeout=60) as resp:
                if resp.status == 200:
                    img_data = await resp.read()
                    await update.message.reply_photo(photo=io.BytesIO(img_data), caption=f"✨ `{prompt}`")
                    await msg.delete()
                elif resp.status == 503:
                    await msg.edit_text("⏳ Model uyanıyor... 15 saniye sonra tekrar deneyin.")
                else:
                    err_resp = await resp.text()
                    await msg.edit_text(f"❌ Hata ({resp.status}): Sunucu yanıt vermedi.")
        except Exception as e:
            await msg.edit_text(f"⚠️ Hata: {str(e)}")

if __name__ == '__main__':
    Thread(target=run_web_server).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("Bot Aktif! /fiyat veya /ciz yazabilirsin.")))
    app_bot.add_handler(CommandHandler("fiyat", fiyat_gonder))
    app_bot.add_handler(CommandHandler("ciz", ciz_gonder))
    app_bot.add_handler(MessageHandler(filters.Regex(r"(?i)fiyat"), fiyat_gonder))
    app_bot.run_polling()
    
