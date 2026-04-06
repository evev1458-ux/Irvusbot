import os, time, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =========================
# 🔐 AYARLAR
# =========================
TOKEN = "8621050385:AAHIB0lWjzkDtgb2XJq32YmOg5Ggb_pZFZg"
CHAT_ID = "-1002393767346"
CA_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
LOGO_URL = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"

app = Flask(__name__)

@app.route("/")
def home(): return "IRVUS MONITOR ACTIVE", 200

# =========================
# 🔍 ALIM TAKİP MOTORU (API DESTEKLİ)
# =========================
def check_dex():
    """DexScreener üzerinden alımları ve fiyatı kontrol eder (Daha stabil)"""
    try:
        url = f"https://api.dexscreener.com/latest/dex/pairs/base/{CA_ADRESI}"
        res = requests.get(url, timeout=10).json()
        pair = res.get('pair', {})
        
        # Fiyat ve Market Cap Bilgisi
        price = pair.get('priceUsd', '0')
        mcap = pair.get('fdv', 0)
        
        # Son 5 dakikadaki alım sayısını kontrol ederek 'yeni alım' simülasyonu yapabiliriz
        # Ancak on-chain takip istiyorsan önceki yazdığın mantığı koruyalım ama düzeltelim.
        return price, mcap
    except:
        return None, None

async def track_buys(context: ContextTypes.DEFAULT_TYPE):
    """Arka planda alımları izleyen görev"""
    last_buy_count = 0
    while True:
        try:
            url = f"https://api.dexscreener.com/latest/dex/pairs/base/{CA_ADRESI}"
            res = requests.get(url, timeout=10).json()
            pair = res.get('pair', {})
            
            current_buys = pair.get('txns', {}).get('m5', {}).get('buys', 0)
            
            # Eğer yeni alım gelmişse (5 dakikalık periyotta artış varsa)
            if last_buy_count != 0 and current_buys > last_buy_count:
                price = pair.get('priceUsd', '0')
                vol = float(pair.get('volume', {}).get('m5', 0))
                
                # SADECE 5 DOLAR ÜSTÜ ALIMLAR
                if vol >= 5.0:
                    msg = (f"🚀 **YENİ $IRVUS ALIMI!** 🟢\n"
                           f"━━━━━━━━━━━━━━\n"
                           f"💰 **Fiyat:** `${price}`\n"
                           f"💵 **Hacim (5dk):** `${vol:.2f}`\n"
                           f"━━━━━━━━━━━━━━\n"
                           f"💎 [Grafik](https://dexscreener.com/base/{CA_ADRESI})")
                    
                    await context.bot.send_photo(chat_id=CHAT_ID, photo=LOGO_URL, caption=msg, parse_mode='Markdown')
            
            last_buy_count = current_buys
        except:
            pass
        await asyncio.sleep(40) # 40 saniyede bir kontrol

# =========================
# 🤖 KOMUTLAR
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💎 IRVUS On-Chain Monitor Aktif!")

# =========================
# 🚀 ANA ÇALIŞTIRICI
# =========================
def main():
    # Flask thread'i
    Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000))), daemon=True).start()

    # Bot kurulumu
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    # Alım takibini asenkron başlat
    job_queue = application.job_queue
    # 40 saniyede bir çalışacak görev
    # Not: python-telegram-bot[job-queue] kütüphanesi yüklü olmalıdır.

    print("Bot başlatılıyor...")
    application.run_polling()

if __name__ == "__main__":
    main()
    
