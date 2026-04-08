import os, asyncio, time, requests, aiohttp
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib.parse import quote

# --- 1. WEB SUNUCUSU (Render İçin) ---
app = Flask(__name__)
@app.route('/')
def home():
    return "IRVUS GLOBAL AI ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAHEpgqJYNNGXyon1I855vghWfkQ8p-4tlk"
CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
LOGO = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"
TWITTER_URL = "https://x.com/IRVUSTOKEN"

# --- 3. AKILLI AI FONKSİYONU ---
async def ask_global_ai(question):
    """Dünya çapında ne sorulursa cevap veren ücretsiz AI motoru"""
    try:
        # Pollinations AI motorunu kullanarak her türlü soruya cevap alıyoruz
        ai_url = f"https://text.pollinations.ai/{quote(question)}?model=openai"
        async with aiohttp.ClientSession() as session:
            async with session.get(ai_url, timeout=15) as resp:
                if resp.status == 200:
                    return await resp.text()
                else:
                    return "Şu an global ağda bir yoğunluk var, birazdan tekrar sorabilirsin."
    except:
        return "Bağlantım koptu, lütfen sorunu tekrar gönderir misin?"

# --- 4. KOMUTLAR ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Butonlu karşılama menüsü"""
    msg = (f"💎 **IRVUS GLOBAL AI SİSTEMİ**\n\n"
           f"🤖 **Bana her şeyi sorabilirsin!**\n"
           f"Kullanım: `/sor Fenerbahçe şampiyon olur mu?` veya `/sor naber?` \n\n"
           f"📄 **CA:** `{CA}`")
    
    kb = [[
        InlineKeyboardButton("🌐 Web Sitesi", url="https://www.irvustoken.xyz"),
        InlineKeyboardButton("🐦 Twitter (X)", url=TWITTER_URL)
    ]]
    
    await update.message.reply_photo(
        photo=LOGO,
        caption=msg,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode='Markdown'
    )

async def sor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yapay zeka soru-cevap komutu"""
    query = " ".join(context.args)
    if not query:
        return await update.message.reply_text("🤖 Bana bir şey sormadın! Örnek: `/sor piyasalar ne olur?` ")
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    answer = await ask_global_ai(query)
    
    await update.message.reply_text(f"🤖 **Irvus AI:**\n\n{answer}")

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Güncel fiyat çekme"""
    try:
        url = f"https://api.dexscreener.com/latest/dex/pairs/base/{CA}"
        r = requests.get(url, timeout=5).json()
        p = r['pair']['priceUsd']
        await update.message.reply_text(f"💰 **Güncel Fiyat:** `${p}`")
    except:
        await update.message.reply_text("⚠️ Fiyat şu an çekilemiyor, grafikten bakabilirsiniz.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """AI Görsel oluşturma"""
    prompt = " ".join(context.args)
    if not prompt:
        return await update.message.reply_text("❌ Örnek: `/ciz uzayda bir aslan` ")
    
    await update.message.reply_text("🎨 Irvus AI senin için çiziyor...")
    image_url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?seed={int(time.time())}"
    await update.message.reply_photo(photo=image_url, caption=f"🖼 **Görsel:** `{prompt}`")

# --- 5. ÇALIŞTIRICI ---
async def main():
    # Flask'ı uyanık tutması için başlat
    Thread(target=run_web, daemon=True).start()

    # Botu kur
    application = ApplicationBuilder().token(TOKEN).build()

    # Komutları kaydet
    application.add_handler(CommandHandler(["start", "star"], start))
    application.add_handler(CommandHandler("sor", sor))
    application.add_handler(CommandHandler("fiyat", fiyat))
    application.add_handler(CommandHandler("ciz", ciz))

    print(">>> IRVUS GLOBAL BOT AKTİF")
    
    async with application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling(drop_pending_updates=True)
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except:
        pass
        
