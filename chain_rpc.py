"""
On-chain RPC helpers for extracting real swap transaction data.

Solana: Uses public JSON-RPC to get actual tx signatures, buyer wallets,
        exact SOL/token amounts — no API key required.
EVM:    Falls back gracefully to DexScreener volume estimates.
"""

import asyncio
import logging
import time
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)

# ─── Solana ──────────────────────────────────────────────────────────────────

SOLANA_RPC_ENDPOINTS = [
    "https://api.mainnet-beta.solana.com",
    "https://solana-rpc.publicnode.com",
    "https://mainnet-ams.chainbuff.com",
]

SOLSCAN_TX = "https://solscan.io/tx/{}"
SOLSCAN_WALLET = "https://solscan.io/account/{}"

# Simple in-memory rate limit: max 5 req/s per endpoint
_rpc_last_call: dict[str, float] = {}
RPC_MIN_INTERVAL = 0.25  # 250ms = 4 req/s


async def _solana_rpc(method: str, params: list, timeout: int = 12) -> Optional[dict]:
    """
    Call a Solana JSON-RPC method, rotating endpoints on failure.
    Retries with exponential backoff on 429 (rate limit).
    """
    for attempt, endpoint in enumerate(SOLANA_RPC_ENDPOINTS):
        # Rate limit guard
        elapsed = time.time() - _rpc_last_call.get(endpoint, 0)
        if elapsed < RPC_MIN_INTERVAL:
            await asyncio.sleep(RPC_MIN_INTERVAL - elapsed)
        _rpc_last_call[endpoint] = time.time()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    headers={"Content-Type": "application/json"},
                ) as resp:
                    if resp.status == 429:
                        backoff = 2 ** attempt  # 1s, 2s, 4s…
                        logger.warning(
                            "[rpc] %s rate-limited (429) — backing off %ds", endpoint, backoff
                        )
                        await asyncio.sleep(backoff)
                        continue
                    if resp.status == 403:
                        logger.warning("[rpc] %s returned 403 (access denied)", endpoint)
                        continue
                    if resp.status != 200:
                        logger.warning("[rpc] %s returned %s", endpoint, resp.status)
                        continue
                    data = await resp.json(content_type=None)
                    if "error" in data:
                        err = data["error"]
                        # -32005 = node is behind / slot not available
                        if isinstance(err, dict) and err.get("code") in (-32005, -32009):
                            logger.warning("[rpc] %s slot error: %s", endpoint, err)
                            continue
                        logger.warning("[rpc] %s error: %s", method, err)
                        continue
                    return data.get("result")
        except asyncio.TimeoutError:
            logger.warning("[rpc] Timeout on %s %s", endpoint, method)
        except Exception as e:
            logger.warning("[rpc] %s %s: %s", endpoint, method, e)

    return None


async def get_signatures_for_address(
    address: str, limit: int = 20, before: Optional[str] = None
) -> list[dict]:
    """Get recent confirmed transaction signatures for a Solana address."""
    params_opts: dict = {"limit": limit, "commitment": "confirmed"}
    if before:
        params_opts["before"] = before

    result = await _solana_rpc("getSignaturesForAddress", [address, params_opts])
    if result is None:
        return []
    return result  # list of {signature, slot, blockTime, err, memo}


async def get_transaction(signature: str) -> Optional[dict]:
    """Fetch a parsed Solana transaction."""
    result = await _solana_rpc(
        "getTransaction",
        [signature, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0,
                     "commitment": "confirmed"}],
        timeout=15,
    )
    return result


def extract_swap_data(tx: dict, target_mint: str) -> Optional[dict]:
    """
    Extract swap data from a parsed Solana transaction.

    Returns dict with:
      - signature
      - buyer_wallet
      - sol_spent       (float, in SOL)
      - tokens_received (float, in token units)
      - is_buy          (bool)
    Or None if the tx is not a relevant buy.
    """
    if not tx:
        return None
    meta = tx.get("meta") or {}
    if meta.get("err"):
        return None  # failed transaction

    try:
        account_keys = tx["transaction"]["message"]["accountKeys"]
        buyer_wallet: str = account_keys[0]["pubkey"]

        pre_balances: list[int] = meta.get("preBalances", [])
        post_balances: list[int] = meta.get("postBalances", [])
        fee: int = meta.get("fee", 0)

        if not pre_balances or not post_balances:
            return None

        # SOL balance change for the signer (index 0)
        sol_change_lamports = pre_balances[0] - post_balances[0] - fee
        sol_spent = sol_change_lamports / 1e9

        # If signer's SOL didn't decrease, it's likely a sell or irrelevant tx
        if sol_spent <= 0.001:  # allow small dust
            return None

        # Find token balance change for the buyer
        pre_token_by_idx = {
            tb["accountIndex"]: tb
            for tb in (meta.get("preTokenBalances") or [])
        }
        post_token_by_idx = {
            tb["accountIndex"]: tb
            for tb in (meta.get("postTokenBalances") or [])
        }

        tokens_received = 0.0
        matched_mint = None

        # Look for an increase in token balance for the buyer's accounts
        for idx, post_tb in post_token_by_idx.items():
            mint = post_tb.get("mint", "")
            # Filter to target token mint if provided
            if target_mint and mint.lower() != target_mint.lower():
                continue

            pre_tb = pre_token_by_idx.get(idx)
            pre_amt = float((pre_tb or {}).get("uiTokenAmount", {}).get("uiAmount") or 0)
            post_amt = float(post_tb.get("uiTokenAmount", {}).get("uiAmount") or 0)
            delta = post_amt - pre_amt

            if delta > 0:
                tokens_received += delta
                matched_mint = mint

        # Only report if we found token receipts OR it's a known swap program call
        # (some buys go through wrapped accounts and the buyer doesn't directly hold)
        if tokens_received <= 0 and not _is_swap_program(tx):
            return None

        sigs = tx.get("transaction", {}).get("signatures", [])
        signature = sigs[0] if sigs else ""

        return {
            "signature": signature,
            "buyer_wallet": buyer_wallet,
            "sol_spent": sol_spent,
            "tokens_received": tokens_received,
            "mint": matched_mint,
            "is_buy": True,
        }

    except (KeyError, IndexError, TypeError) as e:
        logger.debug("[rpc] extract_swap_data error: %s", e)
        return None


