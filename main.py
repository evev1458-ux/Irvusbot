import os, asyncio, time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import aiohttp
from urllib.parse import quote

# --- WEB ---
app = Flask(__name__)
@app.route('/')
def home():
    return "IRVUS ONLINE", 200

# --- AYAR ---
TOKEN = os.getenv("8621050385:AAEPRKANXBaUJUIm6gsHqLcKVYyskUOZ8JU")
CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
GROUP_ID = "-1002393767346"
LOGO = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"

WEB_URL = "https://www.irvustoken.xyz"
X_URL = "https://x.com/irvus"

BASE_RPC = "https://mainnet.base.org"
SWAP_TOPIC = "0xc42079f94a1d5046247098a76b0b302c30b6531398e0a8118d34346e27b13280"

# --- FİYAT ---
async def get_price(session):
    try:
        url = f"https://api.dexscreener.com/latest/dex/pairs/base/{CA}"
        async with session.get(url) as r:
            data = await r.json()
            return float(data['pair']['priceUsd'])
    except:
        return 0

# --- /star ---
async def star(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = f"💎 IRVUS TOKEN\n\n📄 CA:\n`{CA}`"

    kb = [[
        InlineKeyboardButton("🌐 Web Site", url=WEB_URL),
        InlineKeyboardButton("🐦 X", url=X_URL)
    ]]

    await update.message.reply_photo(
        photo=LOGO,
        caption=msg,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode='Markdown'
    )

# --- /fiyat ---
async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with aiohttp.ClientSession() as session:
        price = await get_price(session)

    if price > 0:
        await update.message.reply_text(f"💰 Fiyat: ${price}")
    else:
        await update.message.reply_text("⚠️ Fiyat alınamadı")

# --- /ciz ---
async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)

    if not prompt:
        return await update.message.reply_text("❌ Örnek: /ciz kedi")

    await update.message.reply_text("🎨 çiziliyor...")

    url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?seed={int(time.time())}"

    await update.message.reply_photo(photo=url, caption=prompt)

# --- BASE TAKİP ---
async def monitor(app_bot):
    last_block = 0

    async with aiohttp.ClientSession() as session:
        print(">>> TAKİP BAŞLADI")

        while True:
            try:
                # blok
                payload = {"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}
                async with session.post(BASE_RPC, json=payload) as r:
                    data = await r.json()

                current = int(data["result"], 16)

                if last_block == 0:
                    last_block = current - 1

                if current > last_block:
                    logs_payload = {
                        "jsonrpc":"2.0",
                        "method":"eth_getLogs",
                        "params":[{
                            "fromBlock": hex(last_block+1),
                            "toBlock": hex(current),
                            "address": CA,
                            "topics":[SWAP_TOPIC]
                        }],
                        "id":1
                    }

                    async with session.post(BASE_RPC, json=logs_payload) as r:
                        logs = (await r.json()).get("result", [])

                    for log in logs:
                        try:
                            data_hex = log["data"][2:]
                            amount = int(data_hex[-64:], 16) / 10**18

                            if amount <= 0:
                                continue

                            price = await get_price(session)
                            usd = amount * price

                            if usd < 20:
                                continue

                            # emoji sistem
                            if usd >= 1000:
                                emoji = "🐳"
                            elif usd >= 100:
                                emoji = "🔥"
                            else:
                                emoji = "🟢"

                            tx = log["transactionHash"]

                            msg = (
                                f"{emoji} YENİ ALIM\n\n"
                                f"💰 ${usd:.2f}\n"
                                f"💎 {amount:,.0f} IRVUS\n\n"
                                f"https://basescan.org/tx/{tx}"
                            )

                            await app_bot.bot.send_photo(
                                chat_id=GROUP_ID,
                                photo=LOGO,
                                caption=msg
                            )

                        except:
                            pass

                    last_block = current

            except:
                pass

            await asyncio.sleep(4)

# --- RUN ---
def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

async def main():
    Thread(target=run_web, daemon=True).start()

    bot = ApplicationBuilder().token(TOKEN).build()

    bot.add_handler(CommandHandler("star", star))
    bot.add_handler(CommandHandler("fiyat", fiyat))
    bot.add_handler(CommandHandler("ciz", ciz))

    asyncio.create_task(monitor(bot))

    print(">>> BOT ÇALIŞIYOR")
    await bot.run_polling()

if __name__ == "__main__":
    asyncio.run(main())

