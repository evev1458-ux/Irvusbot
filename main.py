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
def home(): return "IRVUS MULTI-LANG: ACTIVE", 200

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAHnY8zSX9VUhD3bm-v44sHaMWzxVWzq0_c"
CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
LOGO = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"

# --- 3. HABER MOTORU ---
def get_live_news(query):
    try:
        url = f"https://news.google.com/rss/search?q={quote(query)}&hl=tr&gl=TR&ceid=TR:tr"
        r = requests.get(url, timeout=10)
        root = ET.fromstring(r.content)
        headlines = [item.find('title').text for item in root.findall('.//item')[:3]]
        return " | ".join(headlines) if headlines else "No news found."
    except: return "Busy."

# --- 4. KOMUTLAR ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (f"💎 **IRVUS GLOBAL AI (2026)**\n\n"
           f"🇹🇷 Hoş geldiniz! Sorularınızı sorabilirsiniz.\n"
           f"🇺🇸 Welcome! You can ask your questions.\n\n"
           f"📄 CA: `{CA}`")
    kb = [
        [InlineKeyboardButton("🌐 Website", url="https://www.irvustoken.xyz")],
        [InlineKeyboardButton("🐦 Twitter (X)", url="https://x.com/IRVUSTOKEN")]
    ]
    try:
        await update.message.reply_photo(photo=LOGO, caption=msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    except:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def ask_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dil korumalı /sor & /ask komutu"""
    query = " ".join(context.args)
    if not query: 
        return await update.message.reply_text("🇹🇷 Bir soru yazın. / 🇺🇸 Write a question.")
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # İnternetten güncel veriyi çekiyoruz
    live_info = get_live_news(query)
    
    # DİL KONTROLÜ VE TALİMATI (Burayı sertleştirdim)
    # AI'ya sorunun dili neyse o dilde cevap vermesini KESİN olarak emrediyoruz.
    prompt = (f"SYSTEM INSTRUCTION: You are Irvus AI. Current date is April 8, 2026. "
              f"CRITICAL: If the user asks in Turkish, you MUST answer in Turkish. "
              f"If the user asks in English, you MUST answer in English. "
              f"Latest info: {live_info}. User Question: {query}")
    
    try:
        url = f"https://text.pollinations.ai/{quote(prompt)}?model=openai"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=25) as r:
                ans = await r.text()
                await update.message.reply_text(f"🤖 **Irvus AI:**\n\n{ans}")
    except: 
        await update.message.reply_text("Sistem yoğun, tekrar deneyin. / System busy, try again.")

async def price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        url = f"https://api.geckoterminal.com/api/v2/networks/base/tokens/{CA}"
        r = requests.get(url, timeout=10).json()
        p = r['data']['attributes']['price_usd']
        await update.message.reply_text(f"💰 **$IRVUS:** `${float(p):.8f}`")
    except:
        await update.message.reply_text("⚠️ Fiyat çekilemedi. / Price unavailable.")

async def draw_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = " ".join(context.args)
    if not p: return await update.message.reply_text("❌ /draw <prompt>")
    await update.message.reply_text("🎨 Processing / Çiziliyor...")
    img = f"https://image.pollinations.ai/prompt/{quote(p)}?seed={int(time.time())}"
    await update.message.reply_photo(photo=img, caption=f"🖼 `{p}`")

# --- 5. ANA ÇALIŞTIRICI ---
async def main():
    Thread(target=run_web, daemon=True).start()
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler(["start", "star"], start))
    application.add_handler(CommandHandler(["sor", "ask"], ask_cmd))
    application.add_handler(CommandHandler(["fiyat", "price"], price_cmd))
    application.add_handler(CommandHandler(["ciz", "draw"], draw_cmd))

    async with application:
        await application.initialize()
        await application.start()
        print(">>> IRVUS GLOBAL READY")
        await application.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    try: asyncio.run(main())
    except: pass

    
