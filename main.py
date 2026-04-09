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

# --- 🟢 ALCHEMY WEBHOOK (ANLIK ALIM) ---
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
                       f"🚀 **HAYIRLI OLSUN!**")
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                             json={"chat_id": GROUP_ID, "text": msg, "parse_mode": "Markdown"})
    except: pass

# --- 🤖 TÜM KOMUTLAR ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (f"💎 **IRVUS GLOBAL AI & BUY BOT**\n\n"
           f"🇹🇷 Yapay Zeka, Çizim, Fiyat ve Anlık Alımlar Aktif!\n"
           f"🇺🇸 AI, Draw, Price and Live Buys Active!\n\n"
           f"📄 CA: `{CA}`")
    kb = [
        [InlineKeyboardButton("🌐 Website", url="https://www.irvustoken.xyz")],
        [InlineKeyboardButton("📊 Chart", url=f"https://dexscreener.com/base/{CA}")]
    ]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

# FIYAT KOMUTU (GECKOTERMINAL BAĞLANTILI)
async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        url = f"https://api.geckoterminal.com/api/v2/networks/base/tokens/{CA}"
        r = requests.get(url, timeout=10).json()
        data = r['data']['attributes']
        p = data['price_usd']
        v = data['volume_usd']['h24']
        m = data['fdv_usd']
        
        msg = (f"💰 **IRVUS TOKEN PRICE**\n\n"
               f"💵 Price: `${float(p):.8f}`\n"
               f"📊 24h Vol: `${float(v):,.0f}`\n"
               f"💎 MCap
        
