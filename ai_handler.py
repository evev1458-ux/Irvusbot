import aiohttp
import os
import logging

logger = logging.getLogger(__name__)

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/"
TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"

async def ask_ai(soru: str) -> str:
    """
    Ücretsiz AI: Together.ai (ücretsiz tier) veya fallback olarak
    Pollinations text API kullanır.
    """
    api_key = os.getenv("TOGETHER_API_KEY", "")

    # Together.ai varsa kullan (ücretsiz $25 kredi)
    if api_key:
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Sen yardımcı bir Türkçe asistansın. Kısa ve net cevaplar ver."
                        },
                        {
                            "role": "user",
                            "content": soru
                        }
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
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Together AI error: {e}")

    # Fallback: ücretsiz Pollinations text
    try:
        async with aiohttp.ClientSession() as session:
            encoded = aiohttp.helpers.requote_uri(soru)
            url = f"https://text.pollinations.ai/{encoded}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    return text.strip()[:1000]
    except Exception as e:
        logger.error(f"Pollinations text error: {e}")

    return "❌ Şu an yanıt veremiyorum, lütfen tekrar deneyin."


async def draw_image(prompt: str) -> str:
    """
    Ücretsiz görsel: Pollinations.ai (tamamen ücretsiz, API key gerekmez)
    """
    try:
        import urllib.parse
        encoded = urllib.parse.quote(prompt)
        # Pollinations ücretsiz image API
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&nologo=true"
        # URL'yi doğrudan döndür (Telegram doğrudan indirebilir)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status == 200:
                    return url
    except Exception as e:
        logger.error(f"Draw image error: {e}")

    return None
  
