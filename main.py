import os, asyncio, time, requests, aiohttp
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib.parse import quote

# --- 1. WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS 2026 SYSTEM: ACTIVE", 200

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAFP8Pmc0p24oQnDEiL6SwMTgL6tr3HIPss"
CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
LOGO = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"

# --- 3. GERÇEK ZAMANLI AI (2026 ZORLAMALI) ---
async def ask_ai_2026(question):
    try:
        # Tarihi ve konumu zorlayan, internet arama motoru destekli model
        prompt = f"Şu an tarih 8 Nisan 2026. Lütfen 2026 yılındaki güncel haberleri, puan durumlarını ve olayları baz alarak cevap ver: {question}"
        ai_url = f"https://text.pollinations.ai/{quote(prompt)}?model=openai&cache={int(time.time())}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(ai_url, timeout=25) as resp:
                if resp.status == 200:
                    return await resp.text()
                return "AI sistemi şu an meşgul, lütfen tekrar dene."
    except:
        return "Bağlantı hatası oluştu."

# --- 4. GÜÇLENDİRİLMİŞ FİYAT ÇEKİCİ (GECKOTERMINAL) ---
def get_crypto_price():
    try:
        # DexScreener yerine daha stabil olan GeckoTerminal API'si kullanıyoruz
        url = f"https://api.geckoterminal.com/api/v2/networks/base/tokens/{CA}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10).json()
        return r['data']['attributes']['price_usd']
    except:
        try:
            # Yedek: DexScreener
            url2 = f"https://api.dexscreener.com/latest/dex/pairs/base/{CA}"
            r2 = requests.get(url2, headers=headers, timeout=10).json()
            return r2['pair']['priceUsd']
        except:
            return None

# --- 5. KOMUTLAR ---

async def start(update, context):
    msg = f"💎 **IRVUS GLOBAL AI (2026)**\n\nGüncel haberler ve anlık fiyat takibi aktif.\n📄 **CA:** `{CA}`"
    kb = [[InlineKeyboardButton("🐦 Twitter (X)", url="https://x.com/IRVUSTOKEN")]]
    await update.message.reply_photo(photo=LOGO, caption=msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def sor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query: return await update.message.reply_text("🤖 Bana güncel bir soru sor!")
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    answer = await ask_ai_2026(query)
    await update.message.reply_text(f"🤖 **Irvus AI:**\n\n{answer}")

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = get_crypto_price()
    if p:
        await update.message.reply_text(f"💰 **Güncel Fiyat ($IRVUS):** `${float(p):.10f}`")
    else:
        await update.message.reply_text("⚠️ Fiyat şu an çekilemiyor. Grafikten bakmayı deneyin.")

# --- 6. BAŞLAT ---
async def main():
    Thread(target=run_web, daemon=True).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    
    app_bot.add_handler(CommandHandler(["start", "star"], start))
    app_bot.add_handler(CommandHandler("sor", sor))
    app_bot.add_handler(CommandHandler("fiyat", fiyat))

    async with app_bot:
        await app_bot.initialize()
        await app_bot.start()
        print(">>> 2026 FIX AKTIF")
        await app_bot.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    try: asyncio.run(main())
    except: pass
        
