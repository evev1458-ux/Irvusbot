import os, requests, asyncio, time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- 1. WEB SUNUCUSU (Render İçin) ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS SYSTEM ONLINE", 200

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAGC37E6oeacOL1fjtUWqFoN2sXCVlIplOc" # Buraya en son aldığın yeni tokenı yaz!
CA_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
LOGO_URL = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"

# GRUP LİSTESİ (İki grubu da buraya ekledim)
GRUP_LISTESI = ["-1002393767346", "-1002375203585"]

# --- 3. YARDIMCI FONKSİYON ---
def get_safe(url):
    try:
        r = requests.get(url, timeout=10)
        return r.json() if r.status_code == 200 else None
    except: return None

# --- 4. KOMUTLAR (Start, Fiyat, Ciz) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (f"💎 **Irvus Bilgi Sistemine Hoş Geldin!**\n\n"
           f"Ben Irvus topluluğunun yardımcı botuyum. Alımları takip eder, fiyat verir ve resim çizerim.\n\n"
           f"📄 **CA:** `{CA_ADRESI}`")
    
    # Butonlar
    kb = [
        [InlineKeyboardButton("📊 Canlı Grafik", url=f"https://dexscreener.com/base/{CA_ADRESI}")],
        [InlineKeyboardButton("🌐 Web Sitesi", url="https://www.irvustoken.xyz"), 
         InlineKeyboardButton("🐦 X (Twitter)", url="https://x.com/IRVUSTOKEN")]
    ]
    
    await update.message.reply_photo(photo=LOGO_URL, caption=msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await update.message.reply_text("⚠️ Veriler şu an çekilemiyor, lütfen az sonra tekrar dene.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt: return await update.message.reply_text("❌ Kullanım: `/ciz kedi` ")
    
    await update.message.reply_text("🎨 Resmin hazırlanıyor, lütfen bekle...")
    url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?seed={int(time.time())}"
    await update.message.reply_photo(photo=url, caption=f"🖼 **Irvus Sanat:** `{prompt}`")

# --- 5. ALIM TAKİBİ (EN AZ 5$) ---

async def track_buys(context: ContextTypes.DEFAULT_TYPE):
    last_buys = 0
    while True:
        data = get_safe(f"https://api.dexscreener.com/latest/dex/pairs/base/{CA_ADRESI}")
        if data and 'pair' in data:
            pair = data['pair']
            cur = pair.get('txns', {}).get('m5', {}).get('buys', 0)
            
            if last_buys != 0 and cur > last_buys:
                vol = float(pair.get('volume', {}).get('m5', 0))
                # SADECE 5 DOLAR VE ÜSTÜ
                if vol >= 5.0:
                    price = pair.get('priceUsd', '0')
                    msg = (f"🚀 **YENİ $IRVUS ALIMI!** 🟢\n"
                           f"━━━━━━━━━━━━━━\n"
                           f"💰 **Fiyat:** `${price}`\n"
                           f"💵 **Hacim:** `${vol:.2f}`\n"
                           f"━━━━━━━━━━━━━━\n"
                           f"💎 [Grafik](https://dexscreener.com/base/{CA_ADRESI})")
                    for gid in GRUP_LISTESI:
                        try: await context.bot.send_photo(chat_id=gid, photo=LOGO_URL, caption=msg, parse_mode='Markdown')
                        except: pass
            last_buys = cur
        await asyncio.sleep(30) # 30 saniyede bir kontrol

# --- 6. ANA ÇALIŞTIRICI ---

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

async def main():
    # Flask'ı ayrı bir thread'de başlat
    Thread(target=run_flask, daemon=True).start()
    
    # Bot kurulumu
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Komutları buraya ekliyoruz (Handlerlar)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    application.add_handler(CommandHandler(["ciz", "draw"], ciz))
    
    # Botu başlat
    async with application:
        await application.initialize()
        await application.start()
        
        # Alım takibi görevini başlat
        asyncio.create_task(track_buys(application))
        
        # Dinlemeye başla
        await application.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    try: asyncio.run(main())
    except: pass
        
