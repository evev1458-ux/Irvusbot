import os, asyncio, requests, json, aiohttp
from flask import Flask, request, jsonify
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib.parse import quote

# --- AYARLAR ---
TOKEN = "8621050385:AAFP8Pmc0p24oQnDEiL6SwMTgL6tr3HIPss"
GROUP_ID = -1002315757919
CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"

app = Flask(__name__)

@app.route('/')
def home(): 
    return "IRVUS ONLINE", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if data:
        Thread(target=process_buy_signal, args=(data,)).start()
    return jsonify({"status": "ok"}), 200

def process_buy_signal(data):
    try:
        activities = data.get('event', {}).get('activity', []) if isinstance(data, dict) else []
        if not activities and isinstance(data, list): activities = data
        for act in activities:
            tx = act.get('hash') or act.get('transactionHash')
            val = act.get('value')
            if val and float(val) > 0:
                msg = f"🟢 **NEW IRVUS BUY!**\n\n💰 Amount: **{float(val):,.0f} IRVUS**\n🔗 [Basescan](https://basescan.org/tx/{tx})"
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                             json={"chat_id": GROUP_ID, "text": msg, "parse_mode": "Markdown"})
    except: pass

async def start(update, context):
    kb = [[InlineKeyboardButton("🌐 Website", url="https://www.irvustoken.xyz")]]
    await update.message.reply_text("💎 **IRVUS GLOBAL BOT**", reply_markup=InlineKeyboardMarkup(kb))

async def fiyat(update, context):
    try:
        r = requests.get(f"https://api.geckoterminal.com/api/v2/networks/base/tokens/{CA}").json()
        p = r['data']['attributes']['price_usd']
        await update.message.reply_text(f"💰 **IRVUS Price:** `${float(p):.8f}`")
    except: await update.message.reply_text("⚠️ Hata.")

async def ask_cmd(update, context):
    q = " ".join(context.args)
    if not q: return
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://text.pollinations.ai/{quote(q)}") as r:
                await update.message.reply_text(await r.text())
    except: pass

async def main():
    Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler(["fiyat", "price"], fiyat))
    app_bot.add_handler(CommandHandler(["sor", "ask"], ask_cmd))
    
    await app_bot.initialize()
    await app_bot.start()
    await app_bot.updater.start_polling(drop_pending_updates=True)
    while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
    
