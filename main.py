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
    return "IRVUS ALCHEMY SYSTEM: LIVE", 200

# --- 🟢 ANLIK ALIM KAPISI (WEBHOOK) ---
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if data:
        Thread(target=process_buy_signal, args=(data,)).start()
    return jsonify({"status": "ok"}), 200

def process_buy_signal(data):
    try:
        activities = []
        if isinstance(data, dict) and 'event' in data:
            activities = data['event'].get('activity', [])
        elif isinstance(data, list):
            activities = data
        
        for act in activities:
            tx_hash = act.get('hash') or act.get('transactionHash')
            value = act.get('value')
            if value and float(value) > 0:
                msg = (f"🟢 **NEW IRVUS BUY!**\n\n"
                       f"💰 Amount: **{float(value):,.0f} IRVUS**\n"
                       f"🔗 [Basescan Link](https://basescan.org/tx/{tx_hash})\n\n"
                       f"🚀 **TO THE MOON!**")
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                             json={"chat_id": GROUP_ID, "text": msg, "parse_mode": "Markdown"})
    except: pass

# --- 🤖 YAPAY ZEKA VE KOMUTLAR ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "💎 **IRVUS GLOBAL AI & BUY BOT**\n\n🇹🇷 AI ve Anlık Alımlar Aktif!\n🇺🇸 AI and Live Buys Active!"
    await update.message.reply_text(msg, parse_mode='Markdown')

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        url = f"https://api.geckoterminal.com/api/v2/networks/base/tokens/{CA}"
        r = requests.get(url, timeout=10).json()
        p = r['data']['attributes']['price_usd']
        await update.message.reply_text(f"💰 **IRVUS Price:** `${float(p):.8f}`")
    except: await update.message.reply_text("⚠️ Price error.")

async def ask_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query: return await update.message.reply_text("Soru yazın / Ask a question.")
    prompt = f"Date: 2026. Respond in the language of the question: {query}"
    try:
        url = f"https://text.pollinations.ai/{quote(prompt)}?model=openai"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                ans = await r.text()
                await update.message.reply_text(f"🤖 **Irvus AI:**\n\n{ans}")
    except: await update.message.reply_text("AI error.")

# --- 🚀 ANA ÇALIŞTIRICI ---
async def main():
    # Flask sunucusunu başlat
    Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))).start()
    
    # Botu en stabil ayarlarla kur
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Tüm Handlerları ekle
    application.add_handler(CommandHandler(["start", "yardim"], start))
    application.add_handler(CommandHandler(["fiyat", "price"], fiyat))
    application.add_handler(CommandHandler(["sor", "ask"], ask_cmd))
    
    # Botu uyandır ve ESKİ MESAJLARI TEMİZLE (drop_pending_updates)
    await application.initialize()
    await application.start()
    print(">>> BOT TÜM ÖZELLİKLERLE AKTİF!")
    await application.updater.start_polling(drop_pending_updates=True)
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
    
