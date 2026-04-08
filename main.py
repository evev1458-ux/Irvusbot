import os, asyncio, time, requests
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib.parse import quote

# --- 1. WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS 2026 LIVE", 200

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAFP8Pmc0p24oQnDEiL6SwMTgL6tr3HIPss"
CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
LOGO = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"

# --- 3. CANLI HABER VE AI MOTORU ---
async def ask_ai_2026(question):
    try:
        # Tarihi ve konumu netleştirerek internet taramasını tetikliyoruz
        # 'model=search' parametresi en güncel bilgiyi Google/Bing üzerinden tarar
        tarih_notu = "Bugun 8 Nisan 2026 Çarşamba. Lütfen internetteki en güncel haberleri ve verileri (hava durumu, puan durumu vb.) tarayarak cevap ver: "
        url = f"https://text.pollinations.ai/{quote(tarih_notu + question)}?model=search"
        
        # Zaman aşımını biraz artırdık çünkü interneti tarıyor
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            return r.text
        return "⚠️ Şu an canlı veri kaynaklarına ulaşamıyorum, lütfen tekrar dene."
    except:
        return "❌ Bağlantı hatası. Lütfen soruyu tekrar gönderir misin?"

# --- 4. GÜVENLİ FİYAT ---
def get_live_price():
    try:
        # GeckoTerminal daha stabil veri sağlar
        url = f"https://api.geckoterminal.com/api/v2/networks/base/tokens/{CA}"
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15).json()
        return r['data']['attributes']['price_usd']
    except:
        return None

# --- 5. KOMUTLAR ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = f"💎 **IRVUS GLOBAL AI (2026)**\n\nSistem tamamen güncellendi! Artık 2026 yılındaki tüm canlı verilere erişebiliyorum.\n\n📄 **CA:** `{CA}`"
    kb = [
        [InlineKeyboardButton("🌐 Web Sitesi", url="https://www.irvustoken.xyz")],
        [InlineKeyboardButton("🐦 Twitter (X)", url="https://x.com/IRVUSTOKEN")]
    ]
    await update.message.reply_photo(photo=LOGO, caption=msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def sor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query: return await update.message.reply_text("🤖 Ne sormak istersin? (Örn: /sor istanbul hava durumu)")
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    answer = await ask_ai_2026(query)
    await update.message.reply_text(f"🤖 **Irvus AI:**\n\n{answer}")

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = get_live_price()
    if p:
        await update.message.reply_text(f"💰 **Güncel $IRVUS Fiyatı:** `${float(p):.8f}`")
    else:
        await update.message.reply_text("⚠️ Fiyat şu an çekilemiyor, az sonra tekrar deneyin.")

# --- 6. BAŞLAT ---
async def main():
    Thread(target=run_web, daemon=True).start()
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler(["start", "star"], start))
    application.add_handler(CommandHandler("sor", sor))
    application.add_handler(CommandHandler("fiyat", fiyat))

    async with application:
        await application.initialize()
        await application.start()
        print(">>> IRVUS 2026 CANLI SİSTEM DEVREDE!")
        await application.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    try: asyncio.run(main())
    except: pass
        
