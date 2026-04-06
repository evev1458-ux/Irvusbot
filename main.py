import os, requests, asyncio, time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. SUNUCU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS MASTER ONLINE", 200

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAGC37E6oeacOL1fjtUWqFoN2sXCVlIplOc"
CA_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
HF_TOKEN = "Hf_VzFKUkIElGkRTDWwEwLPwPPOOmwWwwBqNq"
GRUP_LISTESI = ["-1002393767346", "-1002375203585"]
LOGO_URL = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"
CHAT_MODEL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"

# --- 3. GERÇEK YAPAY ZEKA SOHBETİ (HAZIR CEVAP YOK) ---
async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    user_text = update.message.text.lower()
    is_reply = update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id
    
    # Bot ismi geçerse veya yanıt verilirse
    if "irvus" in user_text or is_reply:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Bitcoin için özel hızlı veri (Yorumu AI yapacak)
        btc_info = ""
        if "bitcoin" in user_text or "btc" in user_text:
            try:
                r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT").json()
                btc_info = f"(Not: Şu an BTC fiyatı ${float(r['price']):,.0f})"
            except: pass

        try:
            # AI'ya verilen talimat: Asla hazır cevap verme, her zaman özgün ve zeki ol.
            prompt = (f"<|system|>\nSen Irvus Token'ın zeki ve canlı asistanısın. Hazır mesaj kullanma. "
                      f"Kullanıcının sorusuna göre özgün, kısa ve Türkçe cevap ver. {btc_info}</s>\n"
                      f"<|user|>\n{update.message.text}</s>\n<|assistant|>\n")
            
            res = requests.post(CHAT_MODEL, headers={"Authorization": f"Bearer {HF_TOKEN}"}, 
                                json={"inputs": prompt, "parameters": {"max_new_tokens": 150, "temperature": 0.7}}, timeout=15).json()
            
            ans = res[0].get('generated_text', "").split("<|assistant|>")[-1].strip()
            if ans: return await update.message.reply_text(f"🤖 {ans}")
        except:
            # Sadece sistem tamamen çökerse buraya düşer
            await update.message.reply_text("💎 Dostum şu an derin düşüncelerdeyim, Irvus geleceği için planlar yapıyorum. Az sonra tekrar sorsana?")

# --- 4. ALIM TAKİBİ (30 SANİYE) ---
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
                msg = f"🚀 **YENİ $IRVUS ALIMI!** 🟢\n━━━━━━━━━━━━━━\n💰 **Fiyat:** `${price}`\n💵 **Hacim:** `${vol_5m:.2f}`\n━━━━━━━━━━━━━━\n💎 [Grafik](https://dexscreener.com/base/{CA_ADRESI})"
                for gid in GRUP_LISTESI:
                    try: await context.bot.send_photo(chat_id=gid, photo=LOGO_URL, caption=msg)
                    except: pass
            last_buys = current_buys
        except: pass
        await asyncio.sleep(30)

# --- 5. KOMUTLAR ---
async def fiyat(update, context):
    try:
        res = requests.get(f"https://api.dexscreener.com/latest/dex/search?q={CA_ADRESI}").json()
        p = next((x for x in res.get('pairs', []) if x['chainId'] == 'base'), None)
        if p:
            msg = f"💰 **Fiyat:** `${p['priceUsd']}`\n📈 **24s Değişim:** %{p['priceChange']['h24']}\n📊 **MCap:** ${float(p.get('fdv', 0))/1000:.1f}K"
            return await update.message.reply_text(msg)
    except: pass
    await update.message.reply_text("⚠️ Veri şu an güncelleniyor, 10 saniye sonra tekrar dene.")

async def start(update, context):
    kb = [[InlineKeyboardButton("📊 Canlı Grafik", url=f"https://dexscreener.com/base/{CA_ADRESI}")]]
    await update.message.reply_photo(photo=LOGO_URL, caption="💎 **Irvus AI Aktif!**\nSohbet etmeye ne dersin?", reply_markup=InlineKeyboardMarkup(kb))

async def ciz(update, context):
    p = " ".join(context.args)
    if not p: return await update.message.reply_text("❌ Örn: `/ciz uçan bir aslan` ")
    u = f"https://image.pollinations.ai/prompt/{p.replace(' ', '%20')}?seed={int(time.time())}"
    await update.message.reply_photo(photo=u, caption=f"🖼 **Irvus AI:** `{p}`")

# --- 6. ÇALIŞTIR ---
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
                                                                                                                  
