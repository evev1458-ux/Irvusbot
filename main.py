import os, requests, asyncio, time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- 1. WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS ON-CHAIN SYSTEM ACTIVE", 200

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAHAySA0SXbAP4G0KwcnCKGLkYs2yf-OeQU" 
CA_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
ANA_GRUP_ID = "-1002393767346"
LOGO_URL = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"

# AĞ AYARLARI (Base Mainnet)
BASE_RPC = "https://mainnet.base.org"
SWAP_TOPIC = "0xc42079f94a1d5046247098a76b0b302c30b6531398e0a8118d34346e27b13280"

# --- 3. SADECE FİYAT ÇEKİCİ (DexScreener) ---
def get_current_price():
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/pairs/base/{CA_ADRESI}", timeout=5).json()
        return float(r['pair']['priceUsd'])
    except: return 0.0

# --- 4. KOMUTLAR ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (f"💎 **Irvus On-Chain Sistemine Hoş Geldiniz!**\n\n"
           f"Alımlar doğrudan **Base Ağında** takip ediliyor.\n\n"
           f"📄 **CA:** `{CA_ADRESI}`")
    kb = [[InlineKeyboardButton("🌐 Web Sitesi", url="https://www.irvustoken.xyz"), 
           InlineKeyboardButton("📊 Grafik", url=f"https://dexscreener.com/base/{CA_ADRESI}")]]
    await update.message.reply_photo(photo=LOGO_URL, caption=msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = get_current_price()
    if price > 0:
        await update.message.reply_text(f"💰 **Güncel $IRVUS Fiyatı:** `${price}`")
    else:
        await update.message.reply_text("⚠️ Fiyat şu an çekilemiyor, grafikten bakabilirsin.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt: return await update.message.reply_text("❌ Örn: `/ciz aslan` ")
    await update.message.reply_text("🎨 Çiziliyor...")
    u = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?seed={int(time.time())}"
    await update.message.reply_photo(photo=u, caption=f"🖼 **Irvus AI:** `{prompt}`")

# --- 5. ANA MOTOR: BASE AĞI ALIM TAKİBİ ---
async def monitor_base_chain(application):
    last_block = 0
    print(">>> Base Ağı Dinleniyor...")
    
    while True:
        try:
            # 1. En son blok numarasını al
            res = requests.post(BASE_RPC, json={"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}, timeout=10).json()
            current_block = int(res["result"], 16)
            
            if last_block == 0: last_block = current_block - 1
            
            # 2. Yeni blokları tara
            if current_block > last_block:
                payload = {
                    "jsonrpc": "2.0", "method": "eth_getLogs",
                    "params": [{
                        "fromBlock": hex(last_block + 1), "toBlock": hex(current_block),
                        "address": CA_ADRESI, "topics": [SWAP_TOPIC]
                    }], "id": 1
                }
                logs = requests.post(BASE_RPC, json=payload, timeout=10).json().get("result", [])
                
                for log in logs:
                    # Logdan alınan miktarı çöz (HEX to DEC)
                    data_hex = log["data"][2:]
                    amount_raw = int(data_hex[-64:], 16) / 10**18
                    
                    if amount_raw > 0:
                        # Dolar değerini hesapla
                        price = get_current_price()
                        usd_val = amount_raw * price
                        
                        # 5 DOLAR FİLTRESİ
                        if usd_val >= 5.0:
                            tx_hash = log["transactionHash"]
                            buy_msg = (
                                f"🚀 **BASE AĞINDA YENİ ALIM!** 🟢\n"
                                f"━━━━━━━━━━━━━━\n"
                                f"💰 **Spent:** `${usd_val:.2f}`\n"
                                f"💎 **Got:** `{amount_raw:,.0f} IRVUS`\n"
                                f"━━━━━━━━━━━━━━\n"
                                f"🔗 [Basescan](https://basescan.org/tx/{tx_hash})"
                            )
                            try:
                                await application.bot.send_photo(chat_id=ANA_GRUP_ID, photo=LOGO_URL, caption=buy_msg, parse_mode='Markdown')
                            except: pass
                
                last_block = current_block
        except: pass
        await asyncio.sleep(5) # 5 saniyede bir blok kontrolü

# --- 6. ÇALIŞTIRICI ---
async def main():
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    application.add_handler(CommandHandler(["ciz", "draw"], ciz))
    
    await application.initialize()
    await application.start()
    
    # Ağ takip motorunu arka planda başlat
    asyncio.create_task(monitor_base_chain(application))
    
    await application.updater.start_polling(drop_pending_updates=True)
    while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    try: asyncio.run(main())
    except: pass
                        
