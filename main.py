import os
import requests
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- AYARLAR ---
TOKEN = "6815349544:AAH95fWp5n9k8eF68PAn9V8Vf56Gid9LgH0"
BASESCAN_API_KEY = "MG1FPDHVDA5FW76AJ3F88VNTHQACKI6KFA"
POOL_ADDRESS = "0x074900A4058d84033C0b87441B3299F72D852077"
BUY_LOG_CHAT_ID = "-1002393767346" # Alımların düşeceği grup ID

last_tx_hash = None

# --- ALIM TAKİP MODÜLÜ (ARKA PLAN) ---
async def check_buys(context: ContextTypes.DEFAULT_TYPE):
    global last_tx_hash
    while True:
        try:
            # Etherscan API V2 ile Base zinciri sorgusu
            url = f"https://api.etherscan.io/v2/api?chainid=8453&module=account&action=tokentx&address={POOL_ADDRESS}&startblock=0&endblock=99999999&sort=desc&apikey={BASESCAN_API_KEY}"
            response = requests.get(url).json()
            
            if response.get('status') == '1':
                transactions = response.get('result', [])
                if transactions:
                    latest_tx = transactions[0]
                    tx_hash = latest_tx['hash']
                    
                    if tx_hash != last_tx_hash:
                        if last_tx_hash is not None:
                            # USDC 6 decimaldir
                            value = int(latest_tx['value']) / (10**6)
                            
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
            print(f"Alım takip hatası: {e}")
        
        # 30 saniye bekle ve tekrar kontrol et
        await asyncio.sleep(30)

# --- MEVCUT KOMUTLARIN (ÖRNEK) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🦁 Irvus AI aktif! Sorabilir, çizdirebilir veya alımları takip edebilirsin.")

# Buraya kendi mevcut 'fiyat', 'sor', 'çiz' fonksiyonlarını ekleyebilirsin.

# --- ANA ÇALIŞTIRICI ---
if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Komutları ekle
    application.add_handler(CommandHandler('start', start))
    # application.add_handler(CommandHandler('fiyat', fiyat)) # Kendi fonksiyonunu buraya ekle
    
    # KRİTİK NOKTA: Alım takibini botla birlikte başlatır
    application.job_queue.run_once(check_buys, 0)
    
    print("🤖 Irvus AI ve Alım Takibi Başlatıldı...")
    application.run_polling()
    