def _is_swap_program(tx: dict) -> bool:
    """Heuristic: check if well-known DEX program IDs are invoked."""
    SWAP_PROGRAMS = {
        "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",  # Raydium AMM v4
        "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4",  # Jupiter v6
        "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc",   # Orca Whirlpool
        "9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP",  # Orca v1
        "RVKd61ztZW9GUwhRbbLoYVRE5Xf1B2tVscKqwZqXgEr",   # Raydium CLMM
    }
    try:
        inner = tx.get("meta", {}).get("innerInstructions") or []
        for group in inner:
            for instr in group.get("instructions", []):
                prog = instr.get("programId", "")
                if prog in SWAP_PROGRAMS:
                    return True
        # Also check top-level
        for instr in tx.get("transaction", {}).get("message", {}).get("instructions", []):
            prog = instr.get("programId", "")
            if prog in SWAP_PROGRAMS:
                return True
    except Exception:
        pass
    return False


def shorten_wallet(wallet: str) -> str:
    """Shorten a wallet address: show first 4 + last 4 chars."""
    if not wallet or len(wallet) < 10:
        return wallet
    return f"{wallet[:4]}...{wallet[-4:]}"


# ─── Native Token Prices ──────────────────────────────────────────────────────

_price_cache: dict[str, float] = {}
_price_cache_ts: float = 0
PRICE_CACHE_TTL = 60  # seconds

COINGECKO_IDS = {
    "SOL": "solana",
    "ETH": "ethereum",
    "BSC": "binancecoin",
    "BASE": "ethereum",
}

NATIVE_SYMBOLS = {
    "SOL": "SOL",
    "ETH": "ETH",
    "BSC": "BNB",
    "BASE": "ETH",
}


async def get_native_prices() -> dict[str, float]:
    """
    Fetch native token prices in USD from CoinGecko free API.
    Results are cached for 60 seconds.
    """
    global _price_cache, _price_cache_ts

    now = time.time()
    if _price_cache and (now - _price_cache_ts) < PRICE_CACHE_TTL:
        return _price_cache

    ids = "solana,ethereum,binancecoin"
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    _price_cache = {
                        "solana": float(data.get("solana", {}).get("usd", 150)),
                        "ethereum": float(data.get("ethereum", {}).get("usd", 3000)),
                        "binancecoin": float(data.get("binancecoin", {}).get("usd", 600)),
                    }
                    _price_cache_ts = now
                    logger.info(
                        "[prices] SOL=$%.2f ETH=$%.2f BNB=$%.2f",
                        _price_cache["solana"],
                        _price_cache["ethereum"],
                        _price_cache["binancecoin"],
                    )
                    return _price_cache
                else:
                    logger.warning("[prices] CoinGecko returned %s", resp.status)
    except Exception as e:
        logger.warning("[prices] CoinGecko error: %s", e)

    # Return last cache or hardcoded fallback
    if _price_cache:
        return _price_cache
    return {"solana": 150.0, "ethereum": 3000.0, "binancecoin": 600.0}


async def usd_to_native(usd_amount: float, network: str) -> tuple[float, str]:
    """
    Convert a USD amount to the native token amount for a given network.
    Returns (native_amount, native_symbol).
    """
    prices = await get_native_prices()
    cg_id = COINGECKO_IDS.get(network, "solana")
    native_price = prices.get(cg_id, 150.0)
    native_amount = usd_amount / native_price if native_price > 0 else 0
    native_symbol = NATIVE_SYMBOLS.get(network, "SOL")
    return native_amount, native_symbol
