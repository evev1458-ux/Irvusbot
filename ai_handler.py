import aiohttp
import urllib.parse
async def ask_ai(s: str):
    url = f"https://text.pollinations.ai/{urllib.parse.quote(s)}?system=Sen+Irvus+asistanisin."
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            return (await r.text())[:1000] if r.status == 200 else "Hata."
async def draw_image(p: str):
    return f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p)}"
    
