import os, asyncio, requests, json
from flask import Flask, request, jsonify
from threading import Thread
from telegram.ext import ApplicationBuilder, CommandHandler

# --- AYARLAR ---
TOKEN = "8621050385:AAFP8Pmc0p24oQnDEiL6SwMTgL6tr3HIPss"
GROUP_ID = -1002315757919

app = Flask(__name__)

@app.route('/')
def home(): 
    return "IRVUS ALCHEMY SYSTEM: LIVE", 200

# --- 🟢 WEBHOOK KAPISI (HATA KORUMALI) ---
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    # Gelen ham veriyi loglarda görmek için (Render'da 'Logs' kısmına bakabilirsin)
    print(f"DEBUG - Alchemy'den Veri Geldi: {json.dumps(data)}")
    
    if data:
        # Veriyi arka planda işle (Alchemy'nin beklememesi için hemen 200 dönüyoruz)
        Thread(target=parse_and_send, args=(data,)).start()
        
    return jsonify({"status": "ok"}), 200

def parse_and_send(data):
    try:
        activities = []
        # 1. Senaryo: Veri 'event' -> 'activity' içindeyse
        if isinstance(data, dict) and 'event' in data:
            activities = data['event'].get('activity', [])
        # 2. Senaryo: Veri direkt bir liste ise
        elif isinstance(data, list):
            activities = data
        # 3. Senaryo: Veri direkt 'activity' anahtarıyla gelmişse
        elif isinstance(data, dict) and 'activity' in data:
            activities = data.get('activity', [])
        # 4. Senaryo: Sadece tek bir işlem objesi geldiyse
        elif isinstance(data, dict) and 'hash' in data:
            activities = [data]

        for act in activities:
            tx_hash = act.get('hash') or act.get('transactionHash')
            value = act.get('value')
            asset = act.get('asset', 'IRVUS')
            
            # Değer varsa ve 0'dan büyükse (Gerçek bir transferse)
            if value is not None and float(value) > 0:
                msg = (f"🟢 **NEW IRVUS BUY!**\n\n"
                       f"💰 Amount: **{float(value):,.0f} {asset}**\n"
                       f"🔗 [Basescan Link](https://basescan.org/tx/{tx_hash})\n\n"
                       f"🚀 **TO THE MOON!**")
                
                # Telegram API'sine direkt istek at
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                              json={"chat_id": GROUP_ID, "text": msg, "parse_mode": "Markdown"})
    except Exception as e:
        print(f"Işleme Hatası: {e}")

if __name__ == "__main__":
    # Flask sunucusunu ayrı bir kolda başlat
    Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))).start()
    
    # Botu başlat
    application = ApplicationBuilder().token(TOKEN).build()
    print(">>> BOT DINLEMEDE, ALCHEMY ILE SENKRONIZE!")
    application.run_polling(drop_pending_updates=True)
    
