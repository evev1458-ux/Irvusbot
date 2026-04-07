import os, asyncio, time, requests, aiohttp
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- 1. WEB SUNUCUSU (Bağımsız) ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS LIVE", 200

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAHEpgqJYNNGXyon1I855vghWfkQ8p-4tlk"
CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
GROUP_ID = "-1002393767346"
LOGO = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"
BASE_RPC = "https://mainnet.base.org"
SWAP_TOPIC = "0xc42079f94a1d5046247098a76b0b302c30b6531398e0a8118d34346e27b13280"

# --- 3. KOMUTLAR ---
async def start(update, context):
    msg = f"💎 **IRVUS TOKEN DÜNYASI**\n\n📄 **CA:** `{CA}`"
    kb = [[InlineKeyboardButton("🐦 Twitter", url="https://x.com/IRVUSTOKEN")]]
    await update.message.reply_photo(photo=LOGO, caption=msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def fiyat(update, context):
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/pairs/base/{CA}", timeout=5).json()
        p = r['pair']['priceUsd']
        await update.message.reply_text(f"💰 **Fiyat:** `${p}`")
    except: await update.message.reply_text("⚠️ Fiyat verisi şu an yoğun.")

# --- 4. ALIM TAKİBİ (Döngü) ---
async def monitor(app):
    last_block = 0
    while True:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.post(BASE_RPC, json={"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}) as r:
                    curr = int((await r.json())["result"], 16)
                if last_block == 0: last_block = curr - 1
                if curr > last_block:
                    logs = (await s.post(BASE_RPC, json={"jsonrpc":"2.0","method":"eth_getLogs","params":[{"fromBlock":hex(last_block+1),"toBlock":hex(curr),"address":CA,"topics":[SWAP_TOPIC]}],"id":1})).json()["result"]
                    for log in logs:
                        amt = int(log["data"][2:][-64:], 16) / 10**18
                        if amt > 50:
                            await app.bot.send_photo(chat_id=GROUP_ID, photo=LOGO, caption=f"🚀 **YENİ ALIM!**\n💎 `{amt:,.0f} IRVUS`")
                    last_block = curr
        except: pass
        await asyncio.sleep(15)

# --- 5. BAĞIMSIZ BAŞLATICI ---
def main():
    # 1. Web'i başlat
    Thread(target=run_web, daemon=True).start()
    
    # 2. Botu başlat
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler(["start", "star"], start))
    app_bot.add_handler(CommandHandler("fiyat", fiyat))
    
    # 3. İzleyiciyi ayrı bir loop'ta çalıştır
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(monitor(app_bot))
    
    app_bot.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
    
