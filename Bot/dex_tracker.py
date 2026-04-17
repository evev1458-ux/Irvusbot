"""
DexScreener API wrapper + buy alert message builder.
"""

import aiohttp
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

DEXSCREENER_BASE = "https://api.dexscreener.com"

NETWORK_MAP = {
    "ETH": "ethereum",
    "SOL": "solana",
    "BSC": "bsc",
    "BASE": "base",
}

NETWORK_DISPLAY = {
    "ETH": "Ethereum",
    "SOL": "Solana",
    "BSC": "BNB Chain",
    "BASE": "Base",
}

DEXSCREENER_LINKS = {
    "ETH": "https://dexscreener.com/ethereum/{}",
    "SOL": "https://dexscreener.com/solana/{}",
    "BSC": "https://dexscreener.com/bsc/{}",
    "BASE": "https://dexscreener.com/base/{}",
}

SOLSCAN_TX = "https://solscan.io/tx/{}"
ETHERSCAN_TX = "https://etherscan.io/tx/{}"
BSCSCAN_TX = "https://bscscan.com/tx/{}"
BASESCAN_TX = "https://basescan.org/tx/{}"

TX_EXPLORERS = {
    "SOL": SOLSCAN_TX,
    "ETH": ETHERSCAN_TX,
    "BSC": BSCSCAN_TX,
    "BASE": BASESCAN_TX,
}


async def fetch_pair_data(contract_address: str, network: str) -> Optional[dict]:
    """Fetch the highest-liquidity pair for a token from DexScreener."""
    chain = NETWORK_MAP.get(network, network.lower())
    url = f"{DEXSCREENER_BASE}/tokens/v1/{chain}/{contract_address}"
    logger.info("[DexScreener] GET %s", url)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=15),
                headers={"Accept": "application/json"},
            ) as resp:
                logger.info("[DexScreener] Status: %s", resp.status)
                if resp.status == 429:
                    logger.warning("[DexScreener] Rate limited")
                    return None
                if resp.status != 200:
                    logger.warning("[DexScreener] Non-200: %s", resp.status)
                    return None

                data = await resp.json(content_type=None)
                pairs = data if isinstance(data, list) else data.get("pairs", [])

                if not pairs:
                    logger.warning("[DexScreener] No pairs for %s on %s", contract_address, network)
                    return None

                pairs.sort(
                    key=lambda p: float((p.get("liquidity") or {}).get("usd", 0) or 0),
                    reverse=True,
                )
                best = pairs[0]
                logger.info(
                    "[DexScreener] Pair: %s | liq=$%.0f",
                    best.get("pairAddress"),
                    float((best.get("liquidity") or {}).get("usd", 0) or 0),
                )
                return best

    except asyncio.TimeoutError:
        logger.error("[DexScreener] Timeout for %s", contract_address)
    except Exception as e:
        logger.error("[DexScreener] Error: %s", e, exc_info=True)
    return None


def extract_token_info(pair: dict, contract_address: str, network: str) -> dict:
    """Extract a clean token-info dict from a raw DexScreener pair."""
    base_token = pair.get("baseToken") or {}
    quote_token = pair.get("quoteToken") or {}

    if base_token.get("address", "").lower() == contract_address.lower():
        token = base_token
    elif quote_token.get("address", "").lower() == contract_address.lower():
        token = quote_token
    else:
        token = base_token

    price_usd = float(pair.get("priceUsd") or 0)
    market_cap = float(pair.get("marketCap") or pair.get("fdv") or 0)
    pair_address = pair.get("pairAddress", contract_address)

    txns_m5 = (pair.get("txns") or {}).get("m5") or {}
    txns_h1 = (pair.get("txns") or {}).get("h1") or {}
    volume = pair.get("volume") or {}

    return {
        "name": token.get("name", "Unknown"),
        "symbol": token.get("symbol", "???"),
        "price_usd": price_usd,
        "market_cap": market_cap,
        "pair_address": pair_address,
        "contract_address": contract_address,
        "network": network,
        "dexscreener_url": DEXSCREENER_LINKS.get(network, "").format(pair_address),
        "liquidity_usd": float((pair.get("liquidity") or {}).get("usd", 0) or 0),
        "volume_m5": float(volume.get("m5", 0) or 0),
        "volume_h1": float(volume.get("h1", 0) or 0),
        "volume_h24": float(volume.get("h24", 0) or 0),
        "buys_m5": int(txns_m5.get("buys", 0)),
        "sells_m5": int(txns_m5.get("sells", 0)),
        "buys_h1": int(txns_h1.get("buys", 0)),
        "price_change_h24": float((pair.get("priceChange") or {}).get("h24", 0) or 0),
    }


async def get_token_info(contract_address: str, network: str) -> Optional[dict]:
    """Fetch and return clean token info, or None on failure."""
    pair = await fetch_pair_data(contract_address, network)
    if pair is None:
        return None
    return extract_token_info(pair, contract_address, network)


