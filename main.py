import os, asyncio, time, requests, aiohttp
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib.parse import quote

# --- 1. WEB SUNUCUSU (Render'ı Uyanık Tutmak İçin) ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS BOT: ACTIVE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAFP8Pmc0p24oQnDEiL6SwMTgL6tr3HIPss"
CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
LOGO = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"
TWITTER_URL = "https://x.com/IRVUSTOKEN"
WEB_URL = "https://www.irvustoken.xyz"

# --- 3. AKILLI AI VE FİYAT FONKSİYONLARI ---
async def ask_ai(question):
    try:
        # Hata vermeyen en stabil global model
        ai_url = f"https://text.pollinations.ai/{quote(question)}?model=openai"
        async with aiohttp.ClientSession() as session:
            async with session.get(ai_url, timeout=15) as resp:
                return await resp.text()
    except:
        return "Şu an global ağda bir yoğunluk var, lütfen az sonra tekrar sor."

async def get_price():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = f"https://api.dexscreener.com/latest/dex/pairs/base/{CA}"
        r = requests.get(url, headers=headers, timeout=5).json()
        return r['pair']['priceUsd'] if 'pair' in r else None
    except:
        return None

# --- 4. KOMUTLAR ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Butonları ve logoyu garantili şekilde gönderir"""
    msg = (f"💎 **IRVUS GLOBAL AI SİSTEMİ**\n\n"
           f"🤖 **Bana istediğin her şeyi sorabilirsin!**\n"
           f"Kullanım: `/sor Fenerbahçe şampiyon olur mu?` \n\n"
           f"📄 **CA:** `{CA}`")
    
    kb = [
        [InlineKeyboardButton("🌐 Web Sitesi", url=WEB_URL)],
        [InlineKeyboardButton("🐦 Twitter (X)", url=TWITTER_URL)]
    ]
    reply_markup = InlineKeyboardMarkup(kb)

    try:
        await update.message.reply_photo(photo=LOGO, caption=msg, reply_markup=reply_markup, parse_mode='Markdown')
    except:
        await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode='Markdown')

async def sor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query: return await update.message.reply_text("🤖 Bir şey sor! Örnek: `/sor naber?` ")
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    answer = await ask_ai(query)
    await update.message.reply_text(f"🤖 **Irvus AI:**\n\n{answer}")

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = await get_price()
    if p: await update.message.reply_text(f"💰 **Güncel Fiyat:** `${p}`")
    else: await update.message.reply_text("⚠️ DexScreener yoğun, lütfen az sonra tekrar deneyin.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = " ".join(context.args)
    if not p: return await update.message.reply_text("❌ Örnek: `/ciz kedi` ")
    await update.message.reply_text("🎨 Irvus AI senin için çiziyor...")
    img = f"https://image.pollinations.ai/prompt/{quote(p)}?seed={int(time.time())}"
    await update.message.reply_photo(photo=img, caption=f"🖼 **Görsel:** `{p}`")

# --- 5. ANA ÇALIŞTIRICI ---
async def main():
    Thread(target=run_web, daemon=True).start()
    
    # drop_pending_updates=True eski çatışmaları temizlemek için kritiktir
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler(["start", "star"], start))
    application.add_handler(CommandHandler("sor", sor))
    application.add_handler(CommandHandler("fiyat", fiyat))
    application.add_handler(CommandHandler("ciz", ciz))

    async with application:
        await application.initialize()
        await application.start()
        print(">>> SİSTEM YENİ TOKEN İLE BAŞLADI!")
        await application.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except:
        pass
        
