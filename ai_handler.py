import aiohttp
import os
import logging
import urllib.parse  # Yeni URL encode yöntemi

logger = logging.getLogger(__name__)

TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"

async def ask_ai(soru: str) -> str:
    """
    Hatalardan arındırılmış AI fonksiyonu.
    """
    api_key = os.getenv("TOGETHER_API_KEY", "")

    # 1. Seçenek: Together.ai (Eğer anahtarın varsa)
    if api_key:
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
                    "messages": [
                        {"role": "system", "content": "Sen Irvus Token projesinin asistanısın. Türkçe, kısa ve samimi cevaplar ver."},
                        {"role": "user", "content": soru}
                    ],
                    "max_tokens": 500,
                    "temperature": 0.7
                }
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                async with session.post(
                    TOGETHER_API_URL,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=20)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Together AI error: {e}")

    # 2. Seçenek (Fallback): Pollinations Text - BURASI HATALIYDI, DÜZELTİLDİ
    try:
        # requote_uri yerine standart quote kullanıyoruz
        encoded_text = urllib.parse.quote(soru)
        url = f"https://text.pollinations.ai/{encoded_text}?model=llama" # Llama modelini zorunlu kıldık
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    if text:
                        return text.strip()[:1000]
    except Exception as e:
        logger.error(f"Pollinations text error: {e}")

    return "❌ Şu an yanıt veremiyorum, lütfen tekrar deneyin."


async def draw_image(prompt: str) -> str:
    """
    Ücretsiz görsel üretimi.
    """
    try:
        encoded = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&nologo=true&seed=42"
        
        # Sadece URL döndürmek yeterli, Telegram bu URL'yi resim olarak çeker
        return url
    except Exception as e:
        logger.error(f"Draw image error: {e}")
        return None
        
