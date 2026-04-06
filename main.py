import os, requests, asyncio, time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS MULTI-GROUP AI ONLINE", 200

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAGC37E6oeacOL1fjtUWqFoN2sXCVlIplOc"
CA_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
HF_TOKEN = "Hf_VzFKUkIElGkRTDWwEwLPwPPOOmwWwwBqNq"

# GRUPLARIN LİSTESİ (İkisini de buraya ekledim)
GRUP_LISTESI = ["-1002393767346", "-1002375203585"]

CHAT_MODEL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
LOGO_URL = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"

# --- 3. ZEKA FONKSİYONLARI ---
def get_btc_price():
    try:
        res = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd").json()
        return res['bitcoin']['usd']
    except: return "Şu an çekilemiyor."

# --- 4. GELİŞMİŞ SOHBET MOTORU ---
async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    user_text = update.message.text.lower()
    is_reply = update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id
    
    if "irvus" in user_text or is_reply:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        if any(x in user_text for x in ["bitcoin", "btc", "fiyat ne"]):
            btc = get_btc_price()
            return await update.message.reply_text(f"📊 **Piyasa:** BTC `${btc}`. Irvus için her şey yolunda! 🚀")

        if any(x in user_text for x in ["naber", "nasılsın", "ne haber"]):
            return await update.message.reply_text("😊 Çok iyiyim! Her iki grubu da izliyorum ve Irvus topluluğu için çalışıyorum. Sen nasılsın?")

        try:
            prompt = f"<|system|>\nSen Irvus Token asistanısın. Türkçe, zeki ve kısa cevap ver.</s>\n<|user|>\n{update.message.text}</s>\n<|assistant|>\n"
            res = requests.post(CHAT_MODEL, headers={"Authorization": f"Bearer {HF_TOKEN}"}, 
                                json={"inputs": prompt, "parameters": {"max_new_tokens": 150}}, timeout=10).json()
            bot_response = res[0].get('generated_text', "").split("<|assistant|>")[-1].strip()
            await update.message.reply_text(f"🤖 {bot_response}" if bot_response else "💎 Irvus ile gelecek bugün başlıyor!")
        except:
            await update.message.reply_text("💎 Irvus burada! Seni duyuyorum dostum.")

# --- 5. ALIM TAKİBİ (BUY BOT) - 30 SANIYE VE ÇİFT GRUP ---
async def track_buys(context: ContextTypes.DEFAULT_TYPE):
    last_buys = 0
    print(">>> Alım takibi 30 saniye aralıkla başlatıldı...")
    
    while True:
        try:
            url = f"https://api.dexscreener.com/latest/dex/pairs/base/{CA_ADRESI}"
            res = requests.get(url, timeout=10).json()
            pair = res.get('pair', {})
            current_buys = pair.get('txns', {}).get('m5', {}).get('buys', 0)
            vol_5m = float(pair.get('volume', {}).get('m5', 0))
            
            # Eğer yeni alım varsa ve 5 dolar üstündeyse
            if last_buys != 0 and current_buys > last_buys and vol_5m >= 5.0:
                price = pair.get('priceUsd', '0')
                mcap = pair.get('fdv', 0)
                mcap_str = f"{mcap/1000:.1f}K" if mcap < 1000000 else f"{mcap/1000000:.2f}M"
                
                msg = (f"🚀 **YENİ $IRVUS ALIMI!** 🟢\n"
                       f"━━━━━━━━━━━━━━━━━━\n"
                       f"💰 **Fiyat:** `${price}`\n"
                       f"💵 **Hacim:** `${vol_5m:.2f}`\n"
                       f"📊 **MCap:** `${mcap_str}`\n"
                       f"━━━━━━━━━━━━━━━━━━\n"
                       f"💎 [Grafik](https://dexscreener.com/base/{CA_ADRESI})")
                
                # Her iki gruba da mesaj gönder
                for grup_id in GRUP_LISTESI:
                    try:
                        await context.bot.send_photo(chat_id=grup_id, photo=LOGO_URL, caption=msg, parse_mode='Markdown')
                    except Exception as e:
                        print(f"Grup {grup_id} mesaj hatası: {e}")
            
            last_buys = current_buys
        except Exception as e:
            print(f"Takip hatası: {e}")
            
        await asyncio.sleep(30) # 30 Saniye bekleme süresi

# --- 6. KOMUTLAR VE ANA MOTOR ---
async def start(update, context):
    await update.message.reply_text(f"💎 **Irvus Multi-AI Aktif!**\n\nHer iki grubu da 30 saniyede bir denetliyorum.\n\n📄 **CA:** `{CA_ADRESI}`")

async def fiyat(update, context):
    res = requests.get(f"https://api.dexscreener.com/latest/dex/search?q={CA_ADRESI}").json()
    p = next((x for x in res.get('pairs', []) if x['chainId'] == 'base'), None)
    if p: await update.message.reply_text(f"💰 **Fiyat:** `${p['priceUsd']}`\n📈 **24s:** %{p['priceChange']['h24']}")

async def ciz(update, context):
    prompt = " ".join(context.args)
    if not prompt: return await update.message.reply_text("❌ Örn: `/ciz aslan` ")
    url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?seed={int(time.time())}"
    await update.message.reply_photo(photo=url, caption=f"🖼 **Irvus AI:** `{prompt}`")

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
        asyncio.create_task(track_buys(application)) 
        await application.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    try: asyncio.run(main())
    except: pass
            
