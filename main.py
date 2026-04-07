import os, asyncio, time, requests
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib.parse import quote

# --- 1. WEB ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS PRO ONLINE", 200

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAHEpgqJYNNGXyon1I855vghWfkQ8p-4tlk"
CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
LOGO = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"
TWITTER_URL = "https://x.com/irvus" # Burayı kendi Twitter adresinle değiştirebilirsin

# --- 3. KOMUTLAR ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Grafik yerine Twitter butonu eklendi"""
    msg = (f"💎 **IRVUS TOKEN DÜNYASI**\n\n"
           f"📄 **Sözleşme Adresi (CA):**\n`{CA}`")
    
    kb = [[
        InlineKeyboardButton("🌐 Web Sitesi", url="https://www.irvustoken.xyz"),
        InlineKeyboardButton("🐦 Twitter (X)", url=TWITTER_URL)
    ]]
    
    try:
        await update.message.reply_photo(
            photo=LOGO,
            caption=msg,
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode='Markdown'
        )
    except:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fiyat çekme hızı ve hata yönetimi artırıldı"""
    try:
        # Daha hızlı yanıt için timeout ve headers eklendi
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = f"https://api.dexscreener.com/latest/dex/pairs/base/{CA}"
        r = requests.get(url, headers=headers, timeout=5).json()
        
        if 'pair' in r:
            p = r['pair']['priceUsd']
            mcap = float(r['pair'].get('fdv', 0)) / 1000
            await update.message.reply_text(f"💰 **Güncel Fiyat:** `${p}`\n📊 **Market Cap:** `${mcap:.1f}K`")
        else:
            await update.message.reply_text("⚠️ Veri şu an hazır değil, lütfen az sonra tekrar deneyin.")
    except:
        await update.message.reply_text("⚠️ DexScreener şu an yoğun. Lütfen `/fiyat` komutunu tekrar gönderin.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt: return await update.message.reply_text("❌ Örnek: `/ciz aslan` ")
    
    await update.message.reply_text("🎨 Irvus AI senin için çiziyor...")
    img_url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?seed={int(time.time())}"
    await update.message.reply_photo(photo=img_url, caption=f"🖼 **Görsel:** `{prompt}`")

# --- 4. ÇALIŞTIRICI ---
def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    Thread(target=run_web, daemon=True).start()
    
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler(["start", "star"], start))
    application.add_handler(CommandHandler("fiyat", fiyat))
    application.add_handler(CommandHandler("ciz", ciz))
    
    print(">>> IRVUS BOT TÜM AYARLARLA HAZIR!")
    application.run_polling(drop_pending_updates=True)
    
