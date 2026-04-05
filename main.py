import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- WEB SUNUCUSU (Render için) ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS BOT ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- AYARLAR ---
# Yeni verdiğin Token'ı buraya ekledim
TOKEN = "8621050385:AAESXIZLT6HbS3CGeT-sT-HJcgvFuJF8ff0" 
TOKEN_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
HF_TOKEN = "Hf_VzFKUkIElGkRTDWwEwLPwPPOOmwWwwBqNq"
HF_API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"

# --- FONKSİYONLAR ---
async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{TOKEN_ADRESI}", timeout=10).json()
        p = r['pairs'][0]
        msg = (f"💎 **$IRVUS Güncel Durum**\n"
               f"━━━━━━━━━━━━━━━━━━\n"
               f"💰 Fiyat: `${p.get('priceUsd')}`\n"
               f"📈 24s Değişim: `%{p.get('priceChange', {}).get('h24')}`\n"
               f"━━━━━━━━━━━━━━━━━━")
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📈 Grafik", url=p.get('url'))]])
        await update.message.reply_text(msg, reply_markup=kb, parse_mode='Markdown')
    except:
        await update.message.reply_text("⚠️ Fiyat verisi şu an yoğun, lütfen tekrar dene.")

async def ciz_islemi(update, prompt):
    try:
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        response = requests.post(HF_API_URL, headers=headers, json={"inputs": prompt}, timeout=30)
        
        if response.status_code == 200:
            await update.message.reply_photo(photo=response.content, caption=f"🖼 **Irvus AI:** {prompt}")
        else:
            # Yedek motor (Pollinations)
            url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?nologo=true"
            await update.message.reply_photo(photo=url, caption=f"🖼 **Irvus AI (Yedek):** {prompt}")
    except:
        await update.message.reply_text("❌ Çizim sırasında hata oluştu.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        return await update.message.reply_text("❌ Örn: `/ciz aslan` veya `/draw dragon`")
    
    await update.message.reply_text(f"🎨 **'{prompt}'** hazırlanıyor...")
    asyncio.create_task(ciz_islemi(update, prompt))

# --- ANA MOTOR (3.14 Hatasını Baypas Eder) ---
async def main():
    # Flask'ı başlat
    Thread(target=run_web, daemon=True).start()
    
    # Botu en sağlam yapıyla kur
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    application.add_handler(CommandHandler(["ciz", "draw"], ciz))
    
    async with application:
        await application.initialize()
        await application.start()
        print(">>> BOT AKTIF VE DINLEMEDE")
        # Eski hataları temizle ve dinlemeye başla
        await application.updater.start_polling(drop_pending_updates=True)
        # Programın kapanmaması için beklet
        while True:
            await asyncio.sleep(3600)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
        
