import os, requests, asyncio, time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS FIX ONLINE", 200

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAGC37E6oeacOL1fjtUWqFoN2sXCVlIplOc"
CA_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
HF_TOKEN = "Hf_VzFKUkIElGkRTDWwEwLPwPPOOmwWwwBqNq"
GRUP_LISTESI = ["-1002393767346", "-1002375203585"]
LOGO_URL = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"
CHAT_MODEL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"

# --- 3. GÜVENLİ VERİ ÇEKME FONKSİYONU ---
def get_json_safe(url):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

# --- 4. SOHBET VE AI ---
async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.lower()
    is_reply = update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id
    
    if "irvus" in text or is_reply:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Bitcoin için hızlı Binance kontrolü
        if any(x in text for x in ["bitcoin", "btc"]):
            data = get_json_safe("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")
            if data:
                return await update.message.reply_text(f"📊 **BTC:** `${float(data['price']):,.0f}`. Irvus ile takipteyiz! 🚀")

        # AI Yanıtı
        try:
            prompt = f"Sen Irvus Token asistanısın. Türkçe ve kısa cevap ver: {update.message.text}"
            res = requests.post(CHAT_MODEL, headers={"Authorization": f"Bearer {HF_TOKEN}"}, 
                                json={"inputs": prompt, "parameters": {"max_new_tokens": 80}}, timeout=10).json()
            ans = res[0].get('generated_text', "").replace(prompt, "").strip()
            if ans: return await update.message.reply_text(f"🤖 {ans}")
        except: pass
        await update.message.reply_text("💎 Irvus burada! Seni duyuyorum dostum.")

# --- 5. ALIM TAKİBİ (30 SN) ---
async def track_buys(context: ContextTypes.DEFAULT_TYPE):
    last_buys = 0
    while True:
        data = get_json_safe(f"https://api.dexscreener.com/latest/dex/pairs/base/{CA_ADRESI}")
        if data and 'pair' in data:
            pair = data['pair']
            current_buys = pair.get('txns', {}).get('m5', {}).get('buys', 0)
            if last_buys != 0 and current_buys > last_buys:
                vol = float(pair.get('volume', {}).get('m5', 0))
                if vol >= 5.0:
                    msg = f"🚀 **YENİ ALIM!** 🟢\n💰 **Fiyat:** `${pair.get('priceUsd')}`\n💵 **Hacim:** `${vol:.2f}`"
                    for gid in GRUP_LISTESI:
                        try: await context.bot.send_photo(chat_id=gid, photo=LOGO_URL, caption=msg)
                        except: pass
            last_buys = current_buys
        await asyncio.sleep(30)

# --- 6. KOMUTLAR ---
async def start(update, context):
    kb = [[InlineKeyboardButton("📊 Grafik", url=f"https://dexscreener.com/base/{CA_ADRESI}")]]
    await update.message.reply_photo(photo=LOGO_URL, caption="💎 **Irvus AI Aktif!**", reply_markup=InlineKeyboardMarkup(kb))

async def fiyat(update, context):
    data = get_json_safe(f"https://api.dexscreener.com/latest/dex/search?q={CA_ADRESI}")
    if data and 'pairs' in data:
        p = next((x for x in data['pairs'] if x['chainId'] == 'base'), None)
        if p: return await update.message.reply_text(f"💰 **Fiyat:** `${p['priceUsd']}`\n📈 **24s:** %{p['priceChange']['h24']}")
    await update.message.reply_text("💎 Irvus her geçen gün güçleniyor! Detaylar için grafiğe bakabilirsin.")

async def ciz(update, context):
    p = " ".join(context.args)
    if not p: return await update.message.reply_text("❌ Örn: `/ciz aslan` ")
    u = f"https://image.pollinations.ai/prompt/{p.replace(' ', '%20')}?seed={int(time.time())}"
    await update.message.reply_photo(photo=u, caption=f"🖼 **Irvus AI:** `{p}`")

# --- 7. ANA MOTOR ---
async def main():
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    bot.add_handler(CommandHandler(["ciz", "draw"], ciz))
    bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat_ai))
    async with bot:
        await bot.initialize()
        await bot.start()
        asyncio.create_task(track_buys(bot))
        await bot.updater.start_polling(drop_pending_updates=True)
        while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    try: asyncio.run(main())
    except: pass
        
