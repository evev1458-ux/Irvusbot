import os, requests, asyncio, time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- 1. WEB SUNUCUSU (Render Kapanmasın Diye) ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS POWER SYSTEM ONLINE", 200

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAHAySA0SXbAP4G0KwcnCKGLkYs2yf-OeQU" 
CA_ADRESI = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
ANA_GRUP_ID = "-1002393767346"
LOGO_URL = "https://raw.githubusercontent.com/irvus-project/assets/main/logo.jpg"
BASE_RPC = "https://mainnet.base.org"
SWAP_TOPIC = "0xc42079f94a1d5046247098a76b0b302c30b6531398e0a8118d34346e27b13280"

# --- 3. YARDIMCI FONKSİYONLAR ---
def get_safe_price():
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/pairs/base/{CA_ADRESI}", timeout=8).json()
        return r.get('pair')
    except: return None

# --- 4. KOMUTLAR (START, FIYAT, CIZ) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Butonlu Karşılama Ekranı"""
    msg = (f"💎 **Irvus Bilgi Sistemine Hoş Geldiniz!**\n\n"
           f"Anlık alım takibi ve komutlar şu an aktiftir.\n\n"
           f"📄 **CA:** `{CA_ADRESI}`")
    kb = [
        [InlineKeyboardButton("🌐 Web Sitesi", url="https://www.irvustoken.xyz"), 
         InlineKeyboardButton("🐦 X (Twitter)", url="https://x.com/IRVUSTOKEN")],
        [InlineKeyboardButton("📊 Canlı Grafik", url=f"https://dexscreener.com/base/{CA_ADRESI}")]
    ]
    await update.message.reply_photo(photo=LOGO_URL, caption=msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fiyat Bilgisi"""
    p = get_safe_price()
    if p:
        msg = (f"💰 **Fiyat:** `${p['priceUsd']}`\n"
               f"📊 **M.Cap:** `${float(p.get('fdv', 0))/1000:.1f}K`\n"
               f"📈 **24s:** %{p['priceChange']['h24']}")
        return await update.message.reply_text(msg)
    await update.message.reply_text("💎 Veriler güncelleniyor...")

async def ciz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """AI Çizim"""
    prompt = " ".join(context.args)
    if not prompt: return await update.message.reply_text("❌ Kullanım: `/ciz aslan` ")
    await update.message.reply_text("🎨 Resminiz hazırlanıyor...")
    u = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?seed={int(time.time())}"
    await update.message.reply_photo(photo=u, caption=f"🖼 **Irvus AI:** `{prompt}`")

# --- 5. AĞ TAKİP MOTORU (ON-CHAIN) ---
async def track_onchain(application):
    last_block = 0
    while True:
        try:
            res_block = requests.post(BASE_RPC, json={"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}, timeout=10).json()
            current_block = int(res_block["result"], 16)
            if last_block == 0: last_block = current_block - 1

            if current_block > last_block:
                payload = {"jsonrpc": "2.0", "method": "eth_getLogs", "params": [{"fromBlock": hex(last_block + 1), "toBlock": hex(current_block), "address": CA_ADRESI, "topics": [SWAP_TOPIC]}], "id": 1}
                logs = requests.post(BASE_RPC, json=payload, timeout=10).json().get("result", [])
                
                for log in logs:
                    data_hex = log["data"][2:]
                    amount_raw = int(data_hex[-64:], 16) / 10**18
                    if amount_raw > 0:
                        p_data = get_safe_price()
                        if p_data:
                            usd_val = amount_raw * float(p_data['priceUsd'])
                            if usd_val >= 5.0: # 5$ FİLTRESİ
                                msg = (f"🚀 **YENİ ALIM!** 🟢\n━━━━━━━━━━━━━━\n"
                                       f"💰 **Harcama:** `${usd_val:.2f}`\n"
                                       f"💎 **Miktar:** `{amount_raw:,.0f} IRVUS`\n"
                                       f"━━━━━━━━━━━━━━")
                                try: await application.bot.send_photo(chat_id=ANA_GRUP_ID, photo=LOGO_URL, caption=msg)
                                except: pass
                last_block = current_block
        except: pass
        await asyncio.sleep(5)

# --- 6. ANA ÇALIŞTIRICI ---
def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

async def main():
    # 1. Flask'ı ayrı bir kanalda başlat
    Thread(target=run_flask, daemon=True).start()
    
    # 2. Botu kur
    application = ApplicationBuilder().token(TOKEN).build()
    
    # 3. Komutları kaydet (Öncelikli)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler(["fiyat", "p"], fiyat))
    application.add_handler(CommandHandler(["ciz", "draw"], ciz))
    
    # 4. Botu başlat
    await application.initialize()
    await application.start()
    
    # 5. Ağ takibini arka plan görevi olarak ekle
    asyncio.create_task(track_onchain(application))
    
    # 6. Dinlemeye başla
    print(">>> Irvus Bot Tüm Modülleriyle Aktif!")
    await application.updater.start_polling(drop_pending_updates=True)
    
    # Botun açık kalmasını sağla
    while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    try: asyncio.run(main())
    except: pass
        
