import os, requests, asyncio, time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- 1. WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS LIGHT ONLINE", 200

# --- 2. AYARLAR ---
TOKEN = "BURAYA_YENI_ALDIĞIN_TOKENI_YAZ" # BotFather'dan aldığın güncel token
CA_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
GRUP_LISTESI = ["-1002393767346", "-1002375203585"]
LOGO_URL = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"

# --- 3. YARDIMCI FONKSİYON ---
def get_safe(url):
    try:
        r = requests.get(url, timeout=10)
        return r.json() if r.status_code == 200 else None
    except: return None

# --- 4. KOMUTLAR ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (f"💎 **Irvus Bilgi Sistemine Hoş Geldin!**\n\n"
           f"Aşağıdaki butonları kullanarak projemizi takip edebilirsin.\n\n"
           f"📄 **CA:** `{CA_ADRESI}`")
    
    kb = [[InlineKeyboardButton("📊 Canlı Grafik", url=f"https://dexscreener.com/base/{CA_ADRESI}")],
          [InlineKeyboardButton("🌐 Web Sitesi", url="https://www.irvustoken.xyz"), 
           InlineKeyboardButton("🐦 X (Twitter)", url="https://x.com/IRVUSTOKEN")]]
    
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
    await update.message.reply_text("💎 Veriler güncelleniyor, lütfen birazdan tekrar dene.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = " ".join(context.args)
    if not p: return await update.message.reply_text("❌ Kullanım: `/ciz aslan` ")
    u = f"https://image.pollinations.ai/prompt/{p.replace(' ', '%20')}?seed={int(time.time())}"
    await update.message.reply_photo(photo=u, caption=f"🖼 **Irvus Sanat:** `{p}`")

# --- 5. ALIM TAKİBİ (EN AZ 5$) ---
async def track_buys(context: ContextTypes.DEFAULT_TYPE):
    last_buys = 0
    while True:
        data = get_safe(f"https://api.dexscreener.com/latest/dex/pairs/base/{CA_ADRESI}")
        if data and 'pair' in data:
            pair = data['pair']
            cur = pair.get('txns', {}).get('m5', {}).get('buys', 0)
            
            # Yeni alım var mı kontrol et
            if last_buys != 0 and cur > last_buys:
                vol = float(pair.get('volume', {}).get('m5', 0))
                # SADECE 5 DOLAR VE ÜSTÜ ALIMLARI GÖSTER
                if vol >= 5.0:
                    msg = (f"🚀 **YENİ $IRVUS ALIMI!** 🟢\n"
                           f"━━━━━━━━━━━━━━\n"
                           f"💰 **Fiyat:** `${pair.get('priceUsd')}`\n"
                           f"💵 **Hacim:** `${vol:.2f}`\n"
                           f"━━━━━━━━━━━━━━\n"
                           f"💎 [Grafik](https://dexscreener.com/base/{CA_ADRESI})")
                    for gid in GRUP_LISTESI:
                        try: await context.bot.send_photo(chat_id=gid, photo=LOGO_URL, caption=msg, parse_mode='Markdown')
                        except: pass
            last_buys = cur
        await asyncio.sleep(30) # 30 saniyede bir kontrol

# --- 6. ANA ÇALIŞTIRICI ---
async def main():
    # Web sunucusunu başlat
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    
    # Botu başlat
    bot = ApplicationBuilder().token(TOKEN).build()
    
    # Komutları ekle
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    bot.add_handler(CommandHandler(["ciz", "draw"], ciz))
    
    async with bot:
        await bot.initialize()
        await bot.start()
        # Alım takibini arka planda başlat
        asyncio.create_task(track_buys(bot))
        # Botu dinlemeye başla
        await bot.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    try: asyncio.run(main())
    except: pass
        
