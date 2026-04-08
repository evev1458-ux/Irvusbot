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
def home(): return "IRVUS POWER SYSTEM: ONLINE", 200

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAFP8Pmc0p24oQnDEiL6SwMTgL6tr3HIPss"
CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
LOGO = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"

# --- 3. HABER VE FİYAT ÇEKİCİLER ---
def get_live_news(query):
    try:
        url = f"https://news.google.com/rss/search?q={quote(query)}&hl=tr&gl=TR&ceid=TR:tr"
        r = requests.get(url, timeout=10)
        root = ET.fromstring(r.content)
        headlines = [item.find('title').text for item in root.findall('.//item')[:3]]
        return " | ".join(headlines) if headlines else "Güncel haber bulunamadı."
    except: return "Haber kaynağı yoğun."

async def get_crypto_price():
    try:
        url = f"https://api.geckoterminal.com/api/v2/networks/base/tokens/{CA}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as r:
                data = await r.json()
                return data['data']['attributes']['price_usd']
    except: return None

# --- 4. KOMUTLAR ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start komutu ve butonlar geri geldi!"""
    msg = (f"💎 **IRVUS GLOBAL AI (2026)**\n\n"
           f"🤖 **2026 Haberleri, Fiyat ve Çizim aktif!**\n\n"
           f"📄 **CA:** `{CA}`")
    kb = [
        [InlineKeyboardButton("🌐 Web Sitesi", url="https://www.irvustoken.xyz")],
        [InlineKeyboardButton("🐦 Twitter (X)", url="https://x.com/IRVUSTOKEN")]
    ]
    await update.message.reply_photo(photo=LOGO, caption=msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def sor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query: return await update.message.reply_text("🤖 Ne sormak istersin?")
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # Gerçek zamanlı haberlerle AI'yı besliyoruz
    live_data = get_live_news(query)
    prompt = f"Bugün 8 Nisan 2026. İnternetteki en son veriler: {live_data}. Soru: {query}"
    
    try:
        url = f"https://text.pollinations.ai/{quote(prompt)}?model=openai"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=20) as r:
                ans = await r.text()
                await update.message.reply_text(f"🤖 **Irvus AI:**\n\n{ans}")
    except: await update.message.reply_text("❌ Yanıt alınamadı.")

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = await get_crypto_price()
    if p: await update.message.reply_text(f"💰 **Fiyat:** `${float(p):.8f}`")
    else: await update.message.reply_text("⚠️ Fiyat şu an çekilemiyor.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = " ".join(context.args)
    if not p: return await update.message.reply_text("❌ Örnek: /ciz aslan")
    await update.message.reply_text("🎨 Çiziliyor...")
    img = f"https://image.pollinations.ai/prompt/{quote(p)}?seed={int(time.time())}"
    await update.message.reply_photo(photo=img, caption=f"🖼 `{p}`")

# --- 5. ANA ÇALIŞTIRICI ---
async def main():
    Thread(target=run_web, daemon=True).start()
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Tüm komutları tek tek ekledik
    application.add_handler(CommandHandler(["start", "star"], start))
    application.add_handler(CommandHandler("sor", sor))
    application.add_handler(CommandHandler("fiyat", fiyat))
    application.add_handler(CommandHandler("ciz", ciz))

    async with application:
        await application.initialize()
        await application.start()
        print(">>> SİSTEM 2026 MODUNDA AKTİF")
        await application.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    try: asyncio.run(main())
    except: pass
        
