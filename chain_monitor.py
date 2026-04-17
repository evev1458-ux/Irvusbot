import aiohttp
import asyncio
import logging
from database import Database

logger = logging.getLogger(__name__)
db = Database()
seen_txs = set()

async def fetch_buys(ca, chain):
    """
    Tüm ağlar (SOL, ETH, BSC, BASE) için DexScreener üzerinden alımları çeker.
    """
    buys = []
    pair_addr, price_usd, name, symbol, mcap = None, 0, "Token", "???", 0
    
    # Zincir isimlerini DexScreener'ın beklediği formata sokuyoruz
    chain_clean = chain.lower().strip()
    chain_map = {
        "eth": "ethereum",
        "bsc": "bsc",
        "base": "base",
        "sol": "solana"
    }
    dex_chain = chain_map.get(chain_clean, chain_clean)

    try:
        # 1. ADIM: Token/Pair bilgilerini çek
        url = f"https://api.dexscreener.com/latest/dex/tokens/{ca}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=12) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    pairs = data.get("pairs", [])
                    if not pairs:
                        return []
                    
                    # İlgili ağdaki en yüksek likiditeli çifti bul
                    for p in pairs:
                        p_chain = p.get("chainId", "").lower()
                        # Solana ise genelde ilk çift doğrudur, EVM ise zincir kontrolü yap
                        if chain_clean == "sol" or p_chain == dex_chain:
                            pair_addr = p.get("pairAddress")
                            price_usd = float(p.get("priceUsd", 0))
                            name = p.get("baseToken", {}).get("name", "Token")
                            symbol = p.get("baseToken", {}).get("symbol", "???")
                            mcap = p.get("marketCap", 0)
                            break
        
        if not pair_addr:
            return []

        # 2. ADIM: Son işlemleri (Trades) çek
        trades_url = f"https://api.dexscreener.com/latest/dex/trades/{pair_addr}"
        async with aiohttp.ClientSession() as session:
            async with session.get(trades_url, timeout=12) as resp:
                if resp.status == 200:
                    trade_data = await resp.json()
                    
                    # DexScreener yanıtı bazen {'trades': [...]} bazen direkt [...] listesidir
                    if isinstance(trade_data, dict):
                        trades = trade_data.get("trades", [])
                    else:
                        trades = trade_data
                    
                    if not isinstance(trades, list):
                        return []

                    for tx in trades:
                        # Sadece ALIMLARI filtrele
                        if str(tx.get("type", "")).lower() != "buy":
                            continue
                            
                        tx_hash = tx.get("txHash")
                        if not tx_hash or tx_hash in seen_txs:
                            continue
                        
                        # Yeni işlem bulundu!
                        seen_txs.add(tx_hash)
                        # Hafıza dolmasın diye temizlik (5000 işlemde bir)
                        if len(seen_txs) > 5000:
                            seen_txs.clear()

                        buys.append({
                            "tx_hash": tx_hash,
                            "amount_usd": float(tx.get("amountUsd", 0)),
                            "amount_token": float(tx.get("amount1", 0)),
                            "price_usd": price_usd,
                            "mcap": mcap,
                            "name": name,
                            "symbol": symbol,
                            "chain": chain_clean,
                            "ca": ca
                        })
    except Exception as e:
        logger.error(f"Hata [{chain_clean}] {ca}: {e}")
    return buys

class ChainMonitor:
    def __init__(self, app):
        self.app = app

    async def start(self):
        logger.info("🚀 Tüm ağlar için izleme döngüsü başlatıldı (ETH, BSC, SOL, BASE)")
        while True:
            try:
                # Veritabanındaki tüm grupları ve tokenları çek
                groups = db.get_all_groups_with_tokens()
                
                for group in groups:
                    chat_id = group["chat_id"]
                    config = group["config"]
                    tokens = config.get("tokens", [])
                    min_buy = float(config.get("min_buy", 0))

                    for token in tokens:
                        ca = token["ca"]
                        chain = token["chain"]
                        
                        # Alımları sorgula
                        new_buys = await fetch_buys(ca, chain)
                        
                        for buy in new_buys:
                            if buy["amount_usd"] >= min_buy:
                                await self._send_alert(chat_id, config, buy)
                                
            except Exception as e:
                logger.error(f"Monitör ana döngü hatası: {e}")
            
            # API'yi yormadan seri kontrol (10 saniye idealdir)
            await asyncio.sleep(10)

    async def _send_alert(self, chat_id, cfg, buy):
        from buy_alert import build_buy_message
        try:
            text, _ = build_buy_message(buy, cfg)
            media_id = cfg.get("media_file_id")
            m_type = cfg.get("media_type", "photo")

            if media_id:
                if m_type == "animation":
                    await self.app.bot.send_animation(chat_id, media_id, caption=text, parse_mode="Markdown")
                elif m_type == "video":
                    await self.app.bot.send_video(chat_id, media_id, caption=text, parse_mode="Markdown")
                else:
                    await self.app.bot.send_photo(chat_id, media_id, caption=text, parse_mode="Markdown")
            else:
                await self.app.bot.send_message(chat_id, text, parse_mode="Markdown")
            
            logger.info(f"✅ Bildirim Gönderildi: {buy['symbol']} - {buy['amount_usd']}$")
        except Exception as e:
            logger.error(f"Mesaj Gönderim Hatası: {e}")
                        
