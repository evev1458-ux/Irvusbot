import os, requests, asyncio, time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS AI ONLINE", 200

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAGC37E6oeacOL1fjtUWqFoN2sXCVlIplOc" 
CA_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
HF_TOKEN = "Hf_VzFKUkIElGkRTDWwEwLPwPPOOmwWwwBqNq"

# Daha stabil bir model seçtik
CHAT_MODEL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"

X_ADRESI = "https://x.com/IRVUSTOKEN"
WEB_SITESI = "https://www.irvustoken.xyz"
LOGO_URL = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg" 

HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}
LAST_PRICE_DATA = {"price": "0.00", "change": "0", "time": 0}

# --- 3. SOHBET ZEKASI (MESAJ SORUNUNU ÇÖZEN KISIM) ---

async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    user_text = update.message.text
    
    # Botun ismi geçerse veya bota yanıt verilirse çalışır
    is_reply = update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id
    if "irvus" in user_text.lower() or is_reply:
        # Botun düşündüğünü gösteren "yazıyor..." efekti
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        try:
            # Yapay zekaya kimlik kazandıran özel komut (Prompt)
            prompt = f"<|system|>\nSen Irvus Token'ın resmi asistanısın. Türkçe, samimi ve kısa cevaplar ver. Sloganımız: Irvus ile gelecek bugün başlıyor!</s>\n<|user|>\n{user_text}</s>\n<|assistant|>\n"
            
            # API isteği (20 saniye bekleme süresi eklendi)
            response = requests.post(CHAT_MODEL, headers=HEADERS, json={"inputs": prompt, "parameters": {"max_new_tokens": 150, "temperature": 0.7}}, timeout=20)
            
            if response.status_code == 200:
                res_data = response.json()
                # Modelden gelen temiz cevabı ayıklıyoruz
                bot_response = res_data[0].get('generated_text', "").split("<|assistant|>")[-1].strip()
                
                if bot_response:
                    await update.message.reply_text(f"🤖 **Irvus AI:** {bot_response}")
                    return

            # API hata verirse veya boş dönerse yedek akıllı mesaj
            await update.message.reply_text("💎 Irvus burada! Şu an sistemlerimi optimize ediyorum ama seni duyuyorum. Ne sormuştun?")
            
        except Exception as e:
            print(f"Hata detayı: {e}")
            await update.message.reply_text("💎 Irvus her zaman seninle! Geleceği birlikte inşa ediyoruz.")

# --- DİĞER KOMUTLAR (Aynen Kalıyor) ---
# ... (start, fiyat ve ciz fonksiyonların zaten çalıştığı için onları bozma)
