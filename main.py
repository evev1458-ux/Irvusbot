import os, asyncio, requests, time, aiohttp
import xml.etree.ElementTree as ET
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib.parse import quote

# --- 1. WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS GLOBAL SYSTEM: ONLINE", 200

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAFP8Pmc0p24oQnDEiL6SwMTgL6tr3HIPss"
CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
LOGO = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"

# --- 3. GLOBAL HABER VE FİYAT MOTORU ---
def get_live_news(query):
    try:
        # Global haberler için İngilizce ve Türkçe kaynakları tarar
        url = f"https://news.google.com/rss/search?q={quote(query)}&hl=en-US&gl=US&ceid=US:en"
        r = requests.get(url, timeout=10)
        root = ET.fromstring(r.content)
        headlines = [item.find('title').text for item in root.findall('.//item')[:3]]
        return " | ".join(headlines) if headlines else "No recent news found."
    except: return "News source busy."

async def get_crypto_price():
    try:
        url = f"https://api.geckoterminal.com/api/v2/networks/base/tokens/{CA}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as r:
                data = await r.json()
                return data['data']['attributes']['price_usd']
    except: return None

# --- 4. KOMUTLAR (TR/EN DESTEKLİ) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (f"💎 **IRVUS GLOBAL AI (2026)**\n\n"
           f"🇹🇷 **Bana her şeyi sorabilirsin!**\n"
           f"🇺🇸 **You can ask me anything!**\n\n"
           f"📄 **CA:** `{CA}`")
    
    kb = [
        [InlineKeyboardButton("🌐 Website", url="https://www.irvustoken.xyz")],
        [InlineKeyboardButton("🐦 Twitter (X)", url="https://x.com/IRVUSTOKEN")]
    ]
    await update.message.reply_photo(photo=LOGO, caption=msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def sor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query: 
        return await update.message.reply_text("🇹🇷 Lütfen bir soru yazın.\n🇺🇸 Please write a question.")
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # Canlı veri desteği
    live_info = get_live_news(query)
    
    # AI'ya çift dilli ve 2026 odaklı talimat veriyoruz
    prompt = (f"Current date: April 8, 2026. Latest news: {live_info}. "
              f"If the user asks in Turkish, answer in Turkish. If English, answer in English. "
              f"Question: {query}")
    
    try:
        url = f"https://text.pollinations.ai/{quote(prompt)}?model=openai"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=25) as r:
                ans = await r.text()
                await update.message.reply_text(f"🤖 **Irvus Global AI:**\n\n{ans}")
    except: 
        await update.message.reply_text("❌ System busy / Sistem yoğun.")

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = await get_crypto_price()
    if p:
        await update.message.reply_text(f"💰 **$IRVUS Price/Fiyat:** `${float(p):.8f}`")
    else:
        await update.message.reply_text("⚠️ Price unavailable / Fiyat çekilemedi.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = " ".join(context.args)
    if not p: return await update.message.reply_text("❌ /ciz <prompt>")
    await update.message.reply_text("🎨 Drawing/Çiziliyor...")
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
        print(">>> GLOBAL MULTI-LANG SYSTEM ACTIVE")
        await application.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    try: asyncio.run(main())
    except: pass
        
