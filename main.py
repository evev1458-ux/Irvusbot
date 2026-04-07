import os, asyncio, time, aiohttp
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib.parse import quote

# --- 1. WEB SUNUCUSU (Render İçin) ---
app = Flask(__name__)
@app.route('/')
def home():
    return "IRVUS MASTER SYSTEM ONLINE", 200

# --- 2. AYARLAR ---
# Token doğrudan içine yazıldı, os.getenv hatası giderildi.
TOKEN = "8621050385:AAEPRKANXBaUJUIm6gsHqLcKVYyskUOZ8JU"
CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
GROUP_ID = "-1002393767346"
LOGO = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"

WEB_URL = "https://www.irvustoken.xyz"
X_URL = "https://x.com/irvus"

BASE_RPC = "https://mainnet.base.org"
SWAP_TOPIC = "0xc42079f94a1d5046247098a76b0b302c30b6531398e0a8118d34346e27b13280"

# --- 3. FİYAT ÇEKİCİ ---
async def get_price(session):
    try:
        url = f"https://api.dexscreener.com/latest/dex/pairs/base/{CA}"
        async with session.get(url, timeout=5) as r:
            data = await r.json()
            return float(data['pair']['priceUsd'])
    except:
        return 0.0

# --- 4. KOMUTLAR ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start komutu (Star olarak yazmıştın, start daha standarttır)"""
    msg = f"💎 **IRVUS TOKEN DÜNYASI**\n\n📄 **CA:**\n`{CA}`"
    kb = [[
        InlineKeyboardButton("🌐 Web Site", url=WEB_URL),
        InlineKeyboardButton("🐦 X (Twitter)", url=X_URL)
    ]]
    await update.message.reply_photo(
        photo=LOGO,
        caption=msg,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode='Markdown'
    )

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with aiohttp.ClientSession() as session:
        price = await get_price(session)
    if price > 0:
        await update.message.reply_text(f"💰 **Güncel Fiyat:** `${price}`")
    else:
        await update.message.reply_text("⚠️ Fiyat şu an alınamadı.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        return await update.message.reply_text("❌ Örnek: `/ciz uzayda bir aslan` ")
    
    await update.message.reply_text("🎨 Irvus AI çiziyor, lütfen bekle...")
    url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?seed={int(time.time())}"
    await update.message.reply_photo(photo=url, caption=f"🖼 **Sonuç:** `{prompt}`")

# --- 5. BASE AĞI CANLI TAKİP ---
async def monitor(app_bot):
    last_block = 0
    print(">>> AĞ TAKİBİ BAŞLATILDI")

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # Blok numarasını al
                payload = {"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}
                async with session.post(BASE_RPC, json=payload, timeout=10) as r:
                    data = await r.json()
                
                current = int(data["result"], 16)
                if last_block == 0:
                    last_block = current - 1

                if current > last_block:
                    logs_payload = {
                        "jsonrpc":"2.0",
                        "method":"eth_getLogs",
                        "params":[{
                            "fromBlock": hex(last_block + 1),
                            "toBlock": hex(current),
                            "address": CA,
                            "topics":[SWAP_TOPIC]
                        }],
                        "id":1
                    }

                    async with session.post(BASE_RPC, json=logs_payload, timeout=10) as r:
                        logs_res = await r.json()
                        logs = logs_res.get("result", [])

                    for log in logs:
                        try:
                            # Miktarı çöz
                            data_hex = log["data"][2:]
                            amount = int(data_hex[-64:], 16) / 10**18
                            if amount <= 0: continue

                            # Fiyat ve Dolar hesabı
                            price = await get_price(session)
                            usd = amount * price

                            # 5 DOLAR FİLTRESİ (Gereksiz kalabalığı önler)
                            if usd < 5: continue

                            # Emoji Sistemi
                            if usd >= 500: emoji = "🐳 WHALE BUY!"
                            elif usd >= 100: emoji = "🔥 BIG BUY!"
                            else: emoji = "🟢 NEW BUY!"

                            tx = log["transactionHash"]
                            msg = (
                                f"{emoji}\n\n"
                                f"💰 **Spent:** `${usd:.2f}`\n"
                                f"💎 **Got:** `{amount:,.0f} IRVUS`\n\n"
                                f"🔗 [Basescan](https://basescan.org/tx/{tx})"
                            )

                            await app_bot.bot.send_photo(
                                chat_id=GROUP_ID,
                                photo=LOGO,
                                caption=msg,
                                parse_mode='Markdown'
                            )
                        except: pass
                    last_block = current
            except: pass
            await asyncio.sleep(5) # 5 saniyede bir blok kontrolü

# --- 6. ÇALIŞTIRICI ---
def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    # Flask'ı ayrı kolda başlat
    Thread(target=run_web, daemon=True).start()

    # Botu kur
    bot = ApplicationBuilder().token(TOKEN).build()

    # Komutları kaydet
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("fiyat", fiyat))
    bot.add_handler(CommandHandler("ciz", ciz))

    # Takip motorunu arka plana at
    loop = asyncio.get_event_loop()
    loop.create_task(monitor(bot))

    print(">>> IRVUS BOT AKTİF VE DİNLİYOR")
    bot.run_polling(drop_pending_updates=True)
    
