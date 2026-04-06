import os, requests, asyncio, time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- 1. WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS SYSTEM ONLINE", 200

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAGC37E6oeacOL1fjtUWqFoN2sXCVlIplOc"
CA_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
LOGO_URL = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"
ANA_GRUP_ID = "-1002419409893"

# --- 3. YARDIMCI FONKSİYON ---
def get_safe(url):
    try:
        r = requests.get(url, timeout=12)
        return r.json() if r.status_code == 200 else None
    except: return None

# --- 4. KOMUTLAR ---

# TAM İSTEDİĞİN BUTONLU START KOMUTU
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (f"💎 **Irvus AI Dünyasına Hoş Geldiniz!**\n\n"
           f"Her iki grupta da alım takibi ve zeka desteği aktiftir.\n\n"
           f"📄 **CA:** `{CA_ADRESI}`")
    
    # Görseldeki buton yapısının aynısı
    kb = [
        [InlineKeyboardButton("🌐 Web Sitesi", url="https://www.irvustoken.xyz"), 
         InlineKeyboardButton("🐦 X (Twitter)", url="https://x.com/IRVUSTOKEN")],
        [InlineKeyboardButton("📊 Canlı Grafik", url=f"https://dexscreener.com/base/{CA_ADRESI}")]
    ]
    
    await update.message.reply_photo(
        photo=LOGO_URL, 
        caption=msg, 
        reply_markup=InlineKeyboardMarkup(kb), 
        parse_mode='Markdown'
    )

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
    await update.message.reply_text("💎 Veriler güncelleniyor, lütfen tekrar deneyin.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt: return await update.message.reply_text("❌ Kullanım: `/ciz aslan` ")
    
    await update.message.reply_text("🎨 Resminiz hazırlanıyor...")
    u = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?seed={int(time.time())}"
    await update.message.reply_photo(photo=u, caption=f"🖼 **Irvus Sanat:** `{prompt}`")

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
                if vol >= 5.0:
                    msg = (f"🚀 **YENİ ALIM!** 🟢\n━━━━━━━━━━━━━━\n"
                           f"💰 **Fiyat:** `${pair.get('priceUsd')}`\n"
                           f"💵 **Hacim:** `${vol:.2f}`\n━━━━━━━━━━━━━━")
                    try: await context.bot.send_photo(chat_id=ANA_GRUP_ID, photo=LOGO_URL, caption=msg)
                    except: pass
            last_buys = cur
        await asyncio.sleep(30)

# --- 6. ANA ÇALIŞTIRICI ---
async def main():
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    
    bot = ApplicationBuilder().token(TOKEN).build()
    
    # Handlerları buraya ekliyoruz
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    bot.add_handler(CommandHandler(["ciz", "draw"], ciz))
    
    async with bot:
        await bot.initialize()
        await bot.start()
        asyncio.create_task(track_buys(bot))
        await bot.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    try: asyncio.run(main())
    except: pass
        
