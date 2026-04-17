import logging
import os
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are a helpful crypto community assistant inside a Telegram group. 
You answer questions about DeFi, tokens, trading, blockchain technology, and crypto in general.
Keep answers concise and helpful. Avoid financial advice disclaimers unless explicitly discussing investment.
Be friendly and community-oriented."""


async def chat_completion(user_message: str, chat_history: list = None) -> str:
    """Get a chat completion from OpenAI."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    if chat_history:
        messages.extend(chat_history[-6:])  # Keep last 6 messages for context
    
    messages.append({"role": "user", "content": user_message})
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=512,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error("OpenAI chat error: %s", e)
        return "Sorry, I'm having trouble connecting right now. Please try again later."


async def generate_image(prompt: str) -> str | None:
    """Generate an image using DALL-E and return the URL."""
    try:
        response = await client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024",
            quality="standard",
        )
        return response.data[0].url
    except Exception as e:
        logger.error("DALL-E generation error: %s", e)
        return None


# Simple in-memory conversation history per chat
_chat_histories: dict[int, list] = {}


def get_chat_history(chat_id: int) -> list:
    return _chat_histories.get(chat_id, [])


def update_chat_history(chat_id: int, user_msg: str, assistant_msg: str):
    history = _chat_histories.setdefault(chat_id, [])
    history.append({"role": "user", "content": user_msg})
    history.append({"role": "assistant", "content": assistant_msg})
    # Keep only last 20 messages
    if len(history) > 20:
        _chat_histories[chat_id] = history[-20:]
