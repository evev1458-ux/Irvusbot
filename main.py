import os
import requests
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- AYARLAR ---
TOKEN = "6815349544:AAH95fWp5n9k8eF68PAn9V8Vf56Gid9LgH0"
BASESCAN_API_KEY = "MG1FPDHVDA5FW76AJ3F88VNTHQACKI6KFA"
POOL_ADDRESS = "0x074900A4058d84033C0b87441B3299F72D852077"
BUY_LOG_CHAT_ID = "-1002393767346"

last_tx_hash = None

# --- ALIM TAKİP MODÜLÜ ---
async def check_buys(context: ContextTypes.DEFAULT_TYPE):
    global last_tx_hash
    while True:
        try:
            url = f"https://api.etherscan.io/v2/api?chainid=8453&module=account&action=tokentx&address={POOL_ADDRESS}&startblock=0&endblock=99999999&sort=desc&apikey={BASESCAN_API_KEY}"
            response = requests.get(url).json()
            
            if response.get('status') == '1':
                transactions = response.get('result', [])
                if transactions:
                    latest_tx = transactions[0]
                    tx_hash = latest_tx['hash']
                    
                    if tx_hash != last_tx_hash:
                        if last_tx_hash is not None:
                            value = int(latest_tx['value']) / (10**6) # USDC 6 decimal
                            mesaj = (
                                f"🟢 **YENİ IRVUS ALIMI!** 🦁\n\n"
                                f"💰 **Tutar:** {value:.2f} USDC\n"
                                f"🔗 **İşlem:** [Basescan Linki](https://basescan.org/tx/{tx_hash})\n\n"
                                f"🚀 #IRVUS #BaseChain"
                            )
                            await context.bot.send_message(chat_id=BUY_LOG_CHAT_ID, text=mesaj, parse_mode="Markdown", disable_web_page_preview=True)
                        last_tx_hash = tx_hash
        except Exception as e:
            print(f"Alım takip hatası: {e}")
        await asyncio.sleep(30)

# --- BOT KOMUTLARI ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🦁 Irvus AI aktif! /sor, /ciz, /fiyat komutlarını kullanabilirsin. Alımlar otomatik takip ediliyor.")

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Basit bir fiyat çekme mantığı (Dexscreener API kullanılabilir)
    await update.message.reply_text("📊 $IRVUS Fiyatı: Güncel veriler Dexscreener üzerinden kontrol ediliyor...")

async def sor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = " ".join(context.args)
    if not user_input:
        await update.message.reply_text("🦁 Bana bir şey sormak için komutun yanına sorunu yaz! Örn: /sor Irvus nedir?")
        return
    await update.message.reply_text(f"🧠 '{user_input}' sorunu yapay zekaya iletiyorum...")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = " ".join(context.args)
    if not user_input:
        await update.message.reply_text("🎨 Ne çizmemi istersin? Örn: /ciz aslan logolu coin")
        return
    await update.message.reply_text(f"🎨 '{user_input}' hayalini tuvale döküyorum...")

# --- ANA ÇALIŞTIRICI ---
if __name__ == '__main__':
    # .job_queue(True) ekleyerek Render hatasını çözüyoruz
    application = ApplicationBuilder().token(TOKEN).job_queue(True).build()
    
    # Komutları Tanıtıyoruz
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('fiyat', fiyat))
    application.add_handler(CommandHandler('sor', sor))
    application.add_handler(CommandHandler('ciz', ciz))
    
    # Alım takibini arka planda başlatıyoruz
    application.job_queue.run_once(check_buys, 0)
    
    print("🤖 Irvus AI ve Alım Takibi Başlatıldı...")
    application.run_polling()
    
