import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# --- WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS BOT AKTIF", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- AYARLAR ---
TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
TOKEN_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
HF_TOKEN = "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"
HF_API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"

# --- FONKSİYONLAR ---

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # DexScreener bazen çok sorguda 429 atar, timeout ekledik
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{TOKEN_ADRESI}", timeout=10).json()
        if 'pairs' not in r:
            return await update.message.reply_text("❌ Veri henüz hazır değil, az sonra tekrar dene.")
            
        p = r['pairs'][0]
        msg = f"💎 **$IRVUS Güncel Durum**\n\n💰 Fiyat: `${p.get('priceUsd')}`\n📈 24s: `%{p.get('priceChange', {}).get('h24')}`"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📈 Grafik", url=p.get('url'))]])
        await update.message.reply_text(msg, reply_markup=kb, parse_mode='Markdown')
    except:
        await update.message.reply_text("⚠️ API şu an meşgul (Hata 429). 1 dakika sonra tekrar dene.")

async def ciz_islemi(update, prompt):
    try:
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        response = requests.post(HF_API_URL, headers=headers, json={"inputs": prompt}, timeout=30)
        
        if response.status_code == 200:
            await update.message.reply_photo(photo=response.content, caption=f"🖼 **IRVUS AI:** {prompt}")
        else:
            # Hugging Face hata verirse yedek motor
            url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?nologo=true"
            await update.message.reply_photo(photo=url, caption=f"🖼 **AI (Yedek):** {prompt}")
    except:
        await update.message.reply_text("❌ Çizim motoru şu an meşgul.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        return await update.message.reply_text("❌ Örn: `/ciz dragon`")
    
    await update.message.reply_text(f"🎨 **'{prompt}'** hazırlanıyor...")
    asyncio.create_task(ciz_islemi(update, prompt))

# --- ÇALIŞTIRICI ---
if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    # Logdaki hatayı önlemek için ApplicationBuilder kullandık
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    application.add_handler(CommandHandler(["ciz", "draw"], ciz))
    print(">>> BOT BASLATILDI")
    application.run_polling(drop_pending_updates=True)
    
