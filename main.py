import os, asyncio, requests, json, aiohttp, random
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
def home(): return "IRVUS LIVE", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if data: Thread(target=process_buy_signal, args=(data,)).start()
    return jsonify({"status": "ok"}), 200

def process_buy_signal(data):
    try:
        events = data.get('event', {}).get('activity', []) if isinstance(data, dict) else []
        if not events and isinstance(data, list): events = data
        for act in events:
            tx = act.get('hash') or act.get('transactionHash')
            val = act.get('value')
            if val and float(val) > 0:
                msg = f"🟢 **NEW IRVUS BUY!**\n\n💰 Amount: **{float(val):,.0f} IRVUS**\n🔗 [Basescan](https://basescan.org/tx/{tx})"
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": GROUP_ID, "text": msg, "parse_mode": "Markdown"})
    except: pass

# --- KOMUTLAR ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("🌐 Website", url="https://www.irvustoken.xyz")],
        [InlineKeyboardButton("🐦 Twitter (X)", url="https://x.com/IRVUSTOKEN")]
    ]
    await update.message.reply_text(
        "💎 **IRVUS GLOBAL BOT**\n\nAI, Draw, Price and Live Buys are active!", 
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode='Markdown'
    )

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get(f"https://api.geckoterminal.com/api/v2/networks/base/tokens/{CA}").json()
        p = r['data']['attributes']['price_usd']
        await update.message.reply_text(f"💰 **IRVUS Price:** `${float(p):.8f}`", parse_mode='Markdown')
    except: await update.message.reply_text("⚠️ Fiyat hatası.")

async def ask_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = " ".join(context.args)
    if not q: return
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://text.pollinations.ai/{quote(q)}") as r:
                ans = await r.text()
                await update.message.reply_text(f"🤖 **Irvus AI:**\n\n{ans}")
    except: pass

async def draw_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = " ".join(context.args)
    if not p: return await update.message.reply_text("Ne çizelim?")
    await update.message.reply_text("🎨 Çiziliyor, lütfen bekleyin...")
    seed = random.randint(1, 99999)
    url = f"https://pollinations.ai/p/{quote(p)}?width=1024&height=1024&seed={seed}&nologo=true"
    try:
        await update.message.reply_photo(photo=url, caption=f"🖼 **Art:** {p}")
    except: await update.message.reply_text("🎨 Görsel oluşturulamadı.")

async def main():
    Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler(["fiyat", "price"], fiyat))
    app_bot.add_handler(CommandHandler(["sor", "ask"], ask_cmd))
    app_bot.add_handler(CommandHandler(["ciz", "draw"], draw_cmd))
    
    await app_bot.initialize()
    await app_bot.start()
    await app_bot.updater.start_polling(drop_pending_updates=True)
    while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
    
