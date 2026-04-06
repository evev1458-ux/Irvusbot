import os, requests, asyncio, time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS AI ONLINE", 200

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAESXIZLT6HbS3CGeT-sT-HJcgvFuJF8ff0" 
CA_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
HF_TOKEN = "Hf_VzFKUkIElGkRTDWwEwLPwPPOOmwWwwBqNq"

# HIZLI VE ZEKİ MODEL (Gemma)
CHAT_MODEL = "https://api-inference.huggingface.co/models/google/gemma-1.1-7b-it"
IMAGE_MODEL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"

X_ADRESI = "https://x.com/IRVUSTOKEN"
WEB_SITESI = "https://www.irvustoken.xyz"
LOGO_URL = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg" 

HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}
LAST_PRICE_DATA = {"price": "0.00", "change": "0", "time": 0}

# --- 3. SOHBET FONKSİYONU ---

async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    user_text = update.message.text
    
    is_reply = update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id
    if "irvus" in user_text.lower() or is_reply:
        try:
            # Gemma için özel prompt (Türkçe cevap vermesini sağlıyoruz)
            prompt = f"Sen Irvus Token projesinin zeki yapay zekasısın. Türkçe, kısa ve samimi cevap ver: {user_text}"
            res = requests.post(CHAT_MODEL, headers=HEADERS, json={"inputs": prompt}, timeout=15).json()
            
            # Yanıtı al
            bot_response = res[0].get('generated_text', "").replace(prompt, "").strip()
            
            if not bot_response: bot_response = "Irvus her zaman burada! Gelecek bizimle başlıyor. 💎"
            await update.message.reply_text(f"🤖 **Irvus AI:** {bot_response}")
        except:
            await update.message.reply_text("💎 Irvus ile gelecek bugün başlıyor! Ne sormuştun?")

# --- 4. KOMUTLAR ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (f"💎 **Irvus AI Dünyasına Hoş Geldiniz!**\n\n"
           f"Ben Irvus AI. Bana her şeyi sorabilir, fiyat öğrenebilir veya hayallerini çizdirebilirsin.\n\n"
           f"📄 **CA:** `{CA_ADRESI}`\n\n"
           f"🚀 **Komutlar:**\n"
           f"🔹 `/fiyat` - Anlık veriler.\n"
           f"🔹 `/ciz [kelime]` - Görsel oluşturma.")
    
    kb = [[InlineKeyboardButton("🌐 Web Sitesi", url=WEB_SITESI), InlineKeyboardButton("🐦 X (Twitter)", url=X_ADRESI)],
          [InlineKeyboardButton("📊 Canlı Grafik (Base)", url=f"https://dexscreener.com/base/{CA_ADRESI}")]]
    
    try:
        await update.message.reply_photo(photo=LOGO_URL, caption=msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    except:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global LAST_PRICE_DATA
    if time.time() - LAST_PRICE_DATA["time"] < 90 and LAST_PRICE_DATA["price"] != "0.00":
        return await update.message.reply_text(f"💰 **Fiyat:** `${LAST_PRICE_DATA['price']}`\n📈 **24s:** `%{LAST_PRICE_DATA['change']}`")

    try:
        url = f"https://api.dexscreener.com/latest/dex/search?q={CA_ADRESI}"
        res = requests.get(url, headers={"User-Agent":"Mozilla"}, timeout=10).json()
        p = next((x for x in res.get('pairs', []) if x['chainId'] == 'base'), None)
        if p:
            LAST_PRICE_DATA = {"price": p['priceUsd'], "change": p['priceChange']['h24'], "time": time.time()}
            await update.message.reply_text(f"💰 **Fiyat:** `${p['priceUsd']}`\n📈 **24s:** `%{p['priceChange']['h24']}`")
    except:
        await update.message.reply_text("⚠️ API yoğun.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt: return await update.message.reply_text("❌ Örn: `/ciz uzayda bir aslan` ")
    await update.message.reply_text("🎨 Hayal ediyorum...")
    try:
        response = requests.post(IMAGE_MODEL, headers=HEADERS, json={"inputs": prompt}, timeout=30)
        await update.message.reply_photo(photo=response.content, caption=f"🖼 **Irvus AI:** {prompt}")
    except:
        await update.message.reply_text("❌ Çizim motoru meşgul.")

# --- 5. ANA MOTOR ---
async def main():
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    application.add_handler(CommandHandler(["ciz", "draw"], ciz))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat_ai))
    
    async with application:
        await application.initialize()
        await application.start()
        print(">>> IRVUS AI SISTEMI BASLADI")
        await application.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    try: asyncio.run(main())
    except: pass
