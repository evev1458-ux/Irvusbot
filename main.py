import os
import time
import requests
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =========================
# 🔐 TELEGRAM BİLGİLERİ
# =========================

TOKEN = 8621050385:AAHIB0lWjzkDtgb2XJq32YmOg5Ggb_pZFZg"
CHAT_ID = `-1002393767346`"

# =========================
# ⚙️ TOKEN / NETWORK
# =========================

CA_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
BASE_RPC = "https://mainnet.base.org"

LAST_BLOCK = 0

# =========================
# 🌐 FLASK (Render awake)
# =========================

app = Flask(__name__)

@app.route("/")
def home():
    return "IRVUS BOT ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# =========================
# 📩 TELEGRAM SEND
# =========================

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": msg
    }
    try:
        requests.post(url, data=data, timeout=10)
    except:
        pass

# =========================
# 🔍 BLOCK CHECK
# =========================

def get_latest_block():
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_blockNumber",
        "params": [],
        "id": 1
    }
    res = requests.post(BASE_RPC, json=payload).json()
    return int(res["result"], 16)

def get_block(block):
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBlockByNumber",
        "params": [hex(block), True],
        "id": 1
    }
    res = requests.post(BASE_RPC, json=payload).json()
    return res.get("result", {}).get("transactions", [])

# =========================
# 🚨 BUY DETECTOR
# =========================

def check_chain():
    global LAST_BLOCK

    try:
        latest = get_latest_block()

        if LAST_BLOCK == 0:
            LAST_BLOCK = latest - 2

        for b in range(LAST_BLOCK + 1, latest + 1):
            txs = get_block(b)

            for tx in txs:
                to = tx.get("to")

                if to and CA_ADRESI.lower() in to.lower():

                    value = int(tx["value"], 16) / 10**18

                    msg = f"""
🚀 IRVUS ON-CHAIN ACTIVITY

💰 ETH Value: {value:.4f}
👤 Wallet: {tx['from'][:6]}...{tx['from'][-4:]}

🔗 https://basescan.org/tx/{tx['hash']}
"""

                    send_telegram(msg)

        LAST_BLOCK = latest

    except Exception as e:
        print("Hata:", e)

# =========================
# 🔁 LOOP
# =========================

def loop():
    while True:
        check_chain()
        time.sleep(12)

# =========================
# 🤖 TELEGRAM COMMAND
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("IRVUS BOT AKTİF 🚀")

# =========================
# 🚀 START
# =========================

def main():
    Thread(target=run_web).start()
    Thread(target=loop).start()

    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))

    app_bot.run_polling()

if __name__ == "__main__":
    main()
