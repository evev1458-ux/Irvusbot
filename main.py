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

# Bu değişken son işlemi hafızada tutar
last_tx_hash = None

# --- ALIM TAKİP FONKSİYONU ---
async def check_buys(context: ContextTypes.DEFAULT_TYPE):
    global last_tx_hash
    print("🦁 Alım takip sistemi devreye girdi...")
    
    while True:
        try:
            # Basescan/Etherscan V2 API sorgusu
            url = f"https://api.etherscan.io/v2/api?chainid=8453&module=account&action=tokentx&address={POOL_ADDRESS}&startblock=0&endblock=99999999&sort=desc&apikey={BASESCAN_API_KEY}"
            response = requests.get(url).json()
            
            if response.get('status') == '1':
                transactions = response.get('result', [])
                if transactions:
                    latest_tx = transactions[0]
                    tx_hash = latest_tx['hash']
                    
                    # Eğer yeni bir işlemse
                    if tx_hash != last_tx_hash:
                        if last_tx_hash is not None:
                            # USDC 6 decimaldir (10^6)
                            value = int(latest_tx['value']) / 1000000
                            
                            mesaj = (
                                f"🟢 **YENİ IRVUS ALIMI!** 🦁\n\n"
                                f"💰 **Tutar:** {value:.2f} USDC\n"
                                f"🔗 **İşlem:** [Basescan Linki](https://basescan.org/tx/{tx_hash})\n\n"
                                f"🚀 #IRVUS #BaseChain"
                            )
                            await context.bot.send_message(
                                chat_id=BUY_LOG_CHAT_ID, 
                                text=mesaj, 
                                parse_mode="Markdown", 
                                disable_web_page_preview=True
                            )
                        last_tx_hash = tx_hash
        except Exception as e:
            print(f"⚠️ Alım takip hatası: {e}")
        
        # 30 saniye bekle ve tekrar kontrol et
        await asyncio.sleep(30)

# --- BOT KOMUTLARI ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🦁 Irvus AI aktif! \n/sor, /ciz, /fiyat komutlarını kullanabilirsin. \nAlımlar otomatik takip ediliyor!")

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 $IRVUS Fiyatı: Dexscreener üzerinden güncel veriler çekiliyor...")

async def sor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = " ".join(context.args)
    if not user_input:
        await update.message.reply_text("🦁 Bana bir şey sormak için yanına yaz! Örn: /sor Irvus geleceği nedir?")
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
    # Buradaki .build() kısmı en sade haliyle kalmalı, hata vermemesi için
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Komutları Tanıt
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('fiyat', fiyat))
    application.add_handler(CommandHandler('sor', sor))
    application.add_handler(CommandHandler('ciz', ciz))
    
    # Alım takibi görevini başlat (Hata vermemesi için job_queue kontrolüyle)
    if application.job_queue:
        application.job_queue.run_once(check_buys, 5)
    else:
        print("❌ Hata: JobQueue başlatılamadı!")

    print("🤖 Irvus AI ve Alım Takibi Başlatıldı...")
    application.run_polling()
    
