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
# Hugging Face API Ayarı (En kaliteli model)
HF_API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
HF_TOKEN = "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" # Senin verdiğin token
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# --- FONKSİYONLAR ---

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{TOKEN_ADRESI}", timeout=5).json()
        p = r['pairs'][0]
        msg = f"💎 **$IRVUS Güncel Durum**\n\n💰 Fiyat: `${p.get('priceUsd')}`\n📈 24s: `%{p.get('priceChange', {}).get('h24')}`"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📈 Grafik", url=p.get('url'))]])
        await update.message.reply_text(msg, reply_markup=kb, parse_mode='Markdown')
    except:
        await update.message.reply_text("❌ Fiyat verisi şu an çekilemedi.")

async def ciz_islemi(update, prompt):
    try:
        # Hugging Face API'ye istek atıyoruz
        response = requests.post(HF_API_URL, headers=headers, json={"inputs": prompt}, timeout=30)
        if response.status_code == 200:
            await update.message.reply_photo(photo=response.content, caption=f"🖼 **IRVUS AI:** {prompt}")
        else:
            # API meşgulse hızlı motora pasla (Yedek plan)
            url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?nologo=true"
            await update.message.reply_photo(photo=url, caption=f"🖼 **AI (Yedek):** {prompt}")
    except:
        await update.message.reply_text("❌ Çizim sırasında bir hata oluştu.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("❌ Örn: `/ciz blue dragon`")
        return
    
    await update.message.reply_text(f"🎨 **'{prompt}'** Hugging Face ile çiziliyor...")
    # Arka planda çalıştır (Bot donmasın)
    asyncio.create_task(ciz_islemi(update, prompt))

# --- ÇALIŞTIRICI ---
if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    # Buradaki 'Application' yapısı Render'da 3.10 sürümünde hatasız çalışır
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    application.add_handler(CommandHandler(["ciz", "draw"], ciz))
    print(">>> BOT BASLATILDI")
    application.run_polling(drop_pending_updates=True)
    
