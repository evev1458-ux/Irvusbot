import os, asyncio, time, requests, aiohttp
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib.parse import quote

# --- 1. WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS BOT ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAHEpgqJYNNGXyon1I855vghWfkQ8p-4tlk"
CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
LOGO = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"
WEB_URL = "https://www.irvustoken.xyz"
TWITTER_URL = "https://x.com/IRVUSTOKEN"

# --- 3. GÜVENLİ FİYAT VE AI ---
async def get_price():
    try:
        # DexScreener API
        url = f"https://api.dexscreener.com/latest/dex/pairs/base/{CA}"
        r = requests.get(url, timeout=5).json()
        if 'pair' in r:
            return r['pair']['priceUsd']
        return None
    except:
        return None

async def ask_ai(question):
    try:
        # Hata vermeyen stabil model
        url = f"https://text.pollinations.ai/{quote(question)}?model=gpt-4o-mini"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as resp:
                return await resp.text()
    except:
        return "Şu an cevap veremiyorum, lütfen tekrar dene."

# --- 4. KOMUTLAR ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Butonları alt alta ve garanti görünecek şekilde ayarlar"""
    msg = (f"💎 **IRVUS GLOBAL AI SİSTEMİ**\n\n"
           f"🤖 **Her türlü soruyu sorabilirsin!**\n"
           f"Kullanım: `/sor Fenerbahçe'nin durumu ne?` \n\n"
           f"📄 **CA:** `{CA}`")
    
    # Buton listesini en sağlam formatta (liste içinde liste) tanımladık
    keyboard = [
        [InlineKeyboardButton("🌐 Web Sitesi", url=WEB_URL)],
        [InlineKeyboardButton("🐦 Twitter (X)", url=TWITTER_URL)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await update.message.reply_photo(photo=LOGO, caption=msg, reply_markup=reply_markup, parse_mode='Markdown')
    except:
        # Resim atılamazsa mesajı butonsuz bırakmaz, metin olarak atar
        await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode='Markdown')

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = await get_price()
    if p:
        await update.message.reply_text(f"💰 **Güncel Fiyat:** `${p}`")
    else:
        await update.message.reply_text("⚠️ Fiyat verisi çekilemedi. DexScreener şu an yoğun olabilir.")

async def sor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        return await update.message.reply_text("🤖 Lütfen sorunu yaz! Örnek: `/sor naber?` ")
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    answer = await ask_ai(query)
    await update.message.reply_text(f"🤖 **Irvus AI:**\n\n{answer}")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = " ".join(context.args)
    if not p: return await update.message.reply_text("❌ Örnek: `/ciz kedi` ")
    await update.message.reply_text("🎨 Çiziliyor...")
    img = f"https://image.pollinations.ai/prompt/{quote(p)}?seed={int(time.time())}"
    await update.message.reply_photo(photo=img, caption=f"🖼 `{p}`")

# --- 5. ANA ÇALIŞTIRICI ---
async def main():
    Thread(target=run_web, daemon=True).start()
    
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler(["start", "star"], start))
    application.add_handler(CommandHandler("sor", sor))
    application.add_handler(CommandHandler("fiyat", fiyat))
    application.add_handler(CommandHandler("ciz", ciz))

    async with application:
        await application.initialize()
        await application.start()
        print(">>> BOT HAZIR!")
        await application.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
    
