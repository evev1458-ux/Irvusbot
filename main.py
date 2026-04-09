import os, asyncio, requests, json, aiohttp, random
from flask import Flask, request, jsonify
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib.parse import quote

# --- AYARLAR ---
TOKEN = "8621050385:AAHnY8zSX9VUhD3bm-v44sHaMWzxVWzq0_c"
GROUP_ID = -1002315757919
CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"

app = Flask(__name__)

@app.route('/')
def home(): return "IRVUS LIVE", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if data:
        # Gelen veriyi Render loglarına basıyoruz ki ne geldiğini görelim
        print(f"DEBUG - ALCHEMY VERISI: {json.dumps(data)}")
        Thread(target=send_buy, args=(data,)).start()
    return "ok", 200

def send_buy(data):
    try:
        # Alchemy'nin tüm olası veri yollarını kontrol ediyoruz
        acts = []
        if isinstance(data, dict):
            # 'event' -> 'activity' yolu (En yaygın)
            acts = data.get('event', {}).get('activity', [])
            # Eğer boşsa direkt ana dizine bak
            if not acts: acts = data.get('activity', [])
            # O da boşsa ve veri bir 'value' içeriyorsa direkt kendisini al
            if not acts and 'value' in data: acts = [data]
        
        for a in acts:
            # Miktarı (value) yakala
            v = a.get('value')
            if v and float(v) > 0:
                tx = a.get('hash') or a.get('transactionHash') or "0x..."
                # Adet formatını güzelleştirelim (1,000,000 gibi)
                formatted_v = "{:,.0f}".format(float(v))
                
                txt = (f"🟢 **NEW IRVUS BUY!**\n\n"
                       f"💰 Amount: **{formatted_v} IRVUS**\n"
                       f"🔗 [Basescan](https://basescan.org/tx/{tx})\n\n"
                       f"🚀 **HAYIRLI OLSUN!**")
                
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                             json={"chat_id": GROUP_ID, "text": txt, "parse_mode": "Markdown"})
    except Exception as e:
        print(f"HATA: Mesaj gönderilemedi: {e}")

# --- KOMUTLAR ---
async def start(u, c):
    kb = [[InlineKeyboardButton("🌐 Website", url="https://www.irvustoken.xyz")], 
          [InlineKeyboardButton("🐦 Twitter (X)", url="https://x.com/IRVUSTOKEN")]]
    await u.message.reply_text("💎 **IRVUS GLOBAL BOT**", reply_markup=InlineKeyboardMarkup(kb))

async def fiyat(u, c):
    try:
        r = requests.get(f"https://api.geckoterminal.com/api/v2/networks/base/tokens/{CA}").json()
        p = r['data']['attributes']['price_usd']
        await u.message.reply_text(f"💰 **IRVUS Price:** `${float(p):.8f}`")
    except: await u.message.reply_text("⚠️ Hata.")

async def ask(u, c):
    q = " ".join(c.args)
    if not q: return
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://text.pollinations.ai/{quote(q)}?model=llama") as r:
                await u.message.reply_text(f"🤖 **Irvus AI:**\n\n{await r.text()}")
    except: pass

async def draw(u, c):
    p = " ".join(c.args)
    if not p: return
    m = await u.message.reply_text("🎨 Çiziliyor...")
    rid = random.randint(1, 999999)
    url = f"https://image.pollinations.ai/prompt/{quote(p)}?seed={rid}&nologo=true"
    try:
        await u.message.reply_photo(url, caption=f"🖼 **Art:** {p}")
        await m.delete()
    except: await m.edit_text("⚠️ Hata.")

if __name__ == "__main__":
    Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler(["fiyat", "price"], fiyat))
    bot.add_handler(CommandHandler("sor", ask))
    bot.add_handler(CommandHandler("ciz", draw))
    bot.run_polling(drop_pending_updates=True)
    
