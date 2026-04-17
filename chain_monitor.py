import aiohttp
import asyncio
import logging
import os
from database import Database

logger = logging.getLogger(__name__)
db = Database()

# Son görülen tx hash'leri (tekrar bildirimi önle)
seen_txs = set()

# ─── Fiyat & MCAP çek ─────────────────────────────────────────────────────────
async def get_token_info_sol(ca: str) -> dict:
    """DexScreener'dan Solana token bilgisi çek"""
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{ca}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    pairs = data.get("pairs", [])
                    if pairs:
                        p = pairs[0]
                        return {
                            "name": p.get("baseToken", {}).get("name", "Token"),
                            "symbol": p.get("baseToken", {}).get("symbol", "???"),
                            "price_usd": float(p.get("priceUsd", 0)),
                            "mcap": p.get("marketCap", 0),
                            "price_native": float(p.get("priceNative", 0)),
                        }
    except Exception as e:
        logger.error(f"Token info error SOL {ca}: {e}")
    return {}

async def get_token_info_evm(ca: str, chain: str) -> dict:
    """DexScreener'dan EVM token bilgisi çek"""
    chain_map = {"eth": "ethereum", "bsc": "bsc", "base": "base"}
    dex_chain = chain_map.get(chain, chain)
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{ca}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    pairs = data.get("pairs", [])
                    for p in pairs:
                        if p.get("chainId", "").lower() == dex_chain:
                            return {
                                "name": p.get("baseToken", {}).get("name", "Token"),
                                "symbol": p.get("baseToken", {}).get("symbol", "???"),
                                "price_usd": float(p.get("priceUsd", 0)),
                                "mcap": p.get("marketCap", 0),
                                "price_native": float(p.get("priceNative", 0)),
                            }
    except Exception as e:
        logger.error(f"Token info error EVM {ca}: {e}")
    return {}

# ─── Solana alım tespiti ───────────────────────────────────────────────────────
async def get_sol_buys(ca: str) -> list:
    """Solana: DexScreener trades endpoint"""
    buys = []
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{ca}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    pairs = data.get("pairs", [])
                    if not pairs:
                        return []
                    pair_addr = pairs[0].get("pairAddress", "")
                    price_usd = float(pairs[0].get("priceUsd", 0))
                    name = pairs[0].get("baseToken", {}).get("name", "Token")
                    symbol = pairs[0].get("baseToken", {}).get("symbol", "???")
                    mcap = pairs[0].get("marketCap", 0)

        # Trades çek
        trades_url = f"https://api.dexscreener.com/latest/dex/trades/{pair_addr}"
        async with aiohttp.ClientSession() as session:
            async with session.get(trades_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    trades = await resp.json()
                    for tx in trades:
                        if tx.get("type") != "buy":
                            continue
                        tx_hash = tx.get("txHash", "")
                        if tx_hash in seen_txs:
                            continue
                        seen_txs.add(tx_hash)
                        if len(seen_txs) > 5000:
                            seen_txs.clear()

                        amount_usd = float(tx.get("amountUsd", 0))
                        amount_token = float(tx.get("amount1", 0))

                        buys.append({
                            "tx_hash": tx_hash,
                            "amount_usd": amount_usd,
                            "amount_token": amount_token,
                            "price_usd": price_usd,
                            "mcap": mcap,
                            "name": name,
                            "symbol": symbol,
                            "chain": "sol",
                            "ca": ca,
                        })
    except Exception as e:
        logger.error(f"SOL trades error {ca}: {e}")
    return buys

async def get_evm_buys(ca: str, chain: str) -> list:
    """EVM zincirler: DexScreener trades"""
    buys = []
    chain_map = {"eth": "ethereum", "bsc": "bsc", "base": "base"}
    dex_chain = chain_map.get(chain, chain)
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{ca}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    pairs = data.get("pairs", [])
                    pair_addr = None
                    price_usd = 0
                    name = "Token"
                    symbol = "???"
                    mcap = 0
                    for p in pairs:
                        if p.get("chainId", "").lower() == dex_chain:
                            pair_addr = p.get("pairAddress", "")
                            price_usd = float(p.get("priceUsd", 0))
                            name = p.get("baseToken", {}).get("name", "Token")
                            symbol = p.get("baseToken", {}).get("symbol", "???")
                            mcap = p.get("marketCap", 0)
                            break
                    if not pair_addr:
                        return []

        trades_url = f"https://api.dexscreener.com/latest/dex/trades/{pair_addr}"
        async with aiohttp.ClientSession() as session:
            async with session.get(trades_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    trades = await resp.json()
                    for tx in trades:
                        if tx.get("type") != "buy":
                            continue
                        tx_hash = tx.get("txHash", "")
                        if tx_hash in seen_txs:
                            continue
                        seen_txs.add(tx_hash)

                        amount_usd = float(tx.get("amountUsd", 0))
                        amount_token = float(tx.get("amount1", 0))

                        buys.append({
                            "tx_hash": tx_hash,
                            "amount_usd": amount_usd,
                            "amount_token": amount_token,
                            "price_usd": price_usd,
                            "mcap": mcap,
                            "name": name,
                            "symbol": symbol,
                            "chain": chain,
                            "ca": ca,
                        })
    except Exception as e:
        logger.error(f"EVM trades error {ca} {chain}: {e}")
    return buys


class ChainMonitor:
    def __init__(self, application):
        self.application = application
        self.running = False

    async def start(self):
        self.running = True
        logger.info("ChainMonitor başlatıldı.")
        while self.running:
            try:
                await self._check_all_groups()
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
            await asyncio.sleep(15)  # 15 saniyede bir kontrol

    async def _check_all_groups(self):
        groups = db.get_all_groups_with_tokens()
        for group in groups:
            chat_id = group["chat_id"]
            cfg = group["config"]
            tokens = cfg.get("tokens", [])
            min_buy = float(cfg.get("min_buy", 0))

            for token in tokens:
                ca = token["ca"]
                chain = token["chain"]

                if chain == "sol":
                    buys = await get_sol_buys(ca)
                else:
                    buys = await get_evm_buys(ca, chain)

                for buy in buys:
                    if buy["amount_usd"] < min_buy:
                        continue
                    await self._send_buy_alert(chat_id, cfg, buy)

    async def _send_buy_alert(self, chat_id: int, cfg: dict, buy: dict):
        from buy_alert import build_buy_message
        try:
            text, emoji_bar = build_buy_message(buy, cfg)
            media_file_id = cfg.get("media_file_id")
            media_type = cfg.get("media_type", "photo")

            if media_file_id:
                if media_type == "animation":
                    await self.application.bot.send_animation(
                        chat_id=chat_id,
                        animation=media_file_id,
                        caption=text,
                        parse_mode="Markdown"
                    )
                elif media_type == "video":
                    await self.application.bot.send_video(
                        chat_id=chat_id,
                        video=media_file_id,
                        caption=text,
                        parse_mode="Markdown"
                    )
                else:
                    await self.application.bot.send_photo(
                        chat_id=chat_id,
                        photo=media_file_id,
                        caption=text,
                        parse_mode="Markdown"
                    )
            else:
                await self.application.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode="Markdown"
                )
        except Exception as e:
            logger.error(f"Send alert error {chat_id}: {e}")
                            
