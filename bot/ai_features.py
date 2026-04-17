import logging
import os
import google.generativeai as genai

logger = logging.getLogger(__name__)

# --- ÜCRETSİZ AI YAPILANDIRMASI ---
# Render Environment kısmına GEMINI_API_KEY eklemeyi unutma!
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

SYSTEM_PROMPT = """Sen bir Telegram grubunda yardımcı bir kripto topluluk asistanısın. 
DeFi, tokenlar, ticaret, blockchain teknolojisi ve genel olarak kripto hakkındaki soruları cevaplıyorsun.
Cevapları kısa ve yardımcı tut. Dost canlısı ve topluluk odaklı ol."""

async def chat_completion(user_message: str, chat_history: list = None) -> str:
    """Gemini kullanarak ücretsiz sohbet yanıtı al."""
    try:
        # Sistem komutunu ve geçmişi birleştiriyoruz
        full_prompt = f"{SYSTEM_PROMPT}\n\nKullanıcı Sorusu: {user_message}"
        
        # Ücretsiz Gemini yanıtı
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        logger.error("Gemini chat error: %s", e)
        return "Üzgünüm, şu an bağlantı kuramıyorum. Lütfen daha sonra tekrar dene."

async def generate_image(prompt: str) -> str | None:
    """Pollinations AI kullanarak %100 ÜCRETSİZ ve SINIRSIZ görsel oluştur."""
    try:
        # Boşlukları URL formatına çeviriyoruz
        formatted_prompt = prompt.replace(" ", "%20")
        # API anahtarı gerektirmeyen Pollinations linki
        image_url = f"https://pollinations.ai/p/{formatted_prompt}?width=1024&height=1024&model=flux"
        return image_url
    except Exception as e:
        logger.error("Pollinations generation error: %s", e)
        return None

# Basit bellek içi geçmiş (Değişmedi)
_chat_histories: dict[int, list] = {}

def get_chat_history(chat_id: int) -> list:
    return _chat_histories.get(chat_id, [])

def update_chat_history(chat_id: int, user_msg: str, assistant_msg: str):
    history = _chat_histories.setdefault(chat_id, [])
    history.append({"role": "user", "content": user_msg})
    history.append({"role": "assistant", "content": assistant_msg})
    if len(history) > 20:
        _chat_histories[chat_id] = history[-20:]
        
