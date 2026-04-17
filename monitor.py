"""
Buy Monitor — dual-mode detection.

SOLANA MODE  (network == "SOL"):
  Polls getSignaturesForAddress on the pair account every 15s.
  For each new confirmed signature → getTransaction → extract real buyer
  wallet, exact SOL spent, exact tokens received.
  One alert per real on-chain swap. 100% accurate amounts.

EVM MODE  (ETH / BSC / BASE):
  Polls DexScreener txns.m5.buys every 15s.
  Detects count delta → estimates per-buy USD from volume delta.
  Links to DexScreener chart (no individual tx access without API key).
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError, Forbidden, BadRequest, ChatMigrated

from .database import get_all_active_groups
from .dex_tracker import (
    get_token_info, build_buy_alert, format_usd,
    DEXSCREENER_LINKS, TX_EXPLORERS, _esc,
)
from .chain_rpc import (
    get_signatures_for_address, get_transaction,
    extract_swap_data, usd_to_native, get_native_prices,
    NATIVE_SYMBOLS,
)

logger = logging.getLogger(__name__)

POLL_INTERVAL_SOL = 12   # Solana: faster (blocks ~0.4s)
POLL_INTERVAL_EVM = 20   # EVM: slower (DexScreener rate limits)
LOOP_SLEEP = 8


@dataclass
class GroupState:
    group_id: int
    contract: str
    network: str
    # Solana mode
    last_signature: Optional[str] = None
    seen_signatures: set = field(default_factory=set)
    # EVM mode
    last_buys_m5: int = -1
    last_volume_m5: float = 0.0
    # Shared
    pair_address: Optional[str] = None
    token_name: str = ""
    token_symbol: str = ""
    token_price: float = 0.0
    market_cap: float = 0.0
    last_poll_ts: float = 0.0
    consecutive_errors: int = 0


_states: dict[int, GroupState] = {}


def _get_state(group: dict) -> GroupState:
    gid = group["group_id"]
    contract = group.get("contract_address", "")
    network = group.get("network", "")
    if gid not in _states or _states[gid].contract != contract:
        _states[gid] = GroupState(group_id=gid, contract=contract, network=network)
    return _states[gid]


# ─── Alert Sender ─────────────────────────────────────────────────────────────

async def _send_message_with_fallback(bot: Bot, group_id: int, message: str, plain: str):
    """Try MarkdownV2 first; fall back to plain text on parse errors."""
    try:
        await bot.send_message(
            chat_id=group_id,
            text=message,
            parse_mode=ParseMode.MARKDOWN_V2,
            disable_web_page_preview=False,
        )
        return True
    except BadRequest as e:
        logger.warning("[alert] MarkdownV2 parse error for group=%s: %s", group_id, e)
        logger.debug("[alert] Offending message:\n%s", message)
    try:
        await bot.send_message(chat_id=group_id, text=plain)
        return True
    except TelegramError as e:
        logger.error("[alert] Plain fallback also failed group=%s: %s", group_id, e)
        return False


async def send_buy_alert(
    bot: Bot,
    group_id: int,
    config: dict,
    token_info: dict,
    usd_spent: float,
    tokens_received: float,
    *,
    buyer_wallet: str = "",
    txn_signature: str = "",
    native_amount: float = 0.0,
    native_symbol: str = "",
):
    """Format and send a buy alert to the group."""
    min_buy = float(config.get("min_buy_usd") or 0)
    if min_buy > 0 and usd_spent < min_buy:
        logger.info(
            "[alert] SKIP group=%s buy=$%.2f below min=$%.2f",
            group_id, usd_spent, min_buy,
        )
        return

    network = config.get("network", "ETH")
    pair_addr = token_info.get("pair_address", config.get("contract_address", ""))
    chart_url = DEXSCREENER_LINKS.get(network, "").format(pair_addr)

    txn_url = ""
    if txn_signature:
        explorer = TX_EXPLORERS.get(network, "")
        txn_url = explorer.format(txn_signature) if explorer else ""

    message = build_buy_alert(
        token_name=token_info["name"],
        token_symbol=token_info["symbol"],
        usd_spent=usd_spent,
        tokens_received=tokens_received,
        market_cap=token_info["market_cap"],
        network=network,
        chart_url=chart_url,
        config=config,
        native_amount=native_amount,
        native_symbol=native_symbol,
        buyer_wallet=buyer_wallet,
        txn_url=txn_url,
    )

    plain = (
        f"{token_info['name']} (${token_info['symbol']}) Buy!\n\n"
        f"🔄 {native_amount:.4f} {native_symbol} (${usd_spent:,.2f})\n"
        f"🔄 {tokens_received:,.0f} ${token_info['symbol']}\n"
        f"🎖️ Market Cap {format_usd(token_info['market_cap'])}\n"
        f"📊 {chart_url}"
    )
    if buyer_wallet:
        plain += f"\n👤 {buyer_wallet[:4]}...{buyer_wallet[-4:]}"
    if txn_url:
        plain += f" | {txn_url}"

    logger.info(
        "[alert] → group=%s | %s | $%.2f | native=%.4f %s | wallet=%s",
        group_id, token_info["symbol"], usd_spent,
        native_amount, native_symbol,
        buyer_wallet[:8] if buyer_wallet else "n/a",
    )

    media_file_id = config.get("media_file_id")
    media_type = config.get("media_type", "animation")

    try:
        if media_file_id:
            send_fn = bot.send_animation if media_type != "video" else bot.send_video
            kw = "animation" if media_type != "video" else "video"
            await send_fn(**{
                "chat_id": group_id,
                kw: media_file_id,
                "caption": message,
                "parse_mode": ParseMode.MARKDOWN_V2,
            })
        else:
            success = await _send_message_with_fallback(bot, group_id, message, plain)
            if not success:
                return

        logger.info("[alert] SUCCESS → group=%s", group_id)

    except Forbidden as e:
        logger.error("[alert] FORBIDDEN group=%s — bot kicked or no permissions: %s", group_id, e)
    except ChatMigrated as e:
        logger.warning("[alert] Chat migrated group=%s → %s", group_id, e.new_chat_id)
    except TelegramError as e:
        logger.error("[alert] TelegramError group=%s: %s", group_id, e)


# ─── Solana Mode ──────────────────────────────────────────────────────────────

async def _poll_solana(bot: Bot, state: GroupState, config: dict, token_info: dict):
    """
    Detect new buys on Solana by polling getSignaturesForAddress
    on the pair account and processing new transaction signatures.
    """
    pair_address = token_info.get("pair_address")
    if not pair_address:
        logger.warning("[sol] group=%s has no pair_address yet", state.group_id)
        return

    network = state.network
    contract = state.contract

    sigs = await get_signatures_for_address(pair_address, limit=20)
    if not sigs:
        logger.debug("[sol] group=%s — no signatures returned", state.group_id)
        return

    # On first run, just record the latest signature as baseline
    if state.last_signature is None:
        state.last_signature = sigs[0]["signature"]
        state.seen_signatures = {s["signature"] for s in sigs}
        logger.info(
            "[sol] group=%s — baseline set: sig=%s...  (%d recent sigs)",
            state.group_id,
            state.last_signature[:12],
            len(sigs),
        )
        return

    # Find new signatures we haven't processed yet
    new_sigs = [
        s for s in sigs
        if s["signature"] not in state.seen_signatures
        and not s.get("err")  # skip failed txs
    ]

    if not new_sigs:
        logger.debug("[sol] group=%s — no new signatures", state.group_id)
        return

    logger.info("[sol] group=%s — %d new signature(s) to process", state.group_id, len(new_sigs))

    # Update last_signature to newest (but only add to seen AFTER successful fetch)
    state.last_signature = sigs[0]["signature"]
    # Mark ALL sigs from DexScreener-already-seen baseline (older than new_sigs) as seen
    new_sig_set = {s["signature"] for s in new_sigs}
    for s in sigs:
        if s["signature"] not in new_sig_set:
            state.seen_signatures.add(s["signature"])

    # Keep memory bounded
    if len(state.seen_signatures) > 300:
        # Retain the 150 most recently added
        state.seen_signatures = set(list(state.seen_signatures)[-150:])

    # Get native token prices once for this batch
    prices = await get_native_prices()
    sol_price = prices.get("solana", 150.0)

    # Process each new transaction (cap at 2 per poll, spread over time)
    alerts_fired = 0
    for i, sig_info in enumerate(new_sigs[:2]):
        sig = sig_info["signature"]

        # Throttle: stagger RPC calls to avoid rate limits
        if i > 0:
            await asyncio.sleep(1.5)

        try:
            tx = await get_transaction(sig)
            if tx is None:
                # Rate-limited or fetch failed — do NOT mark as seen so next poll retries
                logger.warning("[sol] Could not fetch tx %s — will retry next poll", sig[:12])
                continue

            # Mark as seen only after we have the data
            state.seen_signatures.add(sig)

            swap = extract_swap_data(tx, target_mint=contract)
            if swap is None:
                logger.debug("[sol] tx %s is not a relevant buy", sig[:12])
                continue

            sol_spent = swap["sol_spent"]
            tokens_received = swap["tokens_received"]
            buyer_wallet = swap.get("buyer_wallet", "")
            usd_spent = sol_spent * sol_price

            logger.info(
                "[sol] ✅ BUY tx=%s | wallet=%s | SOL=%.4f ($%.2f) | tokens=%.2f",
                sig[:12], buyer_wallet[:8] if buyer_wallet else "?",
                sol_spent, usd_spent, tokens_received,
            )

            await send_buy_alert(
                bot=bot,
                group_id=state.group_id,
                config=config,
                token_info=token_info,
                usd_spent=usd_spent,
                tokens_received=tokens_received,
                buyer_wallet=buyer_wallet,
                txn_signature=sig,
                native_amount=sol_spent,
                native_symbol="SOL",
            )
            alerts_fired += 1

            # Pace alerts: 1.5s gap between sends
            if alerts_fired < 3:
                await asyncio.sleep(1.5)

        except Exception as e:
            logger.error("[sol] Error processing sig %s: %s", sig[:12], e, exc_info=True)

    if alerts_fired == 0 and new_sigs:
        logger.info(
            "[sol] group=%s — %d new sigs processed, none were confirmed buys",
            state.group_id, len(new_sigs),
        )


# ─── EVM Mode ─────────────────────────────────────────────────────────────────

async def _poll_evm(bot: Bot, state: GroupState, config: dict, token_info: dict):
    """
    Detect new buys on EVM chains via DexScreener buys_m5 count delta.
    """
    curr_buys_m5 = token_info.get("buys_m5", 0)
    curr_volume_m5 = token_info.get("volume_m5", 0.0)
    curr_price = token_info.get("price_usd", 0.0)
    network = state.network

    logger.info(
        "[evm] group=%s | %s | price=$%.8f | mcap=%s | buys_m5=%d | vol_m5=$%.2f | prev=%d",
        state.group_id, token_info["symbol"], curr_price,
        format_usd(token_info.get("market_cap", 0)),
        curr_buys_m5, curr_volume_m5, state.last_buys_m5,
    )

    if state.last_buys_m5 == -1:
        state.last_buys_m5 = curr_buys_m5
        state.last_volume_m5 = curr_volume_m5
        logger.info("[evm] group=%s — baseline set: buys_m5=%d", state.group_id, curr_buys_m5)
        return

    new_buys = curr_buys_m5 - state.last_buys_m5

    if new_buys <= 0:
        if new_buys < 0:
            logger.info("[evm] group=%s — 5m window reset (%d→%d)", state.group_id,
                        state.last_buys_m5, curr_buys_m5)
        state.last_buys_m5 = curr_buys_m5
        state.last_volume_m5 = curr_volume_m5
        return

    vol_delta = max(curr_volume_m5 - state.last_volume_m5, 0)
    per_buy_usd = max(vol_delta / new_buys if new_buys > 0 else vol_delta, 1.0)
    per_buy_tokens = per_buy_usd / curr_price if curr_price > 0 else 0

    logger.info(
        "[evm] group=%s — 🚨 %d new buy(s) | vol_delta=$%.2f | per_buy=$%.2f",
        state.group_id, new_buys, vol_delta, per_buy_usd,
    )

    # Get native token amount
    native_amount, native_symbol = await usd_to_native(per_buy_usd, network)

    alerts_to_fire = min(new_buys, 3)
    for i in range(alerts_to_fire):
        try:
            await send_buy_alert(
                bot=bot,
                group_id=state.group_id,
                config=config,
                token_info=token_info,
                usd_spent=per_buy_usd,
                tokens_received=per_buy_tokens,
                native_amount=native_amount,
                native_symbol=native_symbol,
            )
            if i < alerts_to_fire - 1:
                await asyncio.sleep(1.5)
        except Exception as e:
            logger.error("[evm] Alert error group=%s: %s", state.group_id, e)

    state.last_buys_m5 = curr_buys_m5
    state.last_volume_m5 = curr_volume_m5


# ─── Main Poll Dispatcher ─────────────────────────────────────────────────────

async def poll_group(bot: Bot, state: GroupState, config: dict):
    """One poll cycle for a group — dispatches to Solana or EVM mode."""
    network = state.network
    poll_interval = POLL_INTERVAL_SOL if network == "SOL" else POLL_INTERVAL_EVM

    now = time.time()
    if now - state.last_poll_ts < poll_interval:
        return
    state.last_poll_ts = now

    logger.info(
        "[poll] group=%s | %s...%s | %s",
        state.group_id, state.contract[:6], state.contract[-4:], network,
    )

    try:
        token_info = await get_token_info(state.contract, network)
        if token_info is None:
            state.consecutive_errors += 1
            logger.warning(
                "[poll] group=%s — no token data (errors=%d)",
                state.group_id, state.consecutive_errors,
            )
            return

        state.consecutive_errors = 0
        state.pair_address = token_info.get("pair_address")
        state.token_name = token_info.get("name", "")
        state.token_symbol = token_info.get("symbol", "")
        state.token_price = token_info.get("price_usd", 0)
        state.market_cap = token_info.get("market_cap", 0)

        if network == "SOL":
            await _poll_solana(bot, state, config, token_info)
        else:
            await _poll_evm(bot, state, config, token_info)

    except Exception as e:
        state.consecutive_errors += 1
        logger.error("[poll] group=%s exception: %s", state.group_id, e, exc_info=True)


# ─── Test Alert ───────────────────────────────────────────────────────────────

async def send_test_alert(bot: Bot, group_id: int, config: dict) -> bool:
    """Fire a mock buy alert to verify Telegram connectivity."""
    prices = await get_native_prices()
    network = config.get("network", "SOL")
    native_sym = NATIVE_SYMBOLS.get(network, "SOL")
    native_price = prices.get({"SOL": "solana", "ETH": "ethereum",
                                "BSC": "binancecoin", "BASE": "ethereum"}.get(network, "solana"), 150)

    usd_spent = 500.0
    native_amount = usd_spent / native_price

    mock_token = {
        "name": config.get("token_name") or "TestToken",
        "symbol": config.get("token_symbol") or "TEST",
        "price_usd": 0.00001234,
        "market_cap": 1_500_000,
        "pair_address": config.get("contract_address", "0x0000"),
        "dexscreener_url": "https://dexscreener.com",
    }
    try:
        await send_buy_alert(
            bot=bot,
            group_id=group_id,
            config={**config, "min_buy_usd": 0},
            token_info=mock_token,
            usd_spent=usd_spent,
            tokens_received=40_531_050.0,
            buyer_wallet="Ab3xF7k2Zm9pQ8wR",
            txn_signature="5TestSignatureXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
            native_amount=native_amount,
            native_symbol=native_sym,
        )
        return True
    except Exception as e:
        logger.error("[test] send_test_alert failed: %s", e)
        return False


# ─── Monitor Loop ─────────────────────────────────────────────────────────────

async def monitor_loop(bot: Bot):
    """Main loop — polls all configured groups indefinitely."""
    logger.info("[monitor] Started (SOL interval=%ds, EVM interval=%ds)",
                POLL_INTERVAL_SOL, POLL_INTERVAL_EVM)

    while True:
        try:
            groups = await get_all_active_groups()
            if not groups:
                logger.debug("[monitor] No active groups yet")
            else:
                tasks = [poll_group(bot, _get_state(g), g) for g in groups]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for i, r in enumerate(results):
                    if isinstance(r, Exception):
                        logger.error("[monitor] poll exception group=%s: %s",
                                     groups[i]["group_id"], r)
        except Exception as e:
            logger.error("[monitor] Loop error: %s", e, exc_info=True)

        await asyncio.sleep(LOOP_SLEEP)
