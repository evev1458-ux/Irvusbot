import os, asyncio, time, requests, aiohttp
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib.parse import quote

# --- 1. WEB ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS USD MONITOR ACTIVE", 200

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAHEpgqJYNNGXyon1I855vghWfkQ8p-4tlk"
CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
GROUP_ID = "-1002393767346"
LOGO = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"
BASE_RPC = "https://mainnet.base.org"
SWAP_TOPIC = "0xc42079f94a1d5046247098a76b0b302c30b6531398e0a8118d34346e27b13280"

# --- 3. YARDIMCI FİYAT FONKSİYONU ---
async def get_instant_price(session):
    try:
        url = f"https://api.dexscreener.com/latest/dex/pairs/base/{CA}"
        async with session.get(url, timeout=5) as r:
            data = await r.json()
            return float(data['pair']['priceUsd'])
    except:
        return 0.0

# --- 4. KOMUTLAR ---
async def start(update, context):
    msg = f"💎 **IRVUS V4 USD SISTEMI**\n\nDolar bazlı alımlar takip ediliyor.\n📄 CA: `{CA}`"
    kb = [[InlineKeyboardButton("🐦 Twitter", url="https://x.com/IRVUSTOKEN")]]
    await update.message.reply_photo(photo=LOGO, caption=msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def fiyat(update, context):
    async with aiohttp.ClientSession() as session:
        p = await get_instant_price(session)
    if p > 0: await update.message.reply_text(f"💰 **Fiyat:** `${p}`")
    else: await update.message.reply_text("⚠️ Fiyat şu an çekilemiyor.")

async def ciz(update, context):
    p = " ".join(context.args)
    if not p: return await update.message.reply_text("❌ Örnek: /ciz aslan")
    await update.message.reply_text("🎨 Çiziliyor...")
    url = f"https://image.pollinations.ai/prompt/{quote(p)}?seed={int(time.time())}"
    await update.message.reply_photo(photo=url, caption=f"🖼 `{p}`")

# --- 5. DOLAR BAZLI ALIM TAKİBİ ---
async def monitor(bot_app):
    last_block = 0
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # Blok çek
                async with session.post(BASE_RPC, json={"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}) as r:
                    curr = int((await r.json())["result"], 16)
                
                if last_block == 0: last_block = curr - 1
                if curr > last_block:
                    payload = {"jsonrpc":"2.0","method":"eth_getLogs","params":[{"fromBlock":hex(last_block+1),"toBlock":hex(curr),"address":CA,"topics":[SWAP_TOPIC]}],"id":1}
                    async with session.post(BASE_RPC, json=payload) as r:
                        logs = (await r.json()).get("result", [])
                    
                    for log in logs:
                        try:
                            # Adet hesapla
                            amt = int(log["data"][2:][-64:], 16) / 10**18
                            if amt > 10:
                                # Dolar değerini hesapla
                                price = await get_instant_price(session)
                                usd_value = amt * price
                                
                                # Sadece 5 dolar üstü alımları göster (Grubu kirletmemek için)
                                if usd_value >= 5.0:
                                    tx = log["transactionHash"]
                                    msg = (
                                        f"🚀 **YENİ ALIM!** 🟢\n"
                                        f"━━━━━━━━━━━━━━\n"
                                        f"💰 **Harcama:** `${usd_value:.2f}`\n"
                                        f"💎 **Miktar:** `{amt:,.0f} IRVUS`\n"
                                        f"━━━━━━━━━━━━━━\n"
                                        f"🔗 [Basescan](https://basescan.org/tx/{tx})"
                                    )
                                    await bot_app.bot.send_photo(chat_id=GROUP_ID, photo=LOGO, caption=msg, parse_mode='Markdown')
                        except: pass
                    last_block = curr
            except: pass
            await asyncio.sleep(8)

# --- 6. ÇALIŞTIR ---
def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

async def main():
    Thread(target=run_web, daemon=True).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler(["start", "star"], start))
    bot.add_handler(CommandHandler("fiyat", fiyat))
    bot.add_handler(CommandHandler("ciz", ciz))
    
    asyncio.create_task(monitor(bot))
    await bot.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
    
