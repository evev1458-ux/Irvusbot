import os
import requests
import asyncio
import time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- 1. WEB SUNUCUSU (7/24 Uyanık Tutmak İçin) ---
app = Flask(__name__)

@app.route('/')
def home(): 
    return "IRVUS SISTEM ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. SABİT AYARLAR VE LİNKLER ---
TOKEN = "8621050385:AAHAySA0SXbAP4G0KwcnCKGLkYs2yf-OeQU" 
CA_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
HF_TOKEN = "Hf_VzFKUkIElGkRTDWwEwLPwPPOOmwWwwBqNq"
HF_API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"

X_ADRESI = "https://x.com/IRVUSTOKEN"
WEB_SITESI = "https://www.irvustoken.xyz"
LOGO_URL = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg" 

LAST_PRICE_DATA = {"price": "0.00", "change": "0", "time": 0}
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# --- 3. BOT FONKSİYONLARI ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "💎 **Irvus Token Dünyasına Hoş Geldiniz!**\n\n"
        "Ben **Irvus AI**, topluluğunuzun sanat ve finans asistanıyım.\n\n"
        f"📄 **Kontrat Adresi (Base):**\n`{CA_ADRESI}`\n\n"
        "🚀 **Komutlar:**\n"
        "🔹 `/fiyat` - Anlık $IRVUS verilerini getirir.\n"
        "🔹 `/ciz [kelime]` - Yapay zeka ile görsel oluşturur.\n\n"
        "**Resmi Bağlantılarımız:**"
    )
    keyboard = [
        [InlineKeyboardButton("🌐 Web Sitesi", url=WEB_SITESI), InlineKeyboardButton("🐦 X (Twitter)", url=X_ADRESI)],
        [InlineKeyboardButton("📊 Canlı Grafik (Base)", url=f"https://dexscreener.com/base/{CA_ADRESI}")]
    ]
    try:
        await update.message.reply_photo(photo=LOGO_URL, caption=welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    except:
        await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global LAST_PRICE_DATA
    simdi = time.time()
    
    if simdi - LAST_PRICE_DATA["time"] < 90 and LAST_PRICE_DATA["price"] != "0.00":
        msg = (f"💎 **$IRVUS Güncel Durum**\n"
               f"━━━━━━━━━━━━━━━━━━\n"
               f"💰 Fiyat: `${LAST_PRICE_DATA['price']}`\n"
               f"📈 24s Değişim: `%{LAST_PRICE_DATA['change']}`\n"
               f"━━━━━━━━━━━━━━━━━━\n"
               f"ℹ️ *Veri otomatik güncelleniyor.*")
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📊 Grafiği Görüntüle", url=f"https://dexscreener.com/base/{CA_ADRESI}")]])
        return await update.message.reply_text(msg, reply_markup=kb, parse_mode='Markdown')

    f_usd, degisim = None, "0"
    try:
        url = f"https://api.dexscreener.com/latest/dex/search?q={CA_ADRESI}"
        res = requests.get(url, headers=HEADERS, timeout=12).json()
        p = next((x for x in res.get('pairs', []) if x['chainId'] == 'base'), None)
        if p:
            f_usd = p.get('priceUsd')
            degisim = p.get('priceChange', {}).get('h24', '0')
            LAST_PRICE_DATA = {"price": f_usd, "change": degisim, "time": simdi}
    except: pass

    if f_usd:
        msg = (f"💎 **$IRVUS Güncel Durum**\n"
               f"━━━━━━━━━━━━━━━━━━\n"
               f"💰 Fiyat: `${f_usd}`\n"
               f"📈 24s Değişim: `%{deg
                                   
