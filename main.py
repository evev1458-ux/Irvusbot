import os, asyncio, time, requests
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib.parse import quote

# --- 1. WEB ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS PRO ONLINE", 200

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAHEpgqJYNNGXyon1I855vghWfkQ8p-4tlk"
CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
LOGO = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"
# Twitter adresi büyük harflerle güncellendi
TWITTER_URL = "https://x.com/IRVUSTOKEN"

# --- 3. KOMUTLAR ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Twitter butonu büyük harf hassasiyetiyle eklendi"""
    msg = (f"💎 **IRVUS TOKEN DÜNYASI**\n\n"
           f"📄 **Sözleşme Adresi (CA):**\n`{CA}`")
    
    kb = [[
        InlineKeyboardButton("🌐 Web Sitesi", url="https://www.irvustoken.xyz"),
        InlineKeyboardButton("🐦 Twitter (X)", url=TWITTER_URL)
    ]]
    
    try:
        await update.message.reply_photo(
            photo=LOGO,
            caption=msg,
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode='Markdown'
        )
    except:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """DexScreener engelini aşmak için geliştirilmiş fiyat çekici"""
    try:
        # Gerçek bir tarayıcı gibi davranması için detaylı başlıklar (Headers)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Referer': 'https://dexscreener.com/'
        }
        url = f"https://api.dexscreener.com/latest/dex/pairs/base/{CA}"
        
        # Requests oturumu kullanarak daha stabil veri çekiyoruz
        with requests.Session() as session:
            r = session.get(url, headers=headers, timeout=10).json()
        
        if 'pair' in r:
            p = r['pair']['priceUsd']
            mcap = float(r['pair'].get('fdv', 0)) / 1000
            # Fiyatı daha belirgin göstermek için kalın yazım eklendi
            await update.message.reply_text(f"💰 **Fiyat:** `${p}`\n📊 **Market Cap:** `${mcap:.1f}K`")
        else:
            await update.message.reply_text("⚠️ Veri şu an DexScreener üzerinde güncelleniyor, lütfen tekrar deneyin.")
    except:
        await update.message.reply_text("⚠️ DexScreener şu an bot erişimini kısıtlıyor. Lütfen 1-2 dakika sonra tekrar `/fiyat` yazın.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt: return await update.message.reply_text("❌ Örnek: `/ciz aslan` ")
    
    await update.message.reply_text("🎨 Irvus AI çiziyor...")
    img_url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?seed={int(time.time())}"
    await update.message.reply_photo(photo=img_url, caption=f"🖼 **Görsel:** `{prompt}`")

# --- 4. ÇALIŞTIRICI ---
def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    Thread(target=run_web, daemon=True).start()
    
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler(["start", "star"], start))
    application.add_handler(CommandHandler("fiyat", fiyat))
    application.add_handler(CommandHandler("ciz", ciz))
    
    print(">>> IRVUS BOT SON AYARLARLA AKTİF!")
    application.run_polling(drop_pending_updates=True)
    
