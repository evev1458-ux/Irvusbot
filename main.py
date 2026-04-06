import os, requests, asyncio, time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS AI IS ALIVE", 200

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAGC37E6oeacOL1fjtUWqFoN2sXCVlIplOc" 
CA_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
HF_TOKEN = "Hf_VzFKUkIElGkRTDWwEwLPwPPOOmwWwwBqNq"

# Stabil Sohbet Modeli
CHAT_MODEL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"

X_ADRESI = "https://x.com/IRVUSTOKEN"
WEB_SITESI = "https://www.irvustoken.xyz"
LOGO_URL = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg" 

HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}
LAST_PRICE_DATA = {"price": "0.00", "change": "0", "time": 0}

# --- 3. SOHBET ZEKASI ---

async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    user_text = update.message.text
    
    is_reply = update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id
    if "irvus" in user_text.lower() or is_reply:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        try:
            prompt = f"<|system|>\nSen Irvus Token asistanısın. Kısa, samimi cevap ver.</s>\n<|user|>\n{user_text}</s>\n<|assistant|>\n"
            response = requests.post(CHAT_MODEL, headers=HEADERS, json={"inputs": prompt}, timeout=15)
            
            if response.status_code == 200:
                res_data = response.json()
                bot_response = res_data[0].get('generated_text', "").split("<|assistant|>")[-1].strip()
                if bot_response:
                    await update.message.reply_text(f"🤖 **Irvus AI:** {bot_response}")
                    return
            
            await update.message.reply_text("💎 Irvus burada! Geleceği birlikte inşa ediyoruz. Ne sormuştun?")
        except:
            await update.message.reply_text("💎 Irvus her zaman seninle! Mesajını aldım, sistemlerimi güncelliyorum.")

# --- 4. ASLA HATA VERMEYEN ÇİZİM MOTORU ---

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt: return await update.message.reply_text("❌ Örn: `/ciz gold lion` ")
    
    wait_msg = await update.message.reply_text("🎨 **Irvus AI hayal ediyor, lütfen bekle...**")
    
    try:
        # Pollinations AI: Bekleme sırası yok, meşgul uyarısı yok!
        encoded_prompt = prompt.replace(" ", "%20")
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={int(time.time())}"
        
        # Resmi Telegram'a gönder
        await update.message.reply_photo(photo=image_url, caption=f"🖼 **Irvus AI Sanat Eseri:**\n`{prompt}`", parse_mode='Markdown')
        await wait_msg.delete() # "Çiziyorum" mesajını sil
    except Exception as e:
        await update.message.reply_text(f"❌ Görsel şu an oluşturulamadı. Lütfen tekrar dene.")

# --- 5. DİĞER KOMUTLAR ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (f"💎 **Irvus AI Dünyasına Hoş Geldiniz!**\n\n"
           f"Ben Irvus AI. Bana her şeyi sorabilir, fiyat öğrenebilir veya hayallerini çizdirebilirsin.\n\n"
           f"📄 **CA:** `{CA_ADRESI}`")
    kb = [[InlineKeyboardButton("🌐 Web", url=WEB_SITESI), InlineKeyboardButton("🐦 X", url=X_ADRESI)],
          [InlineKeyboardButton("📊 Grafik", url=f"https://dexscreener.com/base/{CA_ADRESI}")]]
    try:
        await update.message.reply_photo(photo=LOGO_URL, caption=msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    except:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global LAST_PRICE_DATA
    if time.time() - LAST_PRICE_DATA["time"] < 90 and LAST_PRICE_DATA["price"] != "0.00":
        return await update.message.reply_text(f"💰 **Fiyat:** `${LAST_PRICE_DATA['price']}`\n📈 **24s:** `%{LAST_PRICE_DATA['change']}`")
    try:
        url = f"https://api.dexscreener.com/latest/dex/search?q={CA_ADRESI}"
        res = requests.get(url, headers={"User-Agent":"Mozilla"}, timeout=10).json()
        p = next((x for x in res.get('pairs', []) if x['chainId'] == 'base'), None)
        if p:
            LAST_PRICE_DATA = {"price": p['priceUsd'], "change": p['priceChange']['h24'], "time": time.time()}
            await update.message.reply_text(f"💰 **Fiyat:** `${p['priceUsd']}`\n📈 **24s:** `%{p['priceChange']['h24']}`")
    except:
        await update.message.reply_text("⚠️ API şu an yoğun.")

# --- 6. ANA MOTOR ---
async def main():
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
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
        
