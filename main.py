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
# Logo linkini garantilemek için doğrudan GitHub'dan güncelledim
LOGO = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"

# --- 3. AI FONKSİYONU ---
async def ask_live_ai(question):
    try:
        # İnternet tarama özellikli model
        ai_url = f"https://text.pollinations.ai/{quote(question)}?model=search"
        async with aiohttp.ClientSession() as session:
            async with session.get(ai_url, timeout=25) as resp:
                return await resp.text()
    except:
        return "Bağlantıda bir sorun var, lütfen tekrar sorar mısın?"

# --- 4. KOMUTLAR (HATA KORUMALI) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Resim hatalı olsa bile butonlar her zaman gider"""
    msg = (f"💎 **IRVUS GLOBAL AI SİSTEMİ**\n\n"
           f"🌍 **Her şeyi biliyorum!**\n"
           f"Örnek: `/sor İran ABD son durum ne?` \n\n"
           f"📄 **CA:** `{CA}`")
    
    kb = [[InlineKeyboardButton("🐦 Twitter (X)", url="https://x.com/IRVUSTOKEN")]]
    reply_markup = InlineKeyboardMarkup(kb)

    try:
        # Önce resimli dene
        await update.message.reply_photo(photo=LOGO, caption=msg, reply_markup=reply_markup, parse_mode='Markdown')
    except Exception:
        # Resim hata verirse sadece metni gönder (Botun donmasını engeller)
        await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode='Markdown')

async def sor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        return await update.message.reply_text("🤖 Bir şey sor! Örnek: `/sor naber?` ")
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    answer = await ask_live_ai(query)
    await update.message.reply_text(f"🤖 **Irvus AI:**\n\n{answer}")

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/pairs/base/{CA}", timeout=5).json()
        await update.message.reply_text(f"💰 **Fiyat:** `${r['pair']['priceUsd']}`")
    except:
        await update.message.reply_text("⚠️ Fiyat yoğunluğu var.")

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
        print(">>> SİSTEM HAZIR!")
        await application.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
    
