import os, requests, asyncio, time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- 1. WEB SUNUCUSU (Render'ı Açık Tutar) ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS PRO MONITOR ACTIVE", 200

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAHAySA0SXbAP4G0KwcnCKGLkYs2yf-OeQU"
CA_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
ANA_GRUP_ID = "-1002393767346"
LOGO_URL = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"

BASE_RPC = "https://mainnet.base.org"
SWAP_TOPIC = "0xc42079f94a1d5046247098a76b0b302c30b6531398e0a8118d34346e27b13280"

# --- 3. YARDIMCI FİYAT ÇEKİCİ ---
def get_price_data():
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/pairs/base/{CA_ADRESI}", timeout=5).json()
        return r['pair']
    except: return None

# --- 4. KOMUTLAR ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (f"💎 **Irvus On-Chain İzleyici Aktif!**\n\n"
           f"Alımlar saniyeler içinde Base ağından yakalanır.\n\n"
           f"📄 **CA:** `{CA_ADRESI}`")
    kb = [[InlineKeyboardButton("📊 Grafik", url=f"https://dexscreener.com/base/{CA_ADRESI}")]]
    await update.message.reply_photo(photo=LOGO_URL, caption=msg, reply_markup=InlineKeyboardMarkup(kb))

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = get_price_data()
    if p:
        msg = (f"💰 **Fiyat:** `${p['priceUsd']}`\n"
               f"📊 **Market Cap:** `${float(p.get('fdv', 0))/1000:.1f}K`\n"
               f"📈 **24s Değişim:** %{p['priceChange']['h24']}")
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("⚠️ Fiyat şu an çekilemiyor.")

# --- 5. AĞ TAKİP MOTORU (On-Chain) ---
async def track_onchain(application):
    last_block = 0
    print(">>> Irvus On-Chain Engine Başlatıldı...")
    while True:
        try:
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
                        pair_data = get_price_data()
                        price = float(pair_data['priceUsd']) if pair_data else 0
                        usd_val = amount_raw * price
                        
                        if usd_val >= 5.0: # 5$ Filtresi
                            tx = log["transactionHash"]
                            msg = (f"🚀 **YENİ ALIM!** 🟢\n━━━━━━━━━━━━━━\n"
                                   f"💰 **Spent:** `${usd_val:.2f}`\n"
                                   f"💎 **Got:** `{amount_raw:,.0f} IRVUS`\n"
                                   f"━━━━━━━━━━━━━━\n"
                                   f"🔗 [Basescan](https://basescan.org/tx/{tx})")
                            try:
                                await application.bot.send_photo(chat_id=ANA_GRUP_ID, photo=LOGO_URL, caption=msg)
                            except: pass
                last_block = current_block
        except: pass
        await asyncio.sleep(5)

# --- 6. ANA BAŞLATICI ---
def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

async def main():
    # Flask sunucusunu Thread ile ayırıyoruz (Kilitlenmeyi önler)
    Thread(target=run_flask, daemon=True).start()
    
    # Bot kurulumu
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Komutları ekliyoruz
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    
    await application.initialize()
    await application.start()
    
    # On-Chain takibi botun ana işleyişine zarar vermeden arka planda çalıştırıyoruz
    asyncio.create_task(track_onchain(application))
    
    print(">>> Bot Tüm Fonksiyonlarıyla Aktif!")
    await application.updater.start_polling(drop_pending_updates=True)
    
    # Botun açık kalmasını sağla
    while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
        
