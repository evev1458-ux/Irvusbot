import os, requests, asyncio, time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. WEB SUNUCUSU (7/24 Uyanık Tutmak İçin) ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS AI ONLINE", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAESXIZLT6HbS3CGeT-sT-HJcgvFuJF8ff0" 
CA_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
HF_TOKEN = "Hf_VzFKUkIElGkRTDWwEwLPwPPOOmwWwwBqNq"

# GÖRSEL VE SOHBET MODELLERİ
IMAGE_MODEL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
CHAT_MODEL = "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill"

X_ADRESI = "https://x.com/IRVUSTOKEN"
WEB_SITESI = "https://www.irvustoken.xyz"
LOGO_URL = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg" 

HEADERS = {"User-Agent": "Mozilla/5.0", "Authorization": f"Bearer {HF_TOKEN}"}
LAST_PRICE_DATA = {"price": "0.00", "change": "0", "time": 0}

# --- 3. SOHBET FONKSİYONU (Irvus AI Zekası) ---

async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Sadece botun adı geçerse veya bota cevap verilirse çalışır
    user_text = update.message.text
    if not user_text: return
    
    # Botun isminin geçtiği veya bota yanıt verildiği durumlar
    is_reply = update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id
    if "irvus" in user_text.lower() or is_reply:
        try:
            # Hugging Face Chat API
            payload = {"inputs": user_text}
            res = requests.post(CHAT_MODEL, headers=HEADERS, json=payload, timeout=10).json()
            
            # Cevabı alalım
            bot_response = res[0].get('generated_text', "Geleceği inşa ediyorum, şu an biraz meşgulüm!")
            
            # Eğer cevap boşsa yedek bir Irvus mesajı ver
            if not bot_response: bot_response = "Irvus Token ile Base ağında devrim yapıyoruz!"
            
            await update.message.reply_text(f"🤖 **Irvus AI:** {bot_response}")
        except:
            # Hata durumunda (API yoğunsa) klasik bir Irvus cevabı ver
            await update.message.reply_text("💎 Irvus her zaman burada! Ne sormuştun?")

# --- 4. KOMUTLAR ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ca = CA_ADRESI
    msg = (f"💎 **Irvus AI Dünyasına Hoş Geldiniz!**\n\n"
           f"Ben Irvus Token'ın yapay zeka asistanıyım. Benimle grupta sohbet edebilir, fiyat sorabilir veya hayallerini çizdirebilirsin.\n\n"
           f"📄 **CA:** `{ca}`\n\n"
           f"🔹 `/fiyat` - Güncel piyasa verileri.\n"
           f"🔹 `/ciz [kelime]` - AI Görsel oluşturma.")
    
    kb = [[InlineKeyboardButton("🌐 Web", url=WEB_SITESI), InlineKeyboardButton("🐦 X", url=X_ADRESI)],
          [InlineKeyboardButton("📊 Grafik", url=f"https://dexscreener.com/base/{ca}")]]
    
    try:
        await update.message.reply_photo(photo=LOGO_URL, caption=msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    except:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global LAST_PRICE_DATA
    simdi = time.time()
    
    if simdi - LAST_PRICE_DATA["time"] < 90 and LAST_PRICE_DATA["price"] != "0.00":
        msg = (f"💎 **$IRVUS Güncel Durum**\n━━━━━━━━━━━━━━━━━━\n💰 Fiyat: `${LAST_PRICE_DATA['price']}`\n📈 24s Değişim: `%{LAST_PRICE_DATA['change']}`\n━━━━━━━━━━━━━━━━━━")
        return await update.message.reply_text(msg, parse_mode='Markdown')

    try:
        url = f"https://api.dexscreener.com/latest/dex/search?q={CA_ADRESI}"
        res = requests.get(url, headers={"User-Agent":"Mozilla"}, timeout=10).json()
        p = next((x for x in res.get('pairs', []) if x['chainId'] == 'base'), None)
        if p:
            f_usd, deg = p.get('priceUsd'), p.get('priceChange', {}).get('h24', '0')
            LAST_PRICE_DATA = {"price": f_usd, "change": deg, "time": simdi}
            msg = (f"💎 **$IRVUS Güncel Durum**\n━━━━━━━━━━━━━━━━━━\n💰 Fiyat: `${f_usd}`\n📈 24s Değişim: `%{deg}`\n━━━━━━━━━━━━━━━━━━")
            await update.message.reply_text(msg, parse_mode='Markdown')
    except:
        await update.message.reply_text("⚠️ Sistem yoğun, az sonra tekrar dene.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt: return await update.message.reply_text("❌ Örn: `/ciz aslan` ")
    await update.message.reply_text(f"🎨 **'{prompt}'** hazırlanıyor...")
    
    try:
        response = requests.post(IMAGE_MODEL, headers=HEADERS, json={"inputs": prompt}, timeout=30)
        if response.status_code == 200:
            await update.message.reply_photo(photo=response.content, caption=f"🖼 **Irvus AI:** {prompt}")
        else:
            url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?nologo=true"
            await update.message.reply_photo(photo=url, caption=f"🖼 **Irvus AI (Yedek):** {prompt}")
    except:
        await update.message.reply_text("❌ Çizim motoru meşgul.")

# --- 5. ANA MOTOR ---
async def main():
    Thread(target=run_web, daemon=True).start()
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    application.add_handler(CommandHandler(["ciz", "draw"], ciz))
    
    # Sohbet Handler'ı (Gruptaki mesajları dinler)
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
        
