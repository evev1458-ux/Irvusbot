import os, asyncio, requests, time, aiohttp
import xml.etree.ElementTree as ET
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib.parse import quote

# --- 1. WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS GLOBAL SYSTEM: ONLINE", 200

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAFP8Pmc0p24oQnDEiL6SwMTgL6tr3HIPss"
CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
LOGO = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"

# --- 3. KOMUTLAR ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Butonları garantili şekilde gönderen start komutu"""
    # Mesajı Markdown hatası vermemesi için en sade hale getirdim
    msg = (f"💎 **IRVUS GLOBAL AI (2026)**\n\n"
           f"🇹🇷 Hoş geldiniz! Canlı yapay zeka asistanı.\n"
           f"🇺🇸 Welcome! Live AI Assistant.\n\n"
           f"📄 CA: `{CA}`")
    
    # Buton dizilimini tek tek listeler içine alarak en stabil hale getirdim
    kb = [
        [InlineKeyboardButton("🌐 Website", url="https://www.irvustoken.xyz")],
        [InlineKeyboardButton("🐦 Twitter (X)", url="https://x.com/IRVUSTOKEN")]
    ]
    reply_markup = InlineKeyboardMarkup(kb)

    try:
        # Önce logolu dene
        await update.message.reply_photo(
            photo=LOGO, 
            caption=msg, 
            reply_markup=reply_markup, 
            parse_mode='Markdown'
        )
    except Exception as e:
        # Logo hatası olursa sadece metni gönder (Butonlar mutlaka gider)
        await update.message.reply_text(
            msg, 
            reply_markup=reply_markup, 
            parse_mode='Markdown'
        )

# --- 4. ANA ÇALIŞTIRICI ---
async def main():
    # Web sunucusunu başlat
    Thread(target=run_web, daemon=True).start()
    
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Komutları ekle
    application.add_handler(CommandHandler(["start", "star"], start))
    # Diğer komutları (sor, fiyat, ciz) buraya daha önce verdiğim gibi ekleyebilirsin
    
    print(">>> BOT AKTIF!")
    # drop_pending_updates=True eski hatalı mesajları temizler
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)
    while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except:
        pass
        
