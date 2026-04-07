import os, asyncio, time, requests, aiohttp
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib.parse import quote

# --- 1. WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS SYSTEM ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAHEpgqJYNNGXyon1I855vghWfkQ8p-4tlk"
CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
GROUP_ID = "-1002393767346"
LOGO = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"
BASE_RPC = "https://mainnet.base.org"
SWAP_TOPIC = "0xc42079f94a1d5046247098a76b0b302c30b6531398e0a8118d34346e27b13280"

# --- 3. YARDIMCI FONKSİYONLAR ---
async def get_price():
    try:
        url = f"https://api.dexscreener.com/latest/dex/pairs/base/{CA}"
        r = requests.get(url, timeout=5).json()
        return float(r['pair']['priceUsd'])
    except: return 0.0

# --- 4. KOMUTLAR ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = f"💎 **IRVUS TOKEN DÜNYASI**\n\n📄 **CA:** `{CA}`"
    kb = [[InlineKeyboardButton("🐦 Twitter (X)", url="https://x.com/IRVUSTOKEN")]]
    await update.message.reply_photo(photo=LOGO, caption=msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = await get_price()
    if p > 0: await update.message.reply_text(f"💰 **Fiyat:** `${p}`")
    else: await update.message.reply_text("⚠️ Veri şu an çekilemiyor.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = " ".join(context.args)
    if not p: return await update.message.reply_text("❌ Örnek: `/ciz aslan` ")
    await update.message.reply_text("🎨 Çiziliyor...")
    url = f"https://image.pollinations.ai/prompt/{quote(p)}?seed={int(time.time())}"
    await update.message.reply_photo(photo=url, caption=f"🖼 `{p}`")

# --- 5. ALIM TAKİBİ ---
async def monitor(application):
    last_block = 0
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(BASE_RPC, json={"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}) as r:
                    res = await r.json()
                    curr = int(res["result"], 16)
                
                if last_block == 0: last_block = curr - 1
                if curr > last_block:
                    payload = {"jsonrpc":"2.0","method":"eth_getLogs","params":[{"fromBlock":hex(last_block+1),"toBlock":hex(curr),"address":CA,"topics":[SWAP_TOPIC]}],"id":1}
                    async with session.post(BASE_RPC, json=payload) as r:
                        logs = (await r.json()).get("result", [])
                    
                    for log in logs:
                        amt = int(log["data"][2:][-64:], 16) / 10**18
                        if amt > 50:
                            p = await get_price()
                            usd = amt * p
                            if usd >= 5:
                                tx = log["transactionHash"]
                                msg = f"🚀 **YENİ ALIM!** 🟢\n💰 `${usd:.2f}`\n💎 `{amt:,.0f} IRVUS`\n🔗 [Basescan](https://basescan.org/tx/{tx})"
                                await application.bot.send_photo(chat_id=GROUP_ID, photo=LOGO, caption=msg, parse_mode='Markdown')
                last_block = curr
        except: pass
        await asyncio.sleep(10)

# --- 6. MODERN ANA ÇALIŞTIRICI ---
async def main():
    # Flask'ı başlat
    Thread(target=run_web, daemon=True).start()

    # Botu kur
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler(["start", "star"], start))
    application.add_handler(CommandHandler("fiyat", fiyat))
    application.add_handler(CommandHandler("ciz", ciz))

    # Alım takibi görevini başlat
    asyncio.create_task(monitor(application))

    # Botu en güncel yöntemle başlat
    async with application:
        await application.initialize()
        await application.start()
        print(">>> IRVUS SISTEMI AKTIF")
        await application.updater.start_polling(drop_pending_updates=True)
        # Botun sürekli açık kalmasını sağla
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
        
