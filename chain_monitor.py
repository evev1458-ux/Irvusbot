import os
import asyncio
import aiohttp
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Free RPC endpoints
RPC_ENDPOINTS = {
    "eth":  "https://ethereum.publicnode.com",
    "bsc":  "https://bsc-dataseed.binance.org",
    "base": "https://mainnet.base.org",
}

# Free API endpoints
DEXSCREENER_API = "https://api.dexscreener.com/latest/dex/tokens"
SOLANA_TX_API   = "https://api.mainnet-beta.solana.com"
BIRDEYE_API     = "https://public-api.birdeye.so/defi/txs/token"


class ChainMonitor:
    def __init__(self, db, bot, buy_alert):
        self.db = db
        self.bot = bot
        self.buy_alert = buy_alert
        self.running = True

    async def start_monitoring(self):
        """Ana monitoring döngüsü"""
        logger.info("🔍 Chain monitoring başlatıldı")
        while self.running:
            try:
                groups = self.db.get_all_groups_with_tokens()
                tasks = []
                for group in groups:
                    for token in group["tokens"]:
                        tasks.append(
                            self.check_token_buys(
                                group["chat_id"],
                                token["ca"],
                                token["chain"],
                                group["config"]
                            )
                        )
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
            except Exception as e:
                logger.error(f"Monitoring ana döngü hatası: {e}")
            await asyncio.sleep(15)  # Her 15 saniyede kontrol

    async def check_token_buys(self, chat_id: int, ca: str, chain: str, config: dict):
        """Belirli bir token için yeni alımları kontrol et"""
        try:
            if chain == "sol":
                await self.check_solana_buys(chat_id, ca, config)
            else:
                await self.check_evm_buys(chat_id, ca, chain, config)
        except Exception as e:
            logger.error(f"Token kontrol hatası {ca} ({chain}): {e}")

    # ─────────────────────────────────────────────
    # DexScreener ile EVM (ETH/BSC/BASE) buy tespiti
    # ─────────────────────────────────────────────
    async def check_evm_buys(self, chat_id: int, ca: str, chain: str, config: dict):
        url = f"{DEXSCREENER_API}/{ca}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return
                data = await resp.json()

        pairs = data.get("pairs", [])
        if not pairs:
            return

        # En yüksek likiditeye sahip pair'i seç
        pair = max(pairs, key=lambda x: float(x.get("liquidity", {}).get("usd", 0) or 0))

        # Son tx'leri DexScreener'dan al
        pair_address = pair.get("pairAddress", "")
        if not pair_address:
            return

        await self.fetch_dexscreener_txs(chat_id, ca, chain, config, pair, pair_address)

    async def fetch_dexscreener_txs(self, chat_id, ca, chain, config, pair_info, pair_address):
        """DexScreener trades endpoint'inden son alımları al"""
        # DexScreener trades API
        chain_map = {"eth": "ethereum", "bsc": "bsc", "base": "base"}
        ds_chain = chain_map.get(chain, chain)
        url = f"https://api.dexscreener.com/latest/dex/pairs/{ds_chain}/{pair_address}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return
                data = await resp.json()

        pair = data.get("pair", data.get("pairs", [{}])[0] if data.get("pairs") else {})
        if not pair:
            return

        # Token bilgileri
        base_token = pair.get("baseToken", {})
        token_name = base_token.get("name", "Unknown")
        token_symbol = base_token.get("symbol", "???")
        price_usd = float(pair.get("priceUsd", 0) or 0)
        mcap = pair.get("fdv") or pair.get("marketCap", 0)
        if mcap:
            mcap = float(mcap)

        # Txns verisi (son alımları simüle et - DexScreener volume'dan)
        txns = pair.get("txns", {})
        buys_5m = txns.get("m5", {}).get("buys", 0)

        last_tx_key = f"{ca}_{chain}"
        last_sent = self.db.get_last_tx(chat_id, last_tx_key)
        current_marker = f"{pair.get('volume',{}).get('m5',0)}_{buys_5m}"

        if last_sent == current_marker or buys_5m == 0:
            return

        # Min buy kontrolü
        min_buy = float(config.get("min_buy", 0))
        volume_5m = float(pair.get("volume", {}).get("m5", 0) or 0)

        if volume_5m < min_buy and min_buy > 0:
            return

        # Alım miktarını hesapla (ortalama)
        avg_buy_usd = volume_5m / buys_5m if buys_5m > 0 else volume_5m
        tokens_received = avg_buy_usd / price_usd if price_usd > 0 else 0

        tx_data = {
            "token_name": token_name,
            "token_symbol": token_symbol,
            "amount_usd": avg_buy_usd,
            "tokens_received": tokens_received,
            "mcap": mcap,
            "price_usd": price_usd,
            "chain": chain,
            "ca": ca,
            "tx_hash": current_marker,
            "pair_url": pair.get("url", ""),
        }

        self.db.set_last_tx(chat_id, last_tx_key, current_marker)
        await self.buy_alert.send_buy_alert(self.bot, chat_id, tx_data, config)

    # ─────────────────────────────────────────────
    # Solana buy tespiti (Birdeye veya DexScreener)
    # ─────────────────────────────────────────────
    async def check_solana_buys(self, chat_id: int, ca: str, config: dict):
        url = f"{DEXSCREENER_API}/{ca}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return
                data = await resp.json()

        pairs = data.get("pairs", [])
        if not pairs:
            return

        pair = max(pairs, key=lambda x: float(x.get("liquidity", {}).get("usd", 0) or 0))
        pair_address = pair.get("pairAddress", "")
        if not pair_address:
            return

        await self.fetch_solana_txs(chat_id, ca, config, pair)

    async def fetch_solana_txs(self, chat_id, ca, config, pair):
        """Solana token alımlarını işle"""
        base_token = pair.get("baseToken", {})
        token_name = base_token.get("name", "Unknown")
        token_symbol = base_token.get("symbol", "???")
        price_usd = float(pair.get("priceUsd", 0) or 0)
        mcap = float(pair.get("fdv") or pair.get("marketCap", 0) or 0)

        txns = pair.get("txns", {})
        buys_5m = txns.get("m5", {}).get("buys", 0)
        volume_5m = float(pair.get("volume", {}).get("m5", 0) or 0)

        last_tx_key = f"{ca}_sol"
        last_sent = self.db.get_last_tx(chat_id, last_tx_key)
        current_marker = f"{volume_5m}_{buys_5m}"

        if last_sent == current_marker or buys_5m == 0:
            return

        min_buy = float(config.get("min_buy", 0))
        avg_buy_usd = volume_5m / buys_5m if buys_5m > 0 else volume_5m

        if avg_buy_usd < min_buy and min_buy > 0:
            return

        tokens_received = avg_buy_usd / price_usd if price_usd > 0 else 0

        tx_data = {
            "token_name": token_name,
            "token_symbol": token_symbol,
            "amount_usd": avg_buy_usd,
            "tokens_received": tokens_received,
            "mcap": mcap,
            "price_usd": price_usd,
            "chain": "sol",
            "ca": ca,
            "tx_hash": current_marker,
            "pair_url": pair.get("url", ""),
        }

        self.db.set_last_tx(chat_id, last_tx_key, current_marker)
        await self.buy_alert.send_buy_alert(self.bot, chat_id, tx_data, config)
