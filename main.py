import os
import logging
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler

# --- LOGLAMA ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- FLASK (BOTUN UYUMAMASI İÇİN) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot aktif ve çalışıyor!"

def run_web_server():
    # Render'ın verdiği portu kullanmalıyız
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web_server)
    t.start()

# --- TELEGRAM BOT MANTIĞI ---
TOKEN = "8621050385:AAESXIZLT6HbS3CGeT-sT-HJcgvFuJF8ff0"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Render üzerinde çalışan botunuz hazır! 🚀")

async def cevapla(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        text = update.message.text.lower()
        if "selam" in text:
            await update.message.reply_text("Selam! Render sunucusundan cevap veriyorum. 👋")
        else:
            await update.message.reply_text("Mesajını aldım. 👍")

# --- ANA ÇALIŞTIRICI ---
if __name__ == '__main__':
    # 1. Web sunucusunu başlat (Render'ı kandırmak için)
    keep_alive()
    
    # 2. Botu başlat
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), cevapla))
    
    print("Bot ve Web Sunucusu yayında...")
    application.run_polling()
  
