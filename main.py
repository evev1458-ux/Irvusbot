import os, requests, asyncio, time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# --- 1. WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS SYSTEM CHECK OK", 200

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAHAySA0SXbAP4G0KwcnCKGLkYs2yf-OeQU" 
CA_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
LOGO_URL = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"
ANA_GRUP_ID = "-1002419409893"

# --- 3. YARDIMCI FONKSİYONLAR ---
def get_safe(url):
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200: return r.json()
    except: pass
    return None

# --- 4. KOMUT FONKSİYONLARI ---

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Görseldeki gibi butonlu karşılama ekranı"""
    text = (f"💎 **Irvus AI Dünyasına Hoş Geldiniz!**\n\n"
            f"Bilgi sistemi ve alım takibi 7/24 aktiftir.\n\n"
            f"📄 **CA:** `{CA_ADRESI}`")
    
    keyboard = [
        [InlineKeyboardButton("🌐 Web Sitesi", url="https://www.irvustoken.xyz"), 
         InlineKeyboardButton("🐦 X (Twitter)", url="https://x.com/IRVUSTOKEN")],
        [InlineKeyboardButton("📊 Canlı Grafik", url=f"https://dexscreener.com/base/{CA_ADRESI}")]
    ]
    
    await update.message.reply_photo(
        photo=LOGO_URL, 
        caption=text, 
        reply_markup=InlineKeyboardMarkup(keyboard), 
        parse_mode='Markdown'
    )

async def fiyat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fiyat bilgilerini çeker"""
    data = get_safe(f"https://api.dexscreener.com/latest/dex/search?q={CA_ADRESI}")
    if data and 'pairs' in data:
        p = next((x for x in data['pairs'] if x['chainId'] == 'base'), None)
        if p:
            mcap = float(p.get('fdv', 0)) / 1000
            msg = (f"💰 **Irvus Fiyat:** `${p['priceUsd']}`\n"
                   f"📈 **24s Değişim:** %{p['priceChange']['h24']}\n"
                   f"📊 **Market Cap:** `${mcap:.1f}K`\n"
                   f"💧 **Likidite:** `${p.get('liquidity', {}).get('usd', 0):,.0f}`")
            return await update.message.reply_text(msg)
    await update.message.reply_text("💎 Veriler güncelleniyor, lütfen tekrar deneyin.")

async def ciz_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Resim çizer"""
    prompt = " ".join(context.args)
    if not prompt: 
        return await update.message.reply_text("❌ Kullanım: `/ciz aslan` ")
    
    await update.message.reply_text("🎨 Resminiz hazırlanıyor...")
    image_url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?seed={int(time.time())}"
    await update.message.reply_photo(photo=image_url, caption=f"🖼 **Irvus Sanat:** `{prompt}`")

# --- 5. ALIM TAKİBİ ---
async def track_buys(context: ContextTypes.DEFAULT_TYPE):
    last_buys = 0
    while True:
        data = get_safe(f"https://api.dexscreener.com/latest/dex/pairs/base/{CA_ADRESI}")
        if data and 'pair' in data:
            pair = data['pair']
            cur = pair.get('txns', {}).get('m5', {}).get('buys', 0)
            if last_buys != 0 and cur > last_buys:
                vol = float(pair.get('volume', {}).get('m5', 0))
                if vol >= 5.0:
                    msg = (f"🚀 **YENİ ALIM!** 🟢\n━━━━━━━━━━━━━━\n"
                           f"💰 **Fiyat:** `${pair.get('priceUsd')}`\n"
                           f"💵 **Hacim:** `${vol:.2f}`\n━━━━━━━━━━━━━━")
                    try: await context.bot.send_photo(chat_id=ANA_GRUP_ID, photo=LOGO_URL, caption=msg)
                    except: pass
            last_buys = cur
        await asyncio.sleep(35)

# --- 6. ANA ÇALIŞTIRICI (DÜZELTİLDİ) ---
async def main():
    # Flask başlat
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    
    # Bot kurulumu
    app_bot = ApplicationBuilder().token(TOKEN).build()
    
    # KOMUTLARI EKLE (Sıralama ve isimler netleştirildi)
    app_bot.add_handler(CommandHandler("start", start_handler))
    app_bot.add_handler(CommandHandler("fiyat", fiyat_handler))
    app_bot.add_handler(CommandHandler("p", fiyat_handler)) # Kısa yol
    app_bot.add_handler(CommandHandler("ciz", ciz_handler))
    app_bot.add_handler(CommandHandler("draw", ciz_handler)) # Kısa yol
    
    async with app_bot:
        await app_bot.initialize()
        await app_bot.start()
        # Alım takibi başlat
        asyncio.create_task(track_buys(app_bot))
        # Dinlemeye başla
        await app_bot.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    try: asyncio.run(main())
    except: pass
        
