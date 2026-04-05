import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- 1. WEB SUNUCUSU (Render'ın botu kapatmaması için) ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS SISTEM ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. AYARLAR & LİNKLER ---
TOKEN = "8621050385:AAESXIZLT6HbS3CGeT-sT-HJcgvFuJF8ff0" 
CA_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
HF_TOKEN = "Hf_VzFKUkIElGkRTDWwEwLPwPPOOmwWwwBqNq"
HF_API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"

# Sosyal Medya ve Logo
WEB_SITESI = "https://www.irvustoken.xyz"
X_ADRESI = "https://x.com/IRVUSTOKEN"
LOGO_URL = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg" 

# --- 3. FONKSİYONLAR ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "💎 **Irvus Token Dünyasına Hoş Geldiniz!**\n\n"
        "Ben **Irvus AI**, topluluğumuzun hem finans hem de sanat asistanıyım.\n\n"
        f"📄 **Kontrat Adresi (Base):**\n`{CA_ADRESI}`\n\n"
        "🚀 **Komutlar:**\n"
        "🔹 `/fiyat` - Güncel $IRVUS verilerini getirir.\n"
        "🔹 `/ciz [kelime]` - Yapay zeka ile görsel oluşturur.\n\n"
        "**Resmi Bağlantılarımız:**"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🌐 Web Sitesi", url=WEB_SITESI),
            InlineKeyboardButton("🐦 X (Twitter)", url=X_ADRESI)
        ],
        [
            InlineKeyboardButton("📈 Canlı Grafik (Base)", url=f"https://dexscreener.com/base/{CA_ADRESI}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await update.message.reply_photo(photo=LOGO_URL, caption=welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    except:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Base ağı için garantili DexScreener sorgusu
        url = f"https://api.dexscreener.com/latest/dex/pairs/base/{CA_ADRESI}"
        response = requests.get(url, timeout=15)
        data = response.json()
        
        # Veri yapısını kontrol et
        p = data.get('pair') or (data.get('pairs')[0] if data.get('pairs') else None)
        
        if not p:
            return await update.message.reply_text("❌ Veri bulunamadı. Lütfen CA kontrol edin.")

        f_usd = p.get('priceUsd', '0.00')
        degisim = p.get('priceChange', {}).get('h24', '0')

        msg = (f"💎 **$IRVUS Güncel Durum**\n"
               f"━━━━━━━━━━━━━━━━━━\n"
               f"💰 Fiyat: `${f_usd}`\n"
               f"📈 24s Değişim: `%{degisim}`\n"
               f"━━━━━━━━━━━━━━━━━━")
        
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📊 Grafiği Görüntüle", url=p.get('url'))]])
        await update.message.reply_text(msg, reply_markup=kb, parse_mode='Markdown')
    except:
        await update.message.reply_text("⚠️ DexScreener şu an yoğun, lütfen az sonra tekrar deneyin.")

async def ciz_islemi(update, prompt):
    try:
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        response = requests.post(HF_API_URL, headers=headers, json={"inputs": prompt}, timeout=30)
        
        if response.status_code == 200:
            await update.message.reply_photo(photo=response.content, caption=f"🖼 **Irvus AI:** {prompt}")
        else:
            # Hugging Face meşgulse yedek motor (Pollinations)
            url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?nologo=true"
            await update.message.reply_photo(photo=url, caption=f"🖼 **Irvus AI (Yedek):** {prompt}")
    except:
        await update.message.reply_text("❌ Çizim şu an yapılamıyor.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt: return await update.message.reply_text("❌ Örn: `/ciz siberpunk aslan` ")
    await update.message.reply_text(f"🎨 **'{prompt}'** hazırlanıyor...")
    asyncio.create_task(ciz_islemi(update, prompt))

# --- 4. ANA MOTOR (Python 3.14 Uyumlu Asenkron Yapı) ---
async def main_async():
    # Flask sunucusunu başlat
    Thread(target=run_web, daemon=True).start()
    
    # Botu oluştur
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Komutları kaydet
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    application.add_handler(CommandHandler(["ciz", "draw"], ciz))
    
    # Botu asenkron olarak başlat
    async with application:
        await application.initialize()
        await application.start()
        print(">>> IRVUS BOT AKTIF")
        await application.updater.start_polling(drop_pending_updates=True)
        # Botun açık kalmasını sağla
        while True:
            await asyncio.sleep(3600)

if __name__ == '__main__':
    try:
        asyncio.run(main_async())
    except (KeyboardInterrupt, SystemExit):
        pass
        
