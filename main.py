import os, asyncio, time, requests
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib.parse import quote

# --- 1. WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS POWER: ON", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAFP8Pmc0p24oQnDEiL6SwMTgL6tr3HIPss"
CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
LOGO = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"

# --- 3. AKILLI AI (GÜNCEL VE HATASIZ) ---
async def ask_ai_fixed(question):
    try:
        # Engel yemeyen gpt-4o-mini tabanlı motor
        url = f"https://text.pollinations.ai/{quote(question)}?model=openai&system=Sen+Irvus+AI+asistanisin.+Bugun+8+Nisan+2026.+Guncel+olaylari+ve+spor+haberlerini+internet+uzerinden+tara+ve+cevapla."
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            return r.text
        return "Şu an global bir yoğunluk var, lütfen az sonra tekrar sor."
    except:
        return "Bağlantı kurulamadı, lütfen tekrar dene."

# --- 4. GÜVENLİ FİYAT ÇEKİCİ ---
def get_safe_price():
    try:
        # DexScreener yerine daha az engel koyan GeckoTerminal API'si
        url = f"https://api.geckoterminal.com/api/v2/networks/base/tokens/{CA}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10).json()
        return r['data']['attributes']['price_usd']
    except:
        return None

# --- 5. KOMUTLAR ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = f"💎 **IRVUS GLOBAL AI (2026)**\n\nGüncel haberler, sanat ve fiyat takibi aktif.\n📄 **CA:** `{CA}`"
    kb = [
        [InlineKeyboardButton("🌐 Web Sitesi", url="https://www.irvustoken.xyz")],
        [InlineKeyboardButton("🐦 Twitter (X)", url="https://x.com/IRVUSTOKEN")]
    ]
    try:
        await update.message.reply_photo(photo=LOGO, caption=msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    except:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def sor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query: return await update.message.reply_text("🤖 Bana bir şey sor!")
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    ans = await ask_ai_fixed(query)
    await update.message.reply_text(f"🤖 **Irvus AI:**\n\n{ans}")

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = get_safe_price()
    if p:
        await update.message.reply_text(f"💰 **Güncel $IRVUS Fiyatı:** `${float(p):.10f}`")
    else:
        await update.message.reply_text("⚠️ Fiyat verisi şu an çekilemiyor. Grafikten kontrol edin.")

# --- 6. ÇALIŞTIRICI ---
async def main():
    Thread(target=run_web, daemon=True).start()
    
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler(["start", "star"], start))
    application.add_handler(CommandHandler("sor", sor))
    application.add_handler(CommandHandler("fiyat", fiyat))

    async with application:
        await application.initialize()
        await application.start()
        print(">>> SİSTEM TÜM ENGELLERİ AŞARAK BAŞLATILDI!")
        await application.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except:
        pass
        
