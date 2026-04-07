import os, asyncio, time, requests, aiohttp
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib.parse import quote

# --- 1. WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS SYSTEM RUNNING", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAHEpgqJYNNGXyon1I855vghWfkQ8p-4tlk"
CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
GROUP_ID = "-1002393767346"
LOGO = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"
BASE_RPC = "https://mainnet.base.org"
# Uniswap v4 ve genel swap takibi için topic
SWAP_TOPIC = "0xc42079f94a1d5046247098a76b0b302c30b6531398e0a8118d34346e27b13280"

# --- 3. GÜVENLİ FİYAT ÇEKİCİ ---
async def get_safe_price():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        # DexScreener denemesi
        url = f"https://api.dexscreener.com/latest/dex/pairs/base/{CA}"
        r = requests.get(url, headers=headers, timeout=5).json()
        return float(r['pair']['priceUsd'])
    except:
        try:
            # Yedek: GeckoTerminal
            url_g = f"https://api.geckoterminal.com/api/v2/networks/base/tokens/{CA}"
            r_g = requests.get(url_g, headers=headers, timeout=5).json()
            return float(r_g['data']['attributes']['price_usd'])
        except:
            return 0.0

# --- 4. KOMUTLAR ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fiyat çekilmese bile butonlar her zaman gelir"""
    msg = (f"💎 **Irvus On-Chain Sistemine Hoş Geldiniz!**\n\n"
           f"Alımlar doğrudan **Base Ağında** saniyesinde izleniyor.\n\n"
           f"📄 **CA:** `{CA}`")
    
    kb = [
        [InlineKeyboardButton("🌐 Web Sitesi", url="https://www.irvustoken.xyz"), 
         InlineKeyboardButton("🐦 Twitter (X)", url="https://x.com/IRVUSTOKEN")]
    ]
    
    try:
        await update.message.reply_photo(
            photo=LOGO, 
            caption=msg, 
            reply_markup=InlineKeyboardMarkup(kb), 
            parse_mode='Markdown'
        )
    except:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = await get_safe_price()
    if p > 0:
        await update.message.reply_text(f"💰 **Güncel $IRVUS Fiyatı:** `${p}`")
    else:
        await update.message.reply_text("⚠️ Fiyat verisi şu an yoğun, grafikten kontrol edebilirsiniz.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt: return await update.message.reply_text("❌ Kullanım: `/ciz kedi` ")
    await update.message.reply_text("🎨 Çiziliyor...")
    u = f"https://image.pollinations.ai/prompt/{quote(prompt)}?seed={int(time.time())}"
    await update.message.reply_photo(photo=u, caption=f"🖼 **Irvus AI:** `{prompt}`")

# --- 5. ANA MOTOR: BASE AĞI ALIM TAKİBİ ---
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
                        logs_res = await r.json()
                        logs = logs_res.get("result", [])
                    
                    for log in logs:
                        try:
                            amt = int(log["data"][2:][-64:], 16) / 10**18
                            if amt > 10: # Küçük alımları filtrele
                                p = await get_safe_price()
                                usd = amt * p
                                if usd >= 5 or p == 0: # 5$ üstü veya fiyat çekilemese de adet göster
                                    tx = log["transactionHash"]
                                    msg = f"🚀 **YENİ ALIM!** 🟢\n💰 `${usd:.2f}`\n💎 `{amt:,.0f} IRVUS`\n🔗 [Basescan](https://basescan.org/tx/{tx})"
                                    await application.bot.send_photo(chat_id=GROUP_ID, photo=LOGO, caption=msg, parse_mode='Markdown')
                        except: pass
                last_block = curr
        except: pass
        await asyncio.sleep(10)

# --- 6. MODERN ANA ÇALIŞTIRICI ---
async def main():
    Thread(target=run_web, daemon=True).start()
    
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler(["start", "star"], start))
    application.add_handler(CommandHandler("fiyat", fiyat))
    application.add_handler(CommandHandler("ciz", ciz))

    asyncio.create_task(monitor(application))

    async with application:
        await application.initialize()
        await application.start()
        print(">>> IRVUS SISTEMI AKTIF")
        await application.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except: pass
    
