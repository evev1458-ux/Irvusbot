import aiohttp
import asyncio
import logging
from database import Database

logger = logging.getLogger(__name__)
db = Database()
seen_txs = set()

async def fetch_buys(ca, chain):
    buys = []
    # Değişkenleri en başta tanımla
    pair_addr, price_usd, name, symbol, mcap = None, 0, "Token", "???", 0
    chain_map = {"eth": "ethereum", "bsc": "bsc", "base": "base", "sol": "solana"}
    dex_chain = chain_map.get(chain, chain)

    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{ca}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    pairs = data.get("pairs", [])
                    for p in pairs:
                        # Solana ise ilk çifti, EVM ise zincir eşleşeni al
                        if chain == "sol" or p.get("chainId", "").lower() == dex_chain:
                            pair_addr = p.get("pairAddress")
                            price_usd = float(p.get("priceUsd", 0))
                            name = p.get("baseToken", {}).get("name", "Token")
                            symbol = p.get("baseToken", {}).get("symbol", "???")
                            mcap = p.get("marketCap", 0)
                            break
        
        if not pair_addr: return []

        trades_url = f"https://api.dexscreener.com/latest/dex/trades/{pair_addr}"
        async with aiohttp.ClientSession() as session:
            async with session.get(trades_url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    trades = data if isinstance(data, list) else data.get("trades", [])
                    for tx in trades:
                        if tx.get("type") != "buy": continue
                        tx_hash = tx.get("txHash")
                        if not tx_hash or tx_hash in seen_txs: continue
                        seen_txs.add(tx_hash)
                        if len(seen_txs) > 2000: seen_txs.clear()

                        buys.append({
                            "tx_hash": tx_hash, "amount_usd": float(tx.get("amountUsd", 0)),
                            "amount_token": float(tx.get("amount1", 0)), "price_usd": price_usd,
                            "mcap": mcap, "name": name, "symbol": symbol, "chain": chain, "ca": ca
                        })
    except Exception as e:
        logger.error(f"Error on {chain} {ca}: {e}")
    return buys

class ChainMonitor:
    def __init__(self, app): self.app = app
    async def start(self):
        logger.info("İzleme Başladı...")
        while True:
            try:
                groups = db.get_all_groups_with_tokens()
                for g in groups:
                    for t in g["config"].get("tokens", []):
                        buys = await fetch_buys(t["ca"], t["chain"])
                        for b in buys:
                            if b["amount_usd"] >= float(g["config"].get("min_buy", 0)):
                                await self._send(g["chat_id"], g["config"], b)
            except Exception as e: logger.error(f"Loop error: {e}")
            await asyncio.sleep(15)

    async def _send(self, chat_id, cfg, buy):
        from buy_alert import build_buy_message
        try:
            text, _ = build_buy_message(buy, cfg)
            mid, mtype = cfg.get("media_file_id"), cfg.get("media_type", "photo")
            if mid:
                if mtype == "animation": await self.app.bot.send_animation(chat_id, mid, caption=text, parse_mode="Markdown")
                elif mtype == "video": await self.app.bot.send_video(chat_id, mid, caption=text, parse_mode="Markdown")
                else: await self.app.bot.send_photo(chat_id, mid, caption=text, parse_mode="Markdown")
            else: await self.app.bot.send_message(chat_id, text, parse_mode="Markdown")
        except: pass
            