async def validate_contract(contract_address: str, network: str) -> Optional[dict]:
    return await get_token_info(contract_address, network)


# ─── Formatting ──────────────────────────────────────────────────────────────

def format_usd(num: float) -> str:
    """Format to compact USD: $1.50M, $38.4K, $150.00"""
    if num >= 1_000_000_000:
        return f"${num / 1_000_000_000:.2f}B"
    elif num >= 1_000_000:
        return f"${num / 1_000_000:.2f}M"
    elif num >= 1_000:
        return f"${num / 1_000:.1f}K"
    else:
        return f"${num:.2f}"


# Keep backward-compat alias
format_number = format_usd


def format_token_amount(amount: float) -> str:
    """Format token amount with commas and abbreviations."""
    if amount >= 1_000_000_000:
        return f"{amount / 1_000_000_000:.2f}B"
    elif amount >= 1_000_000:
        return f"{amount / 1_000_000:.2f}M"
    elif amount >= 1_000:
        return f"{amount:,.0f}"
    else:
        return f"{amount:.4f}"


def get_emoji_bar(usd_amount: float, emoji: str = "🟢") -> str:
    """Dynamic emoji bar scaled to buy size."""
    if usd_amount < 50:
        count = 1
    elif usd_amount < 200:
        count = 3
    elif usd_amount < 500:
        count = 5
    elif usd_amount < 1_000:
        count = 8
    elif usd_amount < 5_000:
        count = 12
    elif usd_amount < 20_000:
        count = 16
    else:
        count = 20
    return emoji * count


def _esc(text: str) -> str:
    """Escape MarkdownV2 special characters."""
    specials = r"\_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{c}" if c in specials else c for c in str(text))


# Keep backward-compat alias
escape_md2 = _esc


def build_buy_alert(
    token_name: str,
    token_symbol: str,
    usd_spent: float,
    tokens_received: float,
    market_cap: float,
    network: str,
    chart_url: str,
    config: dict,
    *,
    native_amount: float = 0.0,
    native_symbol: str = "",
    buyer_wallet: str = "",
    txn_url: str = "",
) -> str:
    """
    Build the Telegram MarkdownV2 buy alert in the clean standard format:

      Token Name ($SYMBOL) Buy!
      🟢🟢🟢🟢🟢

      🔄 0.75 SOL ($112.50)
      🔄 2,958,500 $SYMBOL
      👤 Ab3x...F7k2 | Txn
      🎖️ Market Cap $38.4K

      [social links]
    """
    emoji = config.get("custom_emoji") or "🟢"
    emoji_bar = get_emoji_bar(usd_amount=usd_spent, emoji=emoji)

    safe_name = _esc(token_name)
    safe_sym = _esc(token_symbol)

    lines: list[str] = [
        f"*{safe_name}* \\(${safe_sym}\\) Buy\\!",
        "",
        emoji_bar,
        "",
    ]

    # Line 1: native token amount + USD value
    if native_amount > 0 and native_symbol:
        nat_str = f"{native_amount:.4f}".rstrip("0").rstrip(".")
        lines.append(
            f"🔄 *{_esc(nat_str)} {_esc(native_symbol)}* "
            f"\\(${_esc(f'{usd_spent:,.2f}')}\\)"
        )
    else:
        lines.append(f"🔄 *${_esc(f'{usd_spent:,.2f}')}*")

    # Line 2: token amount
    tok_str = format_token_amount(tokens_received)
    lines.append(f"🔄 *{_esc(tok_str)}* ${safe_sym}")

    # Line 3: wallet | txn link
    if buyer_wallet and txn_url:
        short_wallet = f"{buyer_wallet[:4]}\\.\\.\\. {buyer_wallet[-4:]}"
        lines.append(f"👤 `{buyer_wallet[:4]}...{buyer_wallet[-4:]}` \\| [Txn]({txn_url})")
    elif txn_url:
        lines.append(f"👤 [View Transaction]({txn_url})")
    elif buyer_wallet:
        short_wallet = f"{buyer_wallet[:4]}...{buyer_wallet[-4:]}"
        lines.append(f"👤 `{short_wallet}`")

    # Line 4: market cap
    mcap_str = _esc(format_usd(market_cap))
    lines.append(f"🎖️ Market Cap {mcap_str}")

    # Chart link
    lines.append("")
    lines.append(f"📊 [Chart]({chart_url})")

    # Social links
    socials: list[str] = []
    if config.get("telegram_link"):
        socials.append(f"[TG]({config['telegram_link']})")
    if config.get("website_link"):
        socials.append(f"[Web]({config['website_link']})")
    if config.get("x_link"):
        socials.append(f"[X]({config['x_link']})")
    if socials:
        lines.append(" \\| ".join(socials))

    return "\n".join(lines)
