import os, asyncio, requests, json, aiohttp, random
from flask import Flask, request, jsonify
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib.parse import quote

TOKEN = "8621050385:AAHnY8zSX9VUhD3bm-v44sHaMWzxVWzq0_c"
GROUP_ID = -1002315757919
CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"

app = Flask(__name__)

# --- WEBHOOK (SADECE ALIMLAR) ---
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if data:
        # Mesajı gönderen fonksiyonu burada tetikleyeceğiz
        # (Telegram bot nesnesine global erişimle)
        asyncio.run_coroutine_threadsafe(send_buy_msg(data), bot_loop)
    return "ok", 200

# Telegram Bot Nesnesini Global Tanımla
bot_instance = None
bot_loop = None

async def send_buy_msg(data):
    global bot_instance
    try:
        # Alım verisini ayıkla
        acts = data.get('event', {}).get('activity', []) or [data]
        for a in acts:
            v = a.get('value') or a.get('amount')
            if v and float(v) > 0:
                tx = a.get('hash') or "0x..."
                msg = f"🟢 **NEW BUY!**\n💰 **{float(v):,.0f} IRVUS**\n🔗 [Basescan](https://basescan.org/tx/{tx})"
                await bot_instance.bot.send_message(chat_id=GROUP_ID, text=msg, parse_mode="Markdown")
    except: pass

# --- TELEGRAM KOMUTLARI ---
async def start(u, c):
    await u.message.reply_text("💎 **IRVUS BOT ONLINE!**")

async def ask(u, c):
    q = " ".join(c.args)
    if not q: return
    async with aiohttp.ClientSession() as s:
        async with s.get(f"https://text.pollinations.ai/{quote(q)}?model=openai") as r:
            ans = await r.text()
            await u.message.reply_text(f"🤖 **Irvus AI:**\n\n{ans}")

# --- BAŞLATICILAR ---
async def main():
    global bot_instance, bot_loop
    bot_loop = asyncio.get_event_loop()
    bot_instance = ApplicationBuilder().token(TOKEN).build()
    bot_instance.add_handler(CommandHandler("start", start))
    bot_instance.add_handler(CommandHandler("sor", ask))
    
    # Botu başlat
    await bot_instance.initialize()
    await bot_instance.start()
    await bot_instance.updater.start_polling(drop_pending_updates=True)
    
    # Flask sunucusunu botla beraber başlat
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    asyncio.run(main())
    
