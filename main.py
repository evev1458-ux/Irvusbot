import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- 1. WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAESXIZLT6HbS3CGeT-sT-HJcgvFuJF8ff0" 
CA_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
HF_TOKEN = "Hf_VzFKUkIElGkRTDWwEwLPwPPOOmwWwwBqNq"
HF_API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"

X_ADRESI = "https://x.com/IRVUSTOKEN"
WEB_SITESI = "https://www.irvustoken.xyz"
LOGO_URL = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg" 

# --- 3. FONKSİYONLAR ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "💎 **Irvus Token Dünyasına Hoş Geldiniz!**\n\n"
        "Ben **Irvus AI**, topluluğunuzun sanat ve finans asistanıyım.\n\n"
        f"📄 **Kontrat Adresi (Base):**\n`{CA_ADRESI}`\n\n"
        "🚀 **Komutlar:**\n"
        "🔹 `/fiyat` - Anlık $IRVUS verileri.\n"
        "🔹 `/ciz [kelime]` - AI Görsel oluşturma.\n\n"
        "**Resmi Bağlantılarımız:**"
    )
    keyboard = [[InlineKeyboardButton("🌐 Web Sitesi", url=WEB_SITESI), InlineKeyboardButton("🐦 X (Twitter)", url=X_ADRESI)],
                [InlineKeyboardButton("📊 Canlı Grafik (Base)", url=f"https://dexscreener.com/base/{CA_ADRESI}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        await update.message.reply_photo(photo=LOGO_URL, caption=welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    except:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # EN GARANTI YONTEM: Search API (Tokenı zorla bulur)
        url = f"https://api.dexscreener.com/latest/dex/search?q={CA_ADRESI}"
        res = requests.get(url, timeout=15).json()
        
        # Base ağındaki doğru çifti seç
        pairs = res.get('pairs', [])
        p = next((x for x in pairs if x['chainId'] == 'base'), None)

        if p:
            f_usd = p.get('priceUsd', '0.00')
            degisim = p.get('priceChange', {}).get('h24', '0')
            msg = (f"💎 **$IRVUS Güncel Durum**\n"
                   f"━━━━━━━━━━━━━━━━━━\n"
                   f"💰 Fiyat: `${f_usd}`\n"
                   f"📈 24s Değişim: `%{degisim}`\n"
                   f"━━━━━━━━━━━━━━━━━━")
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("📊 Grafiği Görüntüle", url=p.get('url'))]])
            await update.message.reply_text(msg, reply_markup=kb, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Fiyat şu an hazır değil (Token henüz yeni olabilir).")
    except:
        await update.message.reply_text("⚠️ API şu an yoğun, lütfen az sonra tekrar deneyin.")

async def ciz_islemi(update, prompt):
    try:
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        response = requests.post(HF_API_URL, headers=headers, json={"inputs": prompt}, timeout=30)
        if response.status_code == 200:
            await update.message.reply_photo(photo=response.content, caption=f"🖼 **Irvus AI:** {prompt}")
        else:
            url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?nologo=true"
            await update.message.reply_photo(photo=url, caption=f"🖼 **Irvus AI (Yedek):** {prompt}")
    except:
        await update.message.reply_text("❌ Çizim motoru meşgul.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt: return await update.message.reply_text("❌ Örn: `/ciz aslan` ")
    await update.message.reply_text(f"🎨 **'{prompt}'** hazırlanıyor...")
    asyncio.create_task(ciz_islemi(update, prompt))

# --- 4. ANA MOTOR ---
async def main():
    Thread(target=run_web, daemon=True).start()
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    application.add_handler(CommandHandler(["ciz", "draw"], ciz))
    async with application:
        await application.initialize()
        await application.start()
        print(">>> IRVUS BOT AKTIF")
        await application.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    try: asyncio.run(main())
    except (KeyboardInterrupt, SystemExit): pass
        
