import os, requests, asyncio, time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- 1. WEB SUNUCUSU (Render Kapanmasın Diye) ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS SYSTEM RUNNING", 200

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAHIB0lWjzkDtgb2XJq32YmOg5Ggb_pZFZg"
CA_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
ANA_GRUP_ID = "-1002393767346"
LOGO_URL = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"
BASE_RPC = "https://mainnet.base.org"
SWAP_TOPIC = "0xc42079f94a1d5046247098a76b0b302c30b6531398e0a8118d34346e27b13280"

# --- 3. YARDIMCI FONKSİYONLAR ---
def get_safe_price():
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/pairs/base/{CA_ADRESI}", timeout=5).json()
        return r['pair']
    except: return None

# --- 4. KOMUTLAR (START, FIYAT, CIZ) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (f"💎 **Irvus Bilgi Sistemi Aktif!**\n\n"
           f"Ağ üzerinden anlık alım takibi ve komutlar devrede.\n\n"
           f"📄 **CA:** `{CA_ADRESI}`")
    kb = [[InlineKeyboardButton("📊 Canlı Grafik", url=f"https://dexscreener.com/base/{CA_ADRESI}")],
          [InlineKeyboardButton("🌐 Web Sitesi", url="https://www.irvustoken.xyz")]]
    await update.message.reply_photo(photo=LOGO_URL, caption=msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = get_safe_price()
    if p:
        msg = (f"💰 **Fiyat:** `${p['priceUsd']}`\n"
               f"📊 **Market Cap:** `${float(p.get('fdv', 0))/1000:.1f}K`\n"
               f"💧 **Likidite:** `${p.get('liquidity', {}).get('usd', 0):,.0f}`")
        return await update.message.reply_text(msg)
    await update.message.reply_text("💎 Veriler güncelleniyor...")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt: return await update.message.reply_text("❌ Örn: `/ciz aslan` ")
    await update.message.reply_text("🎨 Hazırlanıyor...")
    u = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?seed={int(time.time())}"
    await update.message.reply_photo(photo=u, caption=f"🖼 **Irvus AI:** `{prompt}`")

# --- 5. AG TAKIP MOTORU (ON-CHAIN) ---
async def track_onchain(context: ContextTypes.DEFAULT_TYPE):
    last_block = 0
    while True:
        try:
            res_block = requests.post(BASE_RPC, json={"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}, timeout=10).json()
            current_block = int(res_block["result"], 16)
            if last_block == 0: last_block = current_block - 1

            if current_block > last_block:
                payload = {"jsonrpc": "2.0", "method": "eth_getLogs", "params": [{"fromBlock": hex(last_block + 1), "toBlock": hex(current_block), "address": CA_ADRESI, "topics": [SWAP_TOPIC]}], "id": 1}
                logs = requests.post(BASE_RPC, json=payload, timeout=10).json().get("result", [])
                for log in logs:
                    data_hex = log["data"][2:]
                    amount_raw = int(data_hex[-64:], 16) / 10**18
                    if amount_raw > 0:
                        p_data = get_safe_price()
                        if p_data:
                            usd_val = amount_raw * float(p_data['priceUsd'])
                            if usd_val >= 5.0: # 5 DOLAR FILTRESI
                                msg = (f"🚀 **YENİ ALIM!** 🟢\n━━━━━━━━━━━━━━\n"
                                       f"💰 **Harcama:** `${usd_val:.2f}`\n"
                                       f"💎 **Miktar:** `{amount_raw:,.0f} IRVUS`\n"
                                       f"━━━━━━━━━━━━━━")
                                try: await context.bot.send_photo(chat_id=ANA_GRUP_ID, photo=LOGO_URL, caption=msg)
                                except: pass
                last_block = current_block
        except: pass
        await asyncio.sleep(5)

# --- 6. ANA CALISTIRICI (FIXED) ---
async def main():
    # Flask sunucusunu ayrı kolda başlat
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    
    # Bot kurulumu
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Komutları buraya ekliyoruz (Sıralama Önemli)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    application.add_handler(CommandHandler(["ciz", "draw"], ciz))
    
    async with application:
        await application.initialize()
        await application.start()
        # Takip motorunu asenkron görev olarak ekliyoruz
        asyncio.create_task(track_onchain(application))
        # Botu dinlemeye başla (Eski takılmaları temizleyerek)
        await application.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    try: asyncio.run(main())
    except: pass
                                                           
