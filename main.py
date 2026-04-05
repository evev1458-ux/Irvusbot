import os, requests, asyncio, time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS SMART AI ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAESXIZLT6HbS3CGeT-sT-HJcgvFuJF8ff0" 
CA_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
HF_TOKEN = "Hf_VzFKUkIElGkRTDWwEwLPwPPOOmwWwwBqNq"

# DAHA ZEKİ SOHBET MODELİ (Mistral-7B)
CHAT_MODEL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
IMAGE_MODEL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"

HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}
LAST_PRICE_DATA = {"price": "0.00", "change": "0", "time": 0}

# --- 3. SOHBET FONKSİYONU ---

async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if not user_text: return
    
    # Botun isminin geçtiği veya bota yanıt verildiği durumlar
    is_reply = update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id
    if "irvus" in user_text.lower() or is_reply:
        try:
            # Mistral'e uygun özel prompt (Daha insansı cevap için)
            prompt = f"<s>[INST] Sen Irvus Token'ın resmi yapay zeka asistanısın. Kısa ve samimi bir cevap ver: {user_text} [/INST]"
            
            res = requests.post(CHAT_MODEL, headers=HEADERS, json={"inputs": prompt}, timeout=15).json()
            
            # Yanıtı temizleme (Mistral bazen promptu da döndürür)
            full_text = res[0].get('generated_text', "")
            bot_response = full_text.split("[/INST]")[-1].strip()
            
            if not bot_response or len(bot_response) < 2:
                bot_response = "Irvus her zaman burada! Senin için ne yapabilirim? 💎"
            
            await update.message.reply_text(f"🤖 **Irvus AI:** {bot_response}")
        except:
            await update.message.reply_text("💎 Irvus ile gelecek bugün başlıyor! Bir şey mi sormuştun?")

# --- 4. KOMUTLAR (Aynen Kalıyor) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = "💎 **Irvus AI Dünyasına Hoş Geldiniz!**\n\nBana Irvus ile ilgili her şeyi sorabilirsin!"
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global LAST_PRICE_DATA
    simdi = time.time()
    if simdi - LAST_PRICE_DATA["time"] < 90 and LAST_PRICE_DATA["price"] != "0.00":
        msg = f"💰 **Fiyat:** `${LAST_PRICE_DATA['price']}`\n📈 **24s:** `%{LAST_PRICE_DATA['change']}`"
        return await update.message.reply_text(msg, parse_mode='Markdown')
    
    try:
        url = f"https://api.dexscreener.com/latest/dex/search?q={CA_ADRESI}"
        res = requests.get(url, headers={"User-Agent":"Mozilla"}, timeout=10).json()
        p = next((x for x in res.get('pairs', []) if x['chainId'] == 'base'), None)
        if p:
            f_usd, deg = p.get('priceUsd'), p.get('priceChange', {}).get('h24', '0')
            LAST_PRICE_DATA = {"price": f_usd, "change": deg, "time": simdi}
            await update.message.reply_text(f"💰 **Fiyat:** `${f_usd}`\n📈 **24s:** `%{deg}`", parse_mode='Markdown')
    except:
        await update.message.reply_text("⚠️ API yoğun.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt: return await update.message.reply_text("❌ Örn: `/ciz aslan` ")
    await update.message.reply_text("🎨 Çiziyorum...")
    try:
        response = requests.post(IMAGE_MODEL, headers=HEADERS, json={"inputs": prompt}, timeout=30)
        await update.message.reply_photo(photo=response.content, caption=f"🖼 **Irvus AI:** {prompt}")
    except:
        await update.message.reply_text("❌ Hata oluştu.")

# --- 5. ANA MOTOR ---
async def main():
    Thread(target=run_web, daemon=True).start()
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    application.add_handler(CommandHandler(["ciz", "draw"], ciz))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat_ai))
    
    async with application:
        await application.initialize()
        await application.start()
        print(">>> IRVUS AI AKTIF")
        await application.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    try: asyncio.run(main())
    except: pass
                      
