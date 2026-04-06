import os, requests, asyncio, time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- 1. WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS ON-CHAIN PRO ACTIVE", 200

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAHIB0lWjzkDtgb2XJq32YmOg5Ggb_pZFZg"
CA_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
ANA_GRUP_ID = "-1002393767346"
LOGO_URL = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"

BASE_RPC = "https://mainnet.base.org"
# Swap Event Topic
SWAP_TOPIC = "0xc42079f94a1d5046247098a76b0b302c30b6531398e0a8118d34346e27b13280"

# --- 3. YARDIMCI VERİ ÇEKİCİ ---
def get_price():
    """Hesaplama için anlık fiyatı çeker"""
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/pairs/base/{CA_ADRESI}", timeout=5).json()
        return float(r['pair']['priceUsd'])
    except: return None

# --- 4. KOMUTLAR ---
async def start(update, context):
    await update.message.reply_photo(photo=LOGO_URL, caption="💎 **Irvus On-Chain İzleyici Aktif!**\nSaniyeler içinde alım takibi devrede.")

# --- 5. GELİŞMİŞ AĞ TAKİP MOTORU ---
async def track_onchain(context: ContextTypes.DEFAULT_TYPE):
    last_block = 0
    print(">>> Irvus On-Chain Engine Başlatıldı...")

    while True:
        try:
            # Güncel blok numarasını al
            res_block = requests.post(BASE_RPC, json={"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}).json()
            current_block = int(res_block["result"], 16)

            if last_block == 0:
                last_block = current_block - 1

            if current_block > last_block:
                payload = {
                    "jsonrpc": "2.0", "method": "eth_getLogs",
                    "params": [{
                        "fromBlock": hex(last_block + 1), "toBlock": hex(current_block),
                        "address": CA_ADRESI, "topics": [SWAP_TOPIC]
                    }], "id": 1
                }
                logs = requests.post(BASE_RPC, json=payload).json().get("result", [])

                for log in logs:
                    # Log datasından alınan miktarı çıkar (Basitleştirilmiş HEX decoding)
                    # Not: Uniswap V3 log yapısına göre data kısmından miktar çekilir.
                    data_hex = log["data"][2:]
                    # Alınan miktar genellikle logun son kısımlarındadır (18 decimal varsayımı)
                    amount_raw = int(data_hex[-64:], 16) / 10**18 
                    
                    if amount_raw > 0:
                        current_price = get_price()
                        if current_price:
                            usd_value = amount_raw * current_price
                            
                            # 5 DOLAR FİLTRESİ
                            if usd_value >= 5.0:
                                tx_hash = log["transactionHash"]
                                msg = (
                                    f"🚀 **YENİ $IRVUS ALIMI!** 🟢\n"
                                    f"━━━━━━━━━━━━━━\n"
                                    f"💰 **Harcana:** `${usd_value:.2f}`\n"
                                    f"💎 **Alınan:** `{amount_raw:,.0f} IRVUS`\n"
                                    f"🏷 **Fiyat:** `${current_price}`\n"
                                    f"━━━━━━━━━━━━━━\n"
                                    f"🔗 [Basescan](https://basescan.org/tx/{tx_hash})"
                                )
                                try:
                                    await context.bot.send_photo(chat_id=ANA_GRUP_ID, photo=LOGO_URL, caption=msg, parse_mode='Markdown')
                                except: pass

                last_block = current_block
        except: pass
        await asyncio.sleep(4) # 4 saniyede bir blok tarar

async def main():
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    async with bot:
        await bot.initialize()
        await bot.start()
        asyncio.create_task(track_onchain(bot))
        await bot.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main())
    
