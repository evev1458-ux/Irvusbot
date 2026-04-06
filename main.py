import os, requests, asyncio, time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. AYARLAR ---
TOKEN = "8621050385:AAGC37E6oeacOL1fjtUWqFoN2sXCVlIplOc"
CA_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
GRUP_ID = "-1002419409893" # Kendi grup ID'ni buraya yaz
LOGO_URL = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"
MIN_BUY_AMOUNT = 5.0  # Minimum 5 dolarlık alımları yakalar

# Alım takibi için son işlem zamanı hafızası
LAST_CHECK_TIME = time.time() * 1000 

app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS BUY BOT ACTIVE", 200

# --- 2. ALIM TAKİP MOTORU (BUY TRACKER) ---

async def track_buys(context: ContextTypes.DEFAULT_TYPE):
    global LAST_CHECK_TIME
    print(">>> Alım takibi başlatıldı...")
    
    while True:
        try:
            # DexScreener'dan son işlemleri çek (Base ağı için)
            url = f"https://api.dexscreener.com/latest/dex/pairs/base/{CA_ADRESI}"
            res = requests.get(url, timeout=10).json()
            pair = res.get('pair', {})
            
            # Fiyat ve Market Cap verileri
            price = pair.get('priceUsd', '0')
            mcap = pair.get('fdv', 0)
            mcap_str = f"{mcap/1000:.1f}K" if mcap < 1000000 else f"{mcap/1000000:.2f}M"

            # Not: Ücretsiz DexScreener API'si anlık işlem listesi vermeyebilir. 
            # Bu yüzden 5 dakikalık periyotlardaki değişimleri kontrol ediyoruz.
            buys_5m = pair.get('txns', {}).get('m5', {}).get('buys', 0)
            volume_5m = float(pair.get('volume', {}).get('m5', 0))

            # Eğer son 5 dakikada hacim varsa ve alım yapılmışsa (Basit Mantık)
            # Daha gelişmiş takip için Webhook servisleri gerekebilir ancak bu yöntem Render'da stabil çalışır.
            if volume_5m > MIN_BUY_AMOUNT:
                buy_msg = (
                    f"🚀 **YENİ $IRVUS ALIMI!** 🟢\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"💰 **Fiyat:** `${price}`\n"
                    f"📊 **Market Cap:** `${mcap_str}`\n"
                    f"💵 **Hacim (5dk):** `${volume_5m:.2f}`\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"💎 [Grafik](https://dexscreener.com/base/{CA_ADRESI}) | [Satın Al](https://app.uniswap.org/swap?outputCurrency={CA_ADRESI}&chain=base)"
                )
                try:
                    await context.bot.send_photo(chat_id=GRUP_ID, photo=LOGO_URL, caption=buy_msg, parse_mode='Markdown')
                except:
                    pass # Hata durumunda botun çökmemesi için
                    
        except Exception as e:
            print(f"Takip hatası: {e}")
        
        await asyncio.sleep(60) # Her 60 saniyede bir kontrol et

# --- 3. DİĞER FONKSİYONLAR (Start, Fiyat, Ciz, Chat) ---

async def start(update, context):
    msg = f"💎 **Irvus AI Aktif!**\n\nFiyat, Çizim ve Alım Takibi devrede.\n\n📄 **CA:** `{CA_ADRESI}`"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("📊 Grafik", url=f"https://dexscreener.com/base/{CA_ADRESI}")]])
    await update.message.reply_photo(photo=LOGO_URL, caption=msg, reply_markup=kb)

async def fiyat(update, context):
    res = requests.get(f"https://api.dexscreener.com/latest/dex/search?q={CA_ADRESI}").json()
    p = next((x for x in res.get('pairs', []) if x['chainId'] == 'base'), None)
    if p:
        await update.message.reply_text(f"💰 **Fiyat:** `${p['priceUsd']}`\n📈 **24s:** `%{p['priceChange']['h24']}`")

async def ciz(update, context):
    prompt = " ".join(context.args)
    if not prompt: return await update.message.reply_text("❌ Örn: `/ciz aslan` ")
    url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?seed={int(time.time())}"
    await update.message.reply_photo(photo=url, caption=f"🖼 **Irvus AI:** `{prompt}`")

async def chat_ai(update, context):
    if not update.message or not update.message.text: return
    if "irvus" in update.message.text.lower() or (update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id):
        # Önceki sohbet kodun buraya gelebilir
        await update.message.reply_text("💎 Irvus ile gelecek bugün başlıyor!")

# --- 4. ANA MOTOR ---
async def main():
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    application.add_handler(CommandHandler(["ciz", "draw"], ciz))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat_ai))
    
    async with application:
        await application.initialize()
        await application.start()
        
        # Alım Takibini (Buy Bot) Arka Planda Başlatıyoruz
        asyncio.create_task(track_buys(application))
        
        await application.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    try: asyncio.run(main())
    except: pass
    
