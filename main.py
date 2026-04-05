import os, requests, asyncio, time
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

# --- 2. AYARLAR & HAFIZA SİSTEMİ ---
TOKEN = "8621050385:AAESXIZLT6HbS3CGeT-sT-HJcgvFuJF8ff0" 
CA_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
HF_TOKEN = "Hf_VzFKUkIElGkRTDWwEwLPwPPOOmwWwwBqNq"
HF_API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"

# SOSYAL LİNKLER
X_ADRESI = "https://x.com/IRVUSTOKEN"
WEB_SITESI = "https://www.irvustoken.xyz"
LOGO_URL = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg" 

# ÖNBELLEK AYARLARI (API'yi korur)
LAST_PRICE_DATA = {"price": "0.00", "change": "0", "time": 0}
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# --- 3. FONKSİYONLAR ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "💎 **Irvus Token Dünyasına Hoş Geldiniz!**\n\n"
        f"📄 **Kontrat Adresi (Base):**\n`{CA_ADRESI}`\n\n"
        "🚀 **Komutlar:**\n"
        "🔹 `/fiyat` - Anlık $IRVUS verileri.\n"
        "🔹 `/ciz [kelime]` - AI Görsel oluşturma.\n\n"
        "**Resmi Bağlantılarımız:**"
    )
    keyboard = [[InlineKeyboardButton("🌐 Web Sitesi", url=WEB_SITESI), InlineKeyboardButton("🐦 X (Twitter)", url=X_ADRESI)],
                [InlineKeyboardButton("📊 Canlı Grafik (Base)", url=f"https://dexscreener.com/base/{CA_ADRESI}")]]
    try:
        await update.message.reply_photo(photo=LOGO_URL, caption=welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    except:
        await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global LAST_PRICE_DATA
    simdi = time.time()
    
    # EĞER SON SORGUDAN 90 SANİYE GEÇMEDİYSE HAFIZADAN GÖNDER (API'YI YORMAZ)
    if simdi - LAST_PRICE_DATA["time"] < 90 and LAST_PRICE_DATA["price"] != "0.00":
        msg = (f"💎 **$IRVUS Güncel Durum**\n"
               f"━━━━━━━━━━━━━━━━━━\n"
               f"💰 Fiyat: `${LAST_PRICE_DATA['price']}`\n"
               f"📈 24s Değişim: `%{LAST_PRICE_DATA['change']}`\n"
               f"━━━━━━━━━━━━━━━━━━\n"
               f"ℹ️ *Veri her 90 saniyede bir güncellenir.*")
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📊 Grafiği Görüntüle", url=f"https://dexscreener.com/base/{CA_ADRESI}")]])
        return await update.message.reply_text(msg, reply_markup=kb, parse_mode='Markdown')

    # YENİ VERİ ÇEKMEYİ DENE
    f_usd, degisim = None, "0"
    try:
        url = f"https://api.dexscreener.com/latest/dex/search?q={CA_ADRESI}"
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        p = next((x for x in res.get('pairs', []) if x['chainId'] == 'base'), None)
        if p:
            f_usd = p.get('priceUsd')
            degisim = p.get('priceChange', {}).get('h24', '0')
            # HAFIZAYI GÜNCELLE
            LAST_PRICE_DATA = {"price": f_usd, "change": degisim, "time": simdi}
    except: pass

    if f_usd:
        msg = (f"💎 **$IRVUS Güncel Durum**\n"
               f"━━━━━━━━━━━━━━━━━━\n"
               f"💰 Fiyat: `${f_usd}`\n"
               f"📈 24s Değişim: `%{degisim}`\n"
               f"━━━━━━━━━━━━━━━━━━")
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📊 Grafiği Görüntüle", url=f"https://dexscreener.com/base/{CA_ADRESI}")]])
        await update.message.reply_text(msg, reply_markup=kb, parse_mode='Markdown')
    else:
        # API HALA BLOKLUYSA BİLE ESKİ FİYATI GÖSTER (KULLANICI HATA GÖRMESİN)
        if LAST_PRICE_DATA["price"] != "0.00":
            msg = (f"💎 **$IRVUS Güncel Durum**\n"
                   f"━━━━━━━━━━━━━━━━━━\n"
                   f"💰 Fiyat: `${LAST_PRICE_DATA['price']}`\n"
                   f"📈 24s Değişim: `%{LAST_PRICE_DATA['change']}`\n"
                   f"━━━━━━━━━━━━━━━━━━\n"
                   f"⚠️ *Sistem yoğun, son kaydedilen fiyat gösteriliyor.*")
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("📊 Grafiği Görüntüle", url=f"https://dexscreener.com/base/{CA_ADRESI}")]])
            await update.message.reply_text(msg, reply_markup=kb, parse_mode='Markdown')
        else:
            await update.message.reply_text("⚠️ Fiyat servisi şu an meşgul, 30 sn sonra tekrar deneyin.")

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
        
