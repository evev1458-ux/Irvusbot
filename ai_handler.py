import aiohttp
import os
import logging
import urllib.parse

logger = logging.getLogger(__name__)

async def ask_ai(soru: str) -> str:
    # URL'yi en güvenli şekilde encode et
    encoded_text = urllib.parse.quote(soru)
    # Ücretsiz ve sağlam Pollinations URL'si
    url = f"https://text.pollinations.ai/{encoded_text}?model=openai&system=Sen+Irvus+Token+asistanisin.+Kisa+Turkce+cevap+ver."
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    return text.strip()[:1000] if text else "Boş cevap döndü."
    except Exception as e:
        logger.error(f"AI Error: {e}")
    
    return "❌ Şu an yanıt veremiyorum, lütfen tekrar deneyin."

async def draw_image(prompt: str) -> str:
    encoded = urllib.parse.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&nologo=true"
    
