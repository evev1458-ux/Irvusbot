import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# --- WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS BOT ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- AYARLAR ---
TOKEN = "8621050385:AAGA6wcxbFY2rqJ9gjXVK_JNqsebJvTv_Jo"
TOKEN_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"

# YENI TOKEM VE MODEL AYARI
HF_TOKEN = "Hf_VzFKUkIElGkRTDWwEwLPwPPOOmwWwwBqNq" 
HF_API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"

# --- FONKSİYONLAR ---

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{TOKEN_ADRESI}", timeout=10).json()
        p = r['pairs'][0]
        msg = (f"💎 **Irvus Token ($IRVUS)**\n"
               f"━━━━━━━━━━━━━━━━━━\n"
               f"💵 Fiyat: `${p.get('priceUsd')}`\n"
               f"📈 24s Değişim: `%{p.get('priceChange', {}).get('h24')}`\n"
               f"━━━━━━━━━━━━━━━━━━")
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📊 DexScreener Grafiği", url=p.get('url'))]])
        await update.message.reply_text(msg, reply_markup=kb, parse_mode='Markdown')
    except:
        await update.message.reply_text("⚠️ Fiyat verisi şu an yoğunluk nedeniyle çekilemedi, lütfen tekrar deneyin.")

async def ciz_islemi(update, prompt):
    try:
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        # Hugging Face'e istek at
        response = requests.post(HF_API_URL, headers=headers, json={"inputs": prompt}, timeout=30)
        
        if response.status_code == 200:
            await update.message.reply_photo(photo=response.content, caption=f"🖼 **Irvus AI:** {prompt}")
        else:
            # Hugging Face hata verirse (401, 503 vb.) YEDEK MOTOR devreye girer
            backup_url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?nologo=true"
            await update.message.reply_photo(photo=backup_url, caption=f"🖼 **Irvus AI (Hızlı):** {prompt}")
    except:
        await update.message.reply_text("❌ Çizim servisinde bir sorun oluştu.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        return await update.message.reply_text("❌ Kullanım: `/ciz gold lion` veya `/draw dragon`")
    
    await update.message.reply_text(f"🎨 **'{prompt}'** Irvus AI tarafından hazırlanıyor...")
    asyncio.create_task(ciz_islemi(update, prompt))

# --- ANA ÇALIŞTIRICI ---
if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    application = Application.builder().token(TOKEN).build()
    
    # Komutları tanımla
    application.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    application.add_handler(CommandHandler(["ciz", "draw"], ciz))
    
    print(">>> IRVUS SISTEM BASLATILDI")
    application.run_polling(drop_pending_updates=True)
    
