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
# Logo linkini doğrudan GitHub raw üzerinden güncelledim
LOGO = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"

# --- 3. KOMUTLAR ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Butonları ve logoyu her koşulda gönderir"""
    msg = (f"💎 **IRVUS TOKEN DÜNYASI**\n\n"
           f"📄 **Sözleşme Adresi (CA):**\n`{CA}`")
    
    kb = [[
        InlineKeyboardButton("🌐 Web Sitesi", url="https://www.irvustoken.xyz"),
        InlineKeyboardButton("📊 Grafik", url=f"https://dexscreener.com/base/{CA}")
    ]]
    
    try:
        # Fotoğraf gönderilemezse sadece metin gönderir (Hata koruması)
        await update.message.reply_photo(
            photo=LOGO,
            caption=msg,
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode='Markdown'
        )
    except:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fiyat çekme işlemini daha dayanıklı hale getirdik"""
    try:
        # User-Agent ekleyerek DexScreener bloklamasını aşmaya çalışıyoruz
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = f"https://api.dexscreener.com/latest/dex/pairs/base/{CA}"
        r = requests.get(url, headers=headers, timeout=10).json()
        
        if 'pair' in r:
            p = r['pair']['priceUsd']
            mcap = float(r['pair'].get('fdv', 0)) / 1000
            await update.message.reply_text(f"💰 **Güncel Fiyat:** `${p}`\n📊 **Market Cap:** `${mcap:.1f}K`")
        else:
            await update.message.reply_text("⚠️ Fiyat verisi şu an hazır değil, lütfen 1 dk sonra deneyin.")
    except Exception as e:
        await update.message.reply_text("⚠️ DexScreener şu an yoğun, grafikten bakabilirsiniz.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Çizim zaten çalışıyor, dokunmadık"""
    prompt = " ".join(context.args)
    if not prompt: return await update.message.reply_text("❌ Örnek: `/ciz aslan` ")
    
    await update.message.reply_text("🎨 Irvus AI senin için çiziyor...")
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
    
    print(">>> IRVUS BOT HAZIR!")
    application.run_polling(drop_pending_updates=True)
    
