import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS SISTEM ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- AYARLAR ---
TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
TOKEN_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
HF_TOKEN = "Hf_VzFKUkIElGkRTDWwEwLPwPPOOmwWwwBqNq"
HF_API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"

# --- FONKSİYONLAR ---
async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{TOKEN_ADRESI}", timeout=10).json()
        p = r['pairs'][0]
        msg = f"💎 **$IRVUS:** `${p.get('priceUsd')}`\n📈 24s: `%{p.get('priceChange', {}).get('h24')}`"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📈 Grafik", url=p.get('url'))]])
        await update.message.reply_text(msg, reply_markup=kb, parse_mode='Markdown')
    except:
        await update.message.reply_text("⚠️ Fiyat şu an yoğun, tekrar dene.")

async def ciz_islemi(update, prompt):
    try:
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        response = requests.post(HF_API_URL, headers=headers, json={"inputs": prompt}, timeout=30)
        if response.status_code == 200:
            await update.message.reply_photo(photo=response.content, caption=f"🖼 **Irvus AI:** {prompt}")
        else:
            url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?nologo=true"
            await update.message.reply_photo(photo=url, caption=f"🖼 **AI (Hızlı):** {prompt}")
    except:
        await update.message.reply_text("❌ Çizim motoru meşgul.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt: return await update.message.reply_text("❌ Örn: /ciz aslan")
    await update.message.reply_text(f"🎨 **'{prompt}'** hazırlanıyor...")
    asyncio.create_task(ciz_islemi(update, prompt))

# --- ANA MOTOR (BURASI DEĞİŞTİ) ---
async def main():
    # Flask'ı başlat
    Thread(target=run_web, daemon=True).start()
    
    # Botu kur
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    application.add_handler(CommandHandler(["ciz", "draw"], ciz))
    
    # Botu başlat
    async with application:
        await application.initialize()
        await application.start()
        print(">>> BOT AKTIF")
        await application.updater.start_polling(drop_pending_updates=True)
        # Botun sürekli çalışması için sonsuz döngü
        while True:
            await asyncio.sleep(3600)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
        
