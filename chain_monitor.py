import aiohttp
import asyncio
import logging
from database import db
from buy_alert import build_buy_message

logger = logging.getLogger(__name__)
seen_txs = set()

async def fetch_buys(ca, chain):
    buys = []
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{ca}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=12) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    pair = data.get("pairs", [{}])[0]
                    p_addr = pair.get("pairAddress")
                    if not p_addr: return []
                    
                    trades_url = f"https://api.dexscreener.com/latest/dex/trades/{p_addr}"
                    async with session.get(trades_url, timeout=12) as t_resp:
                        if t_resp.status == 200:
                            t_data = await t_resp.json()
                            trades = t_data.get("trades", []) if isinstance(t_data, dict) else t_data
                            for tx in trades:
                                if str(tx.get("type")).lower() != "buy": continue
                                tx_h = tx.get("txHash")
                                if not tx_h or tx_h in seen_txs: continue
                                seen_txs.add(tx_h)
                                buys.append({
                                    "tx_hash": tx_h, "amount_usd": float(tx.get("amountUsd", 0)),
                                    "mcap": pair.get("marketCap", 0), "name": pair.get("baseToken", {}).get("name", "Token"),
                                    "chain": chain, "ca": ca
                                })
    except: pass
    return buys

class ChainMonitor:
    def __init__(self, app): self.app = app
    async def start(self):
        while True:
            for g in db.get_all_groups_with_tokens():
                for t in g["config"].get("tokens", []):
                    for b in await fetch_buys(t["ca"], t["chain"]):
                        text, _ = build_buy_message(b, g["config"])
                        await self.app.bot.send_message(g["chat_id"], text, parse_mode="Markdown")
            await asyncio.sleep(15)
            
