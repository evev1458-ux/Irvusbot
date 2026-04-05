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
# Ücretsiz Çizim API'si (Hugging Face)
HF_API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"

# Loglama ayarları
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- FLASK (Render'ın botu uyutmaması için) ---
app = Flask('')
@app.route('/')
def home(): return "Bot 7/24 Aktif!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- FİYAT VERİSİ ÇEKME FONKSİYONU ---
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
        
        text = (
            f"💎 **Irvus Token ($IRVUS)**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💵 **Fiyat:** `${float(price):.10f}`\n"
            f"📈 **24s Değişim:** `%{change}`\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        
        # Şık Buton Yapısı
        keyboard = [[InlineKeyboardButton("📊 DexScreener Grafiği", url=dex_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # disable_web_page_preview=True -> O büyük ekranı kapatır
        await update.message.reply_text(
            text, 
            parse_mode="Markdown", 
            reply_markup=reply_markup,
            disable_web_page_preview=True 
        )
    else:
        await update.message.reply_text("❌ Fiyat verisi şu an çekilemiyor.")

# --- KOMUT: /ciz ---
async def ciz_gonder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("⚠️ Lütfen ne çizmemi istediğini yaz! \nÖrnek: `/ciz kedi`", parse_mode="Markdown")
        return

    msg = await update.message.reply_text("🎨 Resminizi çiziyorum, lütfen bekleyin...")
    
    try:
        # Hugging Face API isteği
        response = requests.post(HF_API_URL, json={"inputs": prompt}, timeout=60)
        image_bytes = response.content
        
        # Resmi Telegram'a gönder
        await update.message.reply_photo(
            photo=io.BytesIO(image_bytes), 
            caption=f"✨ Çizimim: `{prompt}`",
            parse_mode="Markdown"
        )
        await msg.delete() # "Çiziyorum" mesajını sil
    except Exception as e:
        logging.error(f"Çizim hatası: {e}")
        await msg.edit_text("❌ Şu an çizim yapamıyorum, lütfen biraz sonra tekrar deneyin.")

# --- KOMUT: /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 **Irvus Bot Yayında!**\n\n"
        "📈 `/fiyat` - Canlı fiyat bilgisi\n"
        "🎨 `/ciz [kelime]` - AI ile resim çizer\n\n"
        "Seni dinliyorum!",
        parse_mode="Markdown"
    )

# --- ANA ÇALIŞTIRICI ---
if __name__ == '__main__':
    # Web sunucusunu ayrı bir kolda başlat
    Thread(target=run_web_server).start()
    
    # Bot uygulamasını başlat
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Handler'ları ekle
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("fiyat", fiyat_gonder))
    application.add_handler(CommandHandler("ciz", ciz_gonder))
    
    # Kelime olarak "fiyat" geçerse de fiyatı gönder
    application.add_handler(MessageHandler(filters.Regex(r"(?i)fiyat"), fiyat_gonder))
    
    print("Bot başarıyla başlatıldı!")
    application.run_polling()
