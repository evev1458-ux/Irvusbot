import os, asyncio, requests, time, aiohttp
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
def home(): return "IRVUS ALCHEMY SYSTEM: LIVE", 200

# --- 🟢 ANLIK ALIM KAPISI (WEBHOOK) ---
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if data and 'event' in data:
        # Alchemy sinyalini arka planda işle (Botun donmaması için)
        Thread(target=process_buy_signal, args=(data,)).start()
    return jsonify({"status": "received"}), 200

def process_buy_signal(data):
    try:
        activity = data['event'].get('activity', [])
        for act in activity:
            tx_hash = act.get('hash')
            value = act.get('value')
            asset = act.get('asset', 'IRVUS')
            from_addr = act.get('fromAddress', 'Unknown')
            
            # Sadece alımları (transferleri) yakala
            if value and float(value) > 0:
                msg = (f"🟢 **NEW IRVUS BUY!**\n\n"
                       f"💰 Amount: **{float(value):,.0f} {asset}**\n"
                       f"👤 Buyer: `{from_addr[:6]}...{from_addr[-4:]}`\n"
                       f"🔗 [Basescan](https://basescan.org/tx/{tx_hash})\n\n"
                       f"🚀 **TO THE MOON!**")
                
                # Telegram'a saniyesinde fırlat
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                              json={"chat_id": GROUP_ID, "text": msg, "parse_mode": "Markdown"})
    except: pass

# --- 🤖 YAPAY ZEKA VE KOMUTLAR (TR/EN) ---
async def start(update, context):
    msg = (f"💎 **IRVUS GLOBAL AI & BUY BOT**\n\n"
           f"🇹🇷 Anlık alım takibi ve AI aktif!\n"
           f"🇺🇸 Live buy tracking and AI active!\n\n"
           f"📄 CA: `{CA}`")
    kb = [[InlineKeyboardButton("🌐 Website", url="https://www.irvustoken.xyz")]]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def ask_cmd(update, context):
    query = " ".join(context.args)
    if not query: return await update.message.reply_text("🇹🇷 Lütfen soru yazın. / 🇺🇸 Please ask a question.")
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    prompt = f"Date: April 9, 2026. Respond in the language of the question. User says: {query}"
    try:
        url = f"https://text.pollinations.ai/{quote(prompt)}?model=openai"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=25) as r:
                ans = await r.text()
                await update.message.reply_text(f"🤖 **Irvus AI:**\n\n{ans}")
    except: await update.message.reply_text("System busy.")

async def fiyat(update, context):
    try:
        url = f"https://api.geckoterminal.com/api/v2/networks/base/tokens/{CA}"
        r = requests.get(url, timeout=10).json()
        p = r['data']['attributes']['price_usd']
        await update.message.reply_text(f"💰 **IRVUS:** `${float(p):.8f}`")
    except: await update.message.reply_text("⚠️ Fiyat çekilemedi.")

# --- SİSTEM BAŞLATICI ---
def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

async def main():
    Thread(target=run_web, daemon=True).start()
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Komutları Tanımla (Aliaslı)
    application.add_handler(CommandHandler(["start", "star"], start))
    application.add_handler(CommandHandler(["sor", "ask"], ask_cmd))
    application.add_handler(CommandHandler(["fiyat", "price"], fiyat))
    
    async with application:
        await application.initialize()
        await application.start()
        print(">>> SISTEM ALCHEMY ILE ANLIK MODDA!")
        await application.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    try: asyncio.run(main())
    except: pass
        
