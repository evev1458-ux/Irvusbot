import asyncio
import logging
import aiohttp
from database import get_tokens, get_group, get_seen_txns, add_seen_txns

logger = logging.getLogger(__name__)

# GeckoTerminal API (Hızlı ve Engel Yemez)
GECKO_API = "https://api.geckoterminal.com/api/v2/networks/{network}/tokens/{address}/trades"

# Ağ isimleri GeckoTerminal formatında olmalı
DEXSCREENER_CHAIN_IDS = {
    "ethereum": "eth",
    "bsc": "bsc",
    "base": "base",
    "solana": "solana"
}

CHAIN_MAP = {
    "ethereum": {"name": "Ethereum", "explorer": "https://etherscan.io/tx/"},
    "bsc":      {"name": "BSC",      "explorer": "https://bscscan.com/tx/"},
    "base":     {"name": "Base",     "explorer": "https://basescan.org/tx/"},
    "solana":   {"name": "Solana",   "explorer": "https://solscan.io/tx/"},
}

async def scan_token(bot, session, chat_id, group, token):
    network = DEXSCREENER_CHAIN_IDS.get(token['chain'].lower(), token['chain'].lower())
    url = GECKO_API.format(network=network, address=token['address'])
    
    try:
        async with session.get(url, timeout=10) as r:
            if r.status != 200:
                logger.error(f"❌ API Hatası: {r.status} - Adres: {token['address']}")
                return
            
            data = await r.json()
            trades = data.get("data", [])
            
            if not trades:
                return

            seen = get_seen_txns(chat_id, token["address"])
            new_txs = []
            
            for t in trades:
                attr = t.get("attributes", {})
                tx_h = attr.get("tx_hash")
                
                if not tx_h or tx_h in seen:
                    continue
                
                # Sadece 'buy' (alım) olanları yakala
                if attr.get("kind") == "buy":
                    buy_usd = float(attr.get("volume_in_usd") or 0)
                    if buy_usd == 0:
                        # Alternatif hesaplama
                        p_usd = float(attr.get("price_to_token_quote_in_usd") or 0)
                        amt = float(attr.get("from_token_amount") or 0)
                        buy_usd = p_usd * amt

                    logger.info(f"💰 Alım Tespit Edildi: ${buy_usd}")

                    if buy_usd >= group.get("min_buy", 0):
                        await send_alert(bot, chat_id, group, attr, token, buy_usd)
                
                new_txs.append(tx_h)
            
            if new_txs:
                add_seen_txns(chat_id, token["address"], new_txs)
    except Exception as e:
        logger.error(f"⚠️ Tarama Hatası: {e}")

async def send_alert(bot, chat_id, group, attr, token, buy_usd):
    try:
        emoji = group.get("custom_emoji", "🟢")
        # Her 10$ için bir emoji (max 30)
        emojis = emoji * max(1, min(int(buy_usd / 10) + 1, 30))
        
        tx_hash = attr.get("tx_hash", "")
        explorer = CHAIN_MAP.get(token["chain"], {}).get("explorer", "")
        
        msg = (
            f"<b>{token.get('name', 'Token')} Buy!</b>\n\n"
            f"{emojis}\n\n"
            f"💰 <b>Spent:</b> ${buy_usd:,.2f}\n"
            f"⛓ <b>Chain:</b> {token['chain'].upper()}\n\n"
            f"<a href='{explorer}{tx_hash}'>TX Linki</a>"
        )

        media_id = group.get("media_file_id")
        if media_id:
            m_type = group.get("media_type", "animation")
            if m_type == "video":
                await bot.send_video(chat_id, media_id, caption=msg, parse_mode="HTML")
            else:
                await bot.send_animation(chat_id, media_id, caption=msg, parse_mode="HTML")
        else:
            await bot.send_message(chat_id, msg, parse_mode="HTML")
    except Exception as e:
        logger.error(f"❌ Mesaj Gönderme Hatası: {e}")

async def tracking_loop(bot, get_all_group_chat_ids):
    logger.info("🚀 İZLEME MOTORU BAŞLATILDI!")
    async with aiohttp.ClientSession() as session:
        while True:
            chat_ids = get_all_group_chat_ids()
            for cid in chat_ids:
                group = get_group(cid)
                tokens = get_tokens(cid)
                for t in tokens:
                    await scan_token(bot, session, cid, group, t)
                    await asyncio.sleep(0.5)
            await asyncio.sleep(3)
