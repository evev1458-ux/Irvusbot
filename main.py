import os, asyncio, time, requests, aiohttp
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib.parse import quote

# --- 1. WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS GLOBAL AI IS RUNNING", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAHEpgqJYNNGXyon1I855vghWfkQ8p-4tlk"
CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
LOGO = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"
WEB_URL = "https://www.irvustoken.xyz"
TWITTER_URL = "https://x.com/IRVUSTOKEN"

# --- 3. GÜNCEL AI MOTORU (HATA VERMEYEN MODEL) ---
async def ask_ai(question):
    try:
        # Hata veren 'search' yerine en stabil 'openai' modeline geçtik
        ai_url = f"https://text.pollinations.ai/{quote(question)}?model=openai&cache={int(time.time())}"
        async with aiohttp.ClientSession() as session:
            async with session.get(ai_url, timeout=15) as resp:
                if resp.status == 200:
                    return await resp.text()
                else:
                    return "Şu an global sistemde bir bakım var, lütfen birazdan tekrar sor."
    except:
        return "Bağlantı hatası. Tekrar deneyebilir misin?"

# --- 4. KOMUTLAR ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Butonlar ve Logo (Hata Korumalı)"""
    msg = (f"💎 **IRVUS GLOBAL AI SİSTEMİ**\n\n"
           f"🤖 **Bana her şeyi sorabilirsin!**\n"
           f"Kullanım: `/sor naber?` \n\n"
           f"📄 **CA:** `{CA}`")
    
    # Eksik olan Web Sitesi butonu eklendi
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
    """Fiyatı en garantili yoldan çekiyoruz"""
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/pairs/base/{CA}", timeout=5).json()
        if 'pair' in r:
            p = r['pair']['priceUsd']
            await update.message.reply_text(f"💰 **Güncel Fiyat:** `${p}`")
        else:
            await update.message.reply_text("⚠️ Fiyat verisi şu an DexScreener'da güncelleniyor.")
    except:
        await update.message.reply_text("⚠️ Bağlantı hatası, lütfen tekrar deneyin.")

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
        print(">>> SİSTEM TERTEMİZ BAŞLADI!")
        await application.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
    
