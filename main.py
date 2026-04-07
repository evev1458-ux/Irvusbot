import os, asyncio, time, aiohttp
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib.parse import quote

# --- 1. WEB SUNUCUSU (Render'ı Uyanık Tutar) ---
app = Flask(__name__)
@app.route('/')
def home():
    return "IRVUS POWER SYSTEM ONLINE", 200

# --- 2. AYARLAR ---
# Yeni verdiğin token buraya eklendi
TOKEN = "8621050385:AAHEpgqJYNNGXyon1I855vghWfkQ8p-4tlk"
CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
LOGO = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"

WEB_URL = "https://www.irvustoken.xyz"
X_URL = "https://x.com/irvus"

# --- 3. YARDIMCI FİYAT ÇEKİCİ ---
async def get_price():
    try:
        url = f"https://api.dexscreener.com/latest/dex/pairs/base/{CA}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as r:
                data = await r.json()
                return float(data['pair']['priceUsd'])
    except:
        return 0.0

# --- 4. KOMUTLAR ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start veya /star komutu için butonlu karşılama"""
    msg = (f"💎 **IRVUS TOKEN DÜNYASI**\n\n"
           f"📄 **Sözleşme Adresi (CA):**\n`{CA}`")
    
    kb = [[
        InlineKeyboardButton("🌐 Web Sitesi", url=WEB_URL),
        InlineKeyboardButton("🐦 X (Twitter)", url=X_URL)
    ]]
    
    await update.message.reply_photo(
        photo=LOGO,
        caption=msg,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode='Markdown'
    )

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/fiyat komutu"""
    price = await get_price()
    if price > 0:
        await update.message.reply_text(f"💰 **Güncel $IRVUS Fiyatı:** `${price}`")
    else:
        await update.message.reply_text("⚠️ Fiyat şu an çekilemiyor, lütfen tekrar deneyin.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/ciz komutu"""
    prompt = " ".join(context.args)
    if not prompt:
        return await update.message.reply_text("❌ Kullanım: `/ciz uzayda bir canavar` ")
    
    await update.message.reply_text("🎨 Irvus AI senin için çiziyor...")
    
    # Pollinations AI görsel linki
    image_url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?seed={int(time.time())}"
    
    await update.message.reply_photo(
        photo=image_url, 
        caption=f"🖼 **Görsel:** `{prompt}`"
    )

# --- 5. ÇALIŞTIRICI ---
def run_web():
    # Render PORT ayarı
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Flask sunucusunu ayrı bir kolda başlatıyoruz
    Thread(target=run_web, daemon=True).start()

    # Botu yeni token ile ayağa kaldırıyoruz
    bot = ApplicationBuilder().token(TOKEN).build()

    # Komutları kaydediyoruz
    bot.add_handler(CommandHandler(["start", "star"], start))
    bot.add_handler(CommandHandler("fiyat", fiyat))
    bot.add_handler(CommandHandler("ciz", ciz))

    print(">>> IRVUS BOT YENİ TOKEN İLE AKTİF")
    
    # Botu çalıştırırken bekleyen eski mesajları siliyoruz (Çakışma önleyici)
    bot.run_polling(drop_pending_updates=True)
    
