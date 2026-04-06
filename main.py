import os, requests, asyncio, time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. RENDER İÇİN WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS FULL SYSTEM ONLINE", 200

# --- 2. AYARLAR (Yeni Token'ını Buraya Yaz) ---
TOKEN = "BURAYA_YENI_ALDIĞIN_TOKENI_YAZ" 
CA_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
HF_TOKEN = "Hf_VzFKUkIElGkRTDWwEwLPwPPOOmwWwwBqNq"
GRUP_LISTESI = ["-1002393767346", "-1002375203585"]
LOGO_URL = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"
CHAT_MODEL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"

# --- 3. GÜVENLİ VERİ ÇEKME ---
def get_safe(url):
    try:
        r = requests.get(url, timeout=12)
        return r.json() if r.status_code == 200 else None
    except: return None

# --- 4. KOMUTLAR (Start ve Fiyat Geri Geldi) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (f"💎 **Irvus AI Dünyasına Hoş Geldin!**\n\n"
           f"Ben Irvus topluluğunun zeki asistanıyım. Alımları takip eder, sorularını yanıtlar ve hayallerini çizerim.\n\n"
           f"📄 **CA:** `{CA_ADRESI}`")
    
    kb = [[InlineKeyboardButton("📊 Canlı Grafik", url=f"https://dexscreener.com/base/{CA_ADRESI}")],
          [InlineKeyboardButton("🌐 Web Sitesi", url="https://www.irvustoken.xyz"), InlineKeyboardButton("🐦 X (Twitter)", url="https://x.com/IRVUSTOKEN")]]
    
    await update.message.reply_photo(photo=LOGO_URL, caption=msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_safe(f"https://api.dexscreener.com/latest/dex/search?q={CA_ADRESI}")
    if data and 'pairs' in data:
        p = next((x for x in data['pairs'] if x['chainId'] == 'base'), None)
        if p:
            mcap = float(p.get('fdv', 0)) / 1000
            msg = (f"💰 **Fiyat:** `${p['priceUsd']}`\n"
                   f"📈 **24s Değişim:** %{p['priceChange']['h24']}\n"
                   f"📊 **Market Cap:** `${mcap:.1f}K`\n"
                   f"💧 **Likidite:** `${p.get('liquidity', {}).get('usd', 0):,.0f}`")
            return await update.message.reply_text(msg)
    await update.message.reply_text("💎 Irvus verileri şu an güncelleniyor, grafikten kontrol edebilirsin!")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = " ".join(context.args)
    if not p: return await update.message.reply_text("❌ Kullanım: `/ciz aslan` ")
    u = f"https://image.pollinations.ai/prompt/{p.replace(' ', '%20')}?seed={int(time.time())}"
    await update.message.reply_photo(photo=u, caption=f"🖼 **Irvus AI:** `{p}`")

# --- 5. AKILLI SOHBET ---
async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.lower()
    is_reply = update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id
    
    if "irvus" in text or is_reply:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Bitcoin hızlı yanıt
        if any(x in text for x in ["bitcoin", "btc"]):
            d = get_safe("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")
            if d: return await update.message.reply_text(f"📊 **BTC:** `${float(d['price']):,.0f}`. Irvus ile yükselişe hazırız! 🚀")

        try:
            prompt = f"<|system|>\nSen Irvus Token asistanısın. Türkçe, zeki ve kısa cevap ver.</s>\n<|user|>\n{update.message.text}</s>\n<|assistant|>\n"
            res = requests.post(CHAT_MODEL, headers={"Authorization": f"Bearer {HF_TOKEN}"}, json={"inputs": prompt}, timeout=10).json()
            ans = res[0].get('generated_text', "").split("<|assistant|>")[-1].strip()
            if ans: return await update.message.reply_text(f"🤖 {ans}")
        except: pass
        await update.message.reply_text("💎 Irvus vizyonuyla seni dinliyorum dostum!")

# --- 6. ALIM TAKİBİ ---
async def track_buys(context: ContextTypes.DEFAULT_TYPE):
    last_buys = 0
    while True:
        data = get_safe(f"https://api.dexscreener.com/latest/dex/pairs/base/{CA_ADRESI}")
        if data and 'pair' in data:
            pair = data['pair']
            cur = pair.get('txns', {}).get('m5', {}).get('buys', 0)
            if last_buys != 0 and cur > last_buys:
                vol = float(pair.get('volume', {}).get('m5', 0))
                if vol >= 5.0:
                    msg = f"🚀 **YENİ ALIM!** 🟢\n━━━━━━━━━━━━━━\n💰 **Fiyat:** `${pair.get('priceUsd')}`\n💵 **Hacim:** `${vol:.2f}`\n━━━━━━━━━━━━━━\n💎 [Grafik](https://dexscreener.com/base/{CA_ADRESI})"
                    for gid in GRUP_LISTESI:
                        try: await context.bot.send_photo(chat_id=gid, photo=LOGO_URL, caption=msg)
                        except: pass
            last_buys = cur
        await asyncio.sleep(30)

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
        
