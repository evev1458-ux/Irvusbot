import os, requests, asyncio, time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- 1. WEB SUNUCUSU (Render Kapanmasın Diye) ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS MASTER ONLINE", 200

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAHAySA0SXbAP4G0KwcnCKGLkYs2yf-OeQU"
CA_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
ANA_GRUP_ID = "-1002393767346"
LOGO_URL = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"

BASE_RPC = "https://mainnet.base.org"
SWAP_TOPIC = "0xc42079f94a1d5046247098a76b0b302c30b6531398e0a8118d34346e27b13280"

# --- 3. YARDIMCI FİYAT ÇEKİCİ ---
def get_price_only():
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/pairs/base/{CA_ADRESI}", timeout=5).json()
        return float(r['pair']['priceUsd'])
    except: return 0.0

# --- 4. KOMUTLAR ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "💎 **Irvus On-Chain Aktif!**\n\nAlımlar doğrudan ağdan saniyesinde izleniyor."
    kb = [[InlineKeyboardButton("📊 Grafik", url=f"https://dexscreener.com/base/{CA_ADRESI}")]]
    await update.message.reply_photo(photo=LOGO_URL, caption=msg, reply_markup=InlineKeyboardMarkup(kb))

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = get_price_only()
    if p > 0: await update.message.reply_text(f"💰 **Fiyat:** `${p}`")
    else: await update.message.reply_text("⚠️ Veri şu an çekilemiyor.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt: return await update.message.reply_text("❌ Örn: `/ciz kedi` ")
    u = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?seed={int(time.time())}"
    await update.message.reply_photo(photo=u, caption=f"🖼 **Irvus AI:** `{prompt}`")

# --- 5. AĞ TAKİP MOTORU ---
async def track_onchain(application):
    last_block = 0
    while True:
        try:
            # Blok numarasını çek
            res = requests.post(BASE_RPC, json={"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}, timeout=10).json()
            current_block = int(res["result"], 16)
            if last_block == 0: last_block = current_block - 1

            if current_block > last_block:
                payload = {"jsonrpc":"2.0","method":"eth_getLogs","params":[{"fromBlock":hex(last_block+1),"toBlock":hex(current_block),"address":CA_ADRESI,"topics":[SWAP_TOPIC]}],"id":1}
                logs = requests.post(BASE_RPC, json=payload, timeout=10).json().get("result", [])
                
                for log in logs:
                    data_hex = log["data"][2:]
                    amount_raw = int(data_hex[-64:], 16) / 10**18
                    if amount_raw > 0:
                        price = get_price_only()
                        usd_val = amount_raw * price
                        if usd_val >= 5.0:
                            tx = log["transactionHash"]
                            msg = f"🚀 **YENİ ALIM!** 🟢\n━━━━━━━━━━━━━━\n💰 `${usd_val:.2f}`\n💎 `{amount_raw:,.0f} IRVUS`\n━━━━━━━━━━━━━━\n🔗 [Basescan](https://basescan.org/tx/{tx})"
                            await application.bot.send_photo(chat_id=ANA_GRUP_ID, photo=LOGO_URL, caption=msg)
                last_block = current_block
        except: pass
        await asyncio.sleep(6) # 6 saniye Render için en güvenli hızdır

# --- 6. ANA MOTOR ---
async def main():
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Komutları ekle
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    application.add_handler(CommandHandler("ciz", ciz))
    
    await application.initialize()
    await application.start()
    
    # Arka planda ağı dinle
    asyncio.create_task(track_onchain(application))
    
    await application.updater.start_polling(drop_pending_updates=True)
    while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    try: asyncio.run(main())
    except: pass
        
