import os, requests, asyncio, time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS MULTI-AI ONLINE", 200

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAGC37E6oeacOL1fjtUWqFoN2sXCVlIplOc"
CA_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
HF_TOKEN = "Hf_VzFKUkIElGkRTDWwEwLPwPPOOmwWwwBqNq"

# GRUPLARIN LİSTESİ
GRUP_LISTESI = ["-1002393767346", "-1002375203585"]

CHAT_MODEL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
X_ADRESI = "https://x.com/IRVUSTOKEN"
WEB_SITESI = "https://www.irvustoken.xyz"
LOGO_URL = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"

# --- 3. SOHBET VE BİLGİ MOTORU ---
async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    user_text = update.message.text.lower().strip()
    is_reply = update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id
    
    if "irvus" in user_text or is_reply or any(x in user_text for x in ["bitcoin", "btc", "savaş", "hava"]):
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Bitcoin (Binance API)
        if "bitcoin" in user_text or "btc" in user_text:
            try:
                res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT").json()
                p = float(res['price'])
                return await update.message.reply_text(f"📊 **BTC:** `${p:,.0f}`. Irvus ile yükselişe hazırız! 🚀")
            except: pass

        # Hava ve Savaş (Akıllı Cevaplar)
        if "hava" in user_text:
            return await update.message.reply_text("☀️ **Hava:** Gökyüzü Irvus'un geleceği gibi güneşli ve parlak! 💎")
        if "savaş" in user_text:
            return await update.message.reply_text("🌍 **Gündem:** Piyasalar gergin olabilir ama Irvus topluluğu dimdik ayakta! 🛡️")

        # Naber / Nasılsın
        if any(x in user_text for x in ["naber", "nasılsın"]):
            return await update.message.reply_text("😊 Çok iyiyim! Her iki grubu da 30 saniyede bir denetliyorum. Sen nasılsın?")

        try:
            prompt = f"<|system|>\nSen Irvus Token asistanısın. Türkçe, zeki ve kısa cevap ver.</s>\n<|user|>\n{update.message.text}</s>\n<|assistant|>\n"
            res = requests.post(CHAT_MODEL, headers={"Authorization": f"Bearer {HF_TOKEN}"}, 
                                json={"inputs": prompt, "parameters": {"max_new_tokens": 150}}, timeout=10).json()
            ans = res[0].get('generated_text', "").split("<|assistant|>")[-1].strip()
            if ans: return await update.message.reply_text(f"🤖 {ans}")
        except: pass
        await update.message.reply_text("💎 Irvus burada! Seni duyuyorum dostum.")

# --- 4. ALIM TAKİBİ (BUY BOT) ---
async def track_buys(context: ContextTypes.DEFAULT_TYPE):
    last_buys = 0
    while True:
        try:
            url = f"https://api.dexscreener.com/latest/dex/pairs/base/{CA_ADRESI}"
            res = requests.get(url, timeout=10).json()
            pair = res.get('pair', {})
            current_buys = pair.get('txns', {}).get('m5', {}).get('buys', 0)
            vol_5m = float(pair.get('volume', {}).get('m5', 0))
            
            if last_buys != 0 and current_buys > last_buys and vol_5m >= 5.0:
                price = pair.get('priceUsd', '0')
                mcap = pair.get('fdv', 0)
                mcap_str = f"{mcap/1000:.1f}K" if mcap < 1000000 else f"{mcap/1000000:.2f}M"
                msg = (f"🚀 **YENİ $IRVUS ALIMI!** 🟢\n━━━━━━━━━━━━━━\n"
                       f"💰 **Fiyat:** `${price}`\n💵 **Hacim:** `${vol_5m:.2f}`\n📊 **MCap:** `${mcap_str}`\n"
                       f"━━━━━━━━━━━━━━\n💎 [Grafik](https://dexscreener.com/base/{CA_ADRESI})")
                for gid in GRUP_LISTESI:
                    try: await context.bot.send_photo(chat_id=gid, photo=LOGO_URL, caption=msg, parse_mode='Markdown')
                    except: pass
            last_buys = current_buys
        except: pass
        await asyncio.sleep(30)

# --- 5. KOMUTLAR (BUTONLAR GERİ GELDİ) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (f"💎 **Irvus AI Dünyasına Hoş Geldiniz!**\n\n"
           f"Her iki grupta da alım takibi ve zeka desteği aktiftir.\n\n"
           f"📄 **CA:** `{CA_ADRESI}`")
    
    # Butonlar burada
    kb = [[InlineKeyboardButton("🌐 Web Sitesi", url=WEB_SITESI), InlineKeyboardButton("🐦 X (Twitter)", url=X_ADRESI)],
          [InlineKeyboardButton("📊 Canlı Grafik", url=f"https://dexscreener.com/base/{CA_ADRESI}")]]
    
    try:
        await update.message.reply_photo(photo=LOGO_URL, caption=msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    except:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        res = requests.get(f"https://api.dexscreener.com/latest/dex/search?q={CA_ADRESI}").json()
        p = next((x for x in res.get('pairs', []) if x['chainId'] == 'base'), None)
        if p: await update.message.reply_text(f"💰 **Fiyat:** `${p['priceUsd']}`\n📈 **24s:** %{p['priceChange']['h24']}")
    except: await update.message.reply_text("⚠️ API yoğun.")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = " ".join(context.args)
    if not p: return await update.message.reply_text("❌ Örn: `/ciz aslan` ")
    u = f"https://image.pollinations.ai/prompt/{p.replace(' ', '%20')}?seed={int(time.time())}"
    await update.message.reply_photo(photo=u, caption=f"🖼 **Irvus AI:** `{p}`")

# --- 6. ANA MOTOR ---
async def main():
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    app_bot.add_handler(CommandHandler(["ciz", "draw"], ciz))
    app_bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat_ai))
    async with app_bot:
        await app_bot.initialize()
        await app_bot.start()
        asyncio.create_task(track_buys(app_bot))
        await app_bot.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    try: asyncio.run(main())
    except: pass
        
