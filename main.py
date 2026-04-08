import os, asyncio, requests, xml.etree.ElementTree as ET
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib.parse import quote

# --- 1. WEB SUNUCUSU ---
app = Flask(__name__)
@app.route('/')
def home(): return "IRVUS LIVE SCRAPER: OK", 200
Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))).start()

# --- 2. AYARLAR ---
TOKEN = "8621050385:AAFP8Pmc0p24oQnDEiL6SwMTgL6tr3HIPss"

# --- 3. GERÇEK ZAMANLI HABER ÇEKİCİ (GOOGLE NEWS RSS) ---
def get_google_news(query):
    try:
        # Google Haberler üzerinden o konuyla ilgili en son 3 başlığı çeker
        url = f"https://news.google.com/rss/search?q={quote(query)}&hl=tr&gl=TR&ceid=TR:tr"
        r = requests.get(url, timeout=10)
        root = ET.fromstring(r.content)
        headlines = []
        for item in root.findall('.//item')[:3]:
            headlines.append(item.find('title').text)
        return " | ".join(headlines) if headlines else "Güncel haber bulunamadı."
    except:
        return "Haber kaynağına ulaşılamadı."

# --- 4. KOMUTLAR ---
async def sor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query: return await update.message.reply_text("🤖 Ne sormak istersin?")
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # ÖNCE İNTERNETTEN HABERLERİ ÇEKİYORUZ (GERÇEK VERİ)
    guncel_haberler = get_google_news(query)
    
    # SONRA AI'YA BU HABERLERİ "KESİN BİLGİ" OLARAK VERİYORUZ
    prompt = (f"Bugün 8 Nisan 2026. İnternetteki en son haber başlıkları şunlar: {guncel_haberler}. "
              f"Bu bilgileri kullanarak şu soruyu detaylıca cevapla: {query}")
    
    ai_url = f"https://text.pollinations.ai/{quote(prompt)}?model=openai"
    
    try:
        r = requests.get(ai_url, timeout=20)
        await update.message.reply_text(f"🤖 **Irvus Canlı AI:**\n\n{r.text}")
    except:
        await update.message.reply_text("❌ Yapay zeka yanıt veremedi.")

# --- 5. BAŞLAT ---
async def main():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("sor", sor))
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)
    while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
    
