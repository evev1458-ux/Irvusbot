import os, requests, asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# AYARLARI RENDER'DAN ALIYORUZ
TOKEN = os.getenv("BOT_TOKEN")
BASESCAN_API_KEY = os.getenv("API_KEY")
POOL_ADDRESS = os.getenv("PAIR_ADDRESS")
BUY_LOG_CHAT_ID = os.getenv("CHAT_ID")

last_tx_hash = None

async def check_buys(context: ContextTypes.DEFAULT_TYPE):
    global last_tx_hash
    print("🦁 Takip başladı...")
    while True:
        try:
            url = f"https://api.etherscan.io/v2/api?chainid=8453&module=account&action=tokentx&address={POOL_ADDRESS}&startblock=0&endblock=99999999&sort=desc&apikey={BASESCAN_API_KEY}"
            response = requests.get(url).json()
            if response.get('status') == '1' and response.get('result'):
                latest_tx = response['result'][0]
                tx_hash = latest_tx['hash']
                if tx_hash != last_tx_hash:
                    if last_tx_hash:
                        value = int(latest_tx['value']) / 1000000
                        mesaj = f"🟢 **YENİ IRVUS ALIMI!** 🦁\n\n💰 **Tutar:** {value:.2f} USDC\n🔗 [Basescan](https://basescan.org/tx/{tx_hash})"
                        await context.bot.send_message(chat_id=BUY_LOG_CHAT_ID, text=mesaj, parse_mode="Markdown")
                    last_tx_hash = tx_hash
        except: pass
        await asyncio.sleep(30)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', lambda u, c: u.message.reply_text("🦁 Irvus Aktif!")))
    if app.job_queue: app.job_queue.run_once(check_buys, 5)
    app.run_polling()
    
