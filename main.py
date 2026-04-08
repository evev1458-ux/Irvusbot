import os, asyncio, time, requests, aiohttp
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib.parse import quote

# --- 1. WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS LIVE AI 2026 ONLINE", 200

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAFP8Pmc0p24oQnDEiL6SwMTgL6tr3HIPss"
CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
LOGO = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"

# --- 3. 2026 GÜNCEL VERİ ÇEKEN AI MOTORU ---
async def ask_live_ai(question):
    """2026 internet verilerine canlı erişen AI motoru"""
    try:
        # 'search' ve '2026' bağlamını zorlayarak güncel veri alıyoruz
        # Pollinations üzerinden en güncel arama modelini tetikliyoruz
        ai_url = f"https://text.pollinations.ai/{quote(question)}?model=search&cache={int(time.time())}"
        async with aiohttp.ClientSession() as session:
            async with session.get(ai_url, timeout=25) as resp:
                if resp.status == 200:
                    return await resp.text()
                return "Şu an haber kaynaklarına ulaşamıyorum, lütfen birazdan tekrar dene."
    except:
        return "Bağlantı hatası oluştu. Lütfen tekrar sorar mısın?"

# --- 4. KOMUTLAR ---

async def start(update, context):
    msg = (f"💎 **IRVUS GÜNCEL AI (2026)**\n\n"
           f"🌍 **Artık tamamen güncelim!**\n"
           f"Bana 2026 yılındaki maçları, fiyatları veya siyaseti sorabilirsin.\n\n"
           f"📄 **CA:** `{CA}`")
    kb = [[InlineKeyboardButton("🐦 Twitter (X)", url="https://x.com/IRVUSTOKEN")]]
    await update.message.reply_photo(photo=LOGO, caption=msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def sor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        return await update.message.reply_text("🤖 Lütfen güncel bir soru sor!")
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # AI'ya güncel olduğunu hatırlatan bir ekleme yapıyoruz
    prompt = f"Şu an tarih 8 Nisan 2026. Lütfen bu tarihi baz alarak ve internetteki güncel haberleri tarayarak cevap ver: {query}"
    answer = await ask_live_ai(prompt)
    
    await update.message.reply_text(f"🤖 **Irvus Güncel AI:**\n\n{answer}")

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """DexScreener bazen bloklayabilir, hata yönetimi eklendi"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = f"https://api.dexscreener.com/latest/dex/pairs/base/{CA}"
        r = requests.get(url, headers=headers, timeout=10).json()
        if 'pair' in r:
            await update.message.reply_text(f"💰 **Güncel Fiyat:** `${r['pair']['priceUsd']}`")
        else:
            await update.message.reply_text("⚠️ Fiyat şu an çekilemiyor (DexScreener yoğun).")
    except:
        await update.message.reply_text("⚠️ DexScreener bağlantısı kurulamadı.")

# --- 5. ANA ÇALIŞTIRICI ---
async def main():
    Thread(target=run_web, daemon=True).start()
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler(["start", "star"], start))
    application.add_handler(CommandHandler("sor", sor))
    application.add_handler(CommandHandler("fiyat", fiyat))

    async with application:
        await application.initialize()
        await application.start()
        print(">>> 2026 GÜNCEL SİSTEM AKTİF")
        await application.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    try: asyncio.run(main())
    except: pass
    
