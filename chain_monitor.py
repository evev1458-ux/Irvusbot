import asyncio
import logging
import aiohttp
from database import db
from buy_alert import build_buy_message

logger = logging.getLogger(__name__)
seen_txs = set()

async def fetch_buys(ca, chain):
    buys = []
    # Ağ isimlerini DexScreener formatına çevir
    chain_map = {"eth": "ethereum", "bsc": "bsc", "base": "base", "sol": "solana"}
    target_chain = chain_map.get(chain.lower(), chain.lower())
    
    try:
        # 1. Token genel verilerini ve parite adresini al
        url = f"https://api.dexscreener.com/latest/dex/tokens/{ca}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=12) as resp:
                if resp.status != 200: return []
                data = await resp.json()
                pairs = data.get("pairs", [])
                
                # Belirlenen ağdaki en yüksek likiditeli pariteyi seç
                pair = next((p for p in pairs if p.get("chainId") == target_chain), None)
                if not pair: return []
                
                p_addr = pair.get("pairAddress")
                price_usd = float(pair.get("priceUsd", 0))
                mcap = float(pair.get("marketCap", 0))
                name = pair.get("baseToken", {}).get("name", "Token")
                symbol = pair.get("baseToken", {}).get("symbol", "TOKEN")

                # 2. Gerçek zamanlı işlemleri (Trades) çek
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
                            # Tam rakamları listeye ekle
                            buys.append({
                                "tx_hash": tx_h,
                                "amount_usd": float(tx.get("amountUsd", 0)),
                                "amount_token": float(tx.get("amount1", 0)), # Gerçek adet
                                "price_usd": price_usd,
                                "mcap": mcap,
                                "name": name,
                                "symbol": symbol,
                                "chain": chain,
                                "ca": ca
                            })
    except Exception as e:
        logger.error(f"Sistem Hatası [{chain}]: {e}")
    
    if len(seen_txs) > 3000: seen_txs.clear()
    return buys

class ChainMonitor:
    def __init__(self, app):
        self.app = app

    async def start(self):
        logger.info("🚀 Gerçek Zamanlı İzleme Motoru Başlatıldı (SOL, ETH, BSC, BASE)")
        while True:
            try:
                # Veritabanındaki tüm grupları tara
                groups = db.get_all_groups_with_tokens()
                for g in groups:
                    chat_id = g["chat_id"]
                    config = g["config"]
                    
                    for t in config.get("tokens", []):
                        # Her bir token için alımları çek
                        new_buys = await fetch_buys(t["ca"], t["chain"])
                        for b in new_buys:
                            if b["amount_usd"] >= float(config.get("min_buy", 0)):
                                text, _ = build_buy_message(b, config)
                                # Mesajı gönder
                                await self.app.bot.send_message(chat_id, text, parse_mode="Markdown", disable_web_page_preview=True)
            except Exception as e:
                logger.error(f"Döngü hatası: {e}")
            
            await asyncio.sleep(15) # Render limitleri için 15 saniye ideal
