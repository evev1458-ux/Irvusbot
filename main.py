import os, time, requests
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib.parse import quote

# --- 1. WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS FIX ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAHEpgqJYNNGXyon1I855vghWfkQ8p-4tlk"
CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
LOGO = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"

# --- 3. KOMUTLAR ---

def start(update, context):
    msg = f"💎 **IRVUS GLOBAL AI**\n\nBana her şeyi sorabilirsin!\n📄 **CA:** `{CA}`"
    kb = [
        [InlineKeyboardButton("🌐 Web Sitesi", url="https://www.irvustoken.xyz")],
        [InlineKeyboardButton("🐦 Twitter (X)", url="https://x.com/IRVUSTOKEN")]
    ]
    try:
        update.message.reply_photo(photo=LOGO, caption=msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    except:
        update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

def fiyat(update, context):
    try:
        # User-agent ekleyerek bağlantı hatasını (403/500) aşıyoruz
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = f"https://api.dexscreener.com/latest/dex/pairs/base/{CA}"
        r = requests.get(url, headers=headers, timeout=10).json()
        if 'pair' in r:
            p = r['pair']['priceUsd']
            update.message.reply_text(f"💰 **Güncel Fiyat:** `${p}`")
        else:
            update.message.reply_text("⚠️ Fiyat şu an DexScreener'da hazır değil.")
    except:
        update.message.reply_text("⚠️ DexScreener bağlantı hatası verdi. Az sonra tekrar deneyin.")

def sor(update, context):
    query = " ".join(context.args)
    if not query:
        return update.message.reply_text("🤖 Lütfen bir soru yaz! Örnek: `/sor naber?` ")
    
    update.message.reply_text("🤔 Düşünüyorum...")
    try:
        # Hata veren 'search' parametresini tamamen sildik, en sade model:
        ai_url = f"https://text.pollinations.ai/{quote(query)}?model=openai"
        r = requests.get(ai_url, timeout=20)
        update.message.reply_text(f"🤖 **Irvus AI:**\n\n{r.text}")
    except:
        update.message.reply_text("⚠️ Yapay zeka şu an cevap veremiyor.")

def ciz(update, context):
    p = " ".join(context.args)
    if not p: return update.message.reply_text("❌ Örnek: `/ciz kedi` ")
    update.message.reply_text("🎨 Çiziliyor...")
    img = f"https://image.pollinations.ai/prompt/{quote(p)}?seed={int(time.time())}"
    update.message.reply_photo(photo=img, caption=f"🖼 `{p}`")

# --- 4. ANA ÇALIŞTIRICI ---
if __name__ == "__main__":
    Thread(target=run_web, daemon=True).start()
    
    # En stabil senkron (synchronous) yapıyı kuruyoruz
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler(["start", "star"], start))
    application.add_handler(CommandHandler("sor", sor))
    application.add_handler(CommandHandler("fiyat", fiyat))
    application.add_handler(CommandHandler("ciz", ciz))
    
    print(">>> BOT YAYINDA!")
    application.run_polling(drop_pending_updates=True)
    
