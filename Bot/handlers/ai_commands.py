import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from telegram.constants import ParseMode

from ..ai_features import chat_completion, generate_image, get_chat_history, update_chat_history

logger = logging.getLogger(__name__)


async def draw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /draw command for image generation."""
    if not context.args:
        await update.message.reply_text(
            "🎨 *Usage:* `/draw <description>`\n\n"
            "*Example:* `/draw a golden dragon on a mountain at sunset`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    prompt = " ".join(context.args)
    status_msg = await update.message.reply_text(
        f"🎨 Generating: _{prompt}_...",
        parse_mode=ParseMode.MARKDOWN,
    )

    image_url = await generate_image(prompt)

    if image_url:
        await status_msg.delete()
        await update.message.reply_photo(
            photo=image_url,
            caption=f"🎨 *{prompt}*",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        await status_msg.edit_text(
            "❌ Failed to generate image. Please try again later."
        )


async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ask command for AI chat."""
    if not context.args:
        await update.message.reply_text(
            "💬 *Usage:* `/ask <question>`\n\n"
            "*Example:* `/ask What is DeFi?`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    question = " ".join(context.args)
    chat_id = update.effective_chat.id
    history = get_chat_history(chat_id)
    typing_msg = await update.message.reply_text("💭 Thinking...")

    response = await chat_completion(question, history)
    update_chat_history(chat_id, question, response)
    await typing_msg.edit_text(response)


async def handle_bot_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages where the bot is mentioned (called from router)."""
    message = update.message
    if not message or not message.text:
        return

    bot_username = context.bot.username
    question = message.text.replace(f"@{bot_username}", "").strip()

    if not question:
        await message.reply_text(
            f"Hey! Ask me something — mention me with a question:\n"
            f"@{bot_username} What is liquidity?"
        )
        return

    chat_id = update.effective_chat.id
    history = get_chat_history(chat_id)
    response = await chat_completion(question, history)
    update_chat_history(chat_id, question, response)
    await message.reply_text(response)


async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /price command."""
    from ..database import get_group_config
    from ..dex_tracker import get_token_info, format_number, NETWORK_DISPLAY

    chat = update.effective_chat
    if chat.type == "private":
        await update.message.reply_text("Use this command in a group where the bot is set up.")
        return

    config = await get_group_config(chat.id)
    if not config or not config.get("contract_address"):
        await update.message.reply_text("❌ Bot not configured. Use /setup first.")
        return

    status_msg = await update.message.reply_text("📊 Fetching price data...")
    token_info = await get_token_info(config["contract_address"], config["network"])

    if not token_info:
        await status_msg.edit_text("❌ Could not fetch token data. Try again later.")
        return

    price = token_info.get("price_usd", 0)
    mcap = token_info.get("market_cap", 0)
    volume_h24 = token_info.get("volume_h24", 0)
    volume_m5 = token_info.get("volume_m5", 0)
    buys_m5 = token_info.get("buys_m5", 0)
    sells_m5 = token_info.get("sells_m5", 0)
    change = token_info.get("price_change_h24", 0)
    liquidity = token_info.get("liquidity_usd", 0)

    change_emoji = "🟢" if change >= 0 else "🔴"
    change_str = f"{'+' if change >= 0 else ''}{change:.2f}%"

    await status_msg.edit_text(
        f"📊 *{token_info['name']}* (${token_info['symbol']})\n"
        f"{'─' * 28}\n\n"
        f"💵 *Price:* ${price:.10f}\n"
        f"{change_emoji} *24h Change:* {change_str}\n"
        f"📈 *Market Cap:* {format_number(mcap)}\n"
        f"💧 *Liquidity:* {format_number(liquidity)}\n"
        f"📦 *24h Volume:* {format_number(volume_h24)}\n"
        f"⚡ *5m Volume:* {format_number(volume_m5)}\n"
        f"🟢 *5m Buys:* {buys_m5}  🔴 *5m Sells:* {sells_m5}\n"
        f"⛓️ *Network:* {NETWORK_DISPLAY.get(config['network'], config['network'])}\n\n"
        f"🔗 [View Chart]({token_info.get('dexscreener_url', '#')})",
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )


async def testbuy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /testbuy — Admin command. Fires a mock buy alert immediately to verify
    Telegram sending is working correctly. Bypasses all thresholds.
    """
    from ..database import get_group_config
    from ..monitor import send_test_alert

    chat = update.effective_chat
    if chat.type == "private":
        await update.message.reply_text("Use /testbuy inside the configured group.")
        return

    # Admin check
    try:
        member = await context.bot.get_chat_member(chat.id, update.effective_user.id)
        if member.status not in ("administrator", "creator"):
            await update.message.reply_text("❌ Only admins can use /testbuy.")
            return
    except Exception:
        return

    config = await get_group_config(chat.id)
    if not config:
        await update.message.reply_text("❌ Bot not configured. Run /setup first.")
        return

    status_msg = await update.message.reply_text("🧪 Sending test buy alert...")

    success = await send_test_alert(context.bot, chat.id, config)

    if success:
        await status_msg.edit_text(
            "✅ *Test alert sent!*\n\n"
            "If you see a buy alert above, Telegram sending works correctly.\n"
            "The bot will now post real alerts whenever buys are detected.",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        await status_msg.edit_text(
            "❌ *Test alert failed.*\n\n"
            "Check the bot console logs for the specific Telegram error.\n"
            "Common causes: bot not admin, missing send_messages permission.",
            parse_mode=ParseMode.MARKDOWN,
        )


async def diag_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /diag — Show current monitor state for this group.
    Admin only. Useful for debugging without reading logs.
    """
    from ..database import get_group_config
    from ..dex_tracker import get_token_info, format_number, NETWORK_DISPLAY
    from ..monitor import _states

    chat = update.effective_chat
    if chat.type == "private":
        await update.message.reply_text("Use /diag inside the configured group.")
        return

    try:
        member = await context.bot.get_chat_member(chat.id, update.effective_user.id)
        if member.status not in ("administrator", "creator"):
            await update.message.reply_text("❌ Only admins can use /diag.")
            return
    except Exception:
        return

    config = await get_group_config(chat.id)
    if not config:
        await update.message.reply_text("❌ Not configured. Run /setup first.")
        return

    status_msg = await update.message.reply_text("🔍 Running diagnostics...")

    # Live API check
    token_info = await get_token_info(config["contract_address"], config["network"])

    state = _states.get(chat.id)

    lines = ["🔬 *Diagnostics Report*\n"]

    # Config
    lines.append("*Configuration:*")
    lines.append(f"  Network: {NETWORK_DISPLAY.get(config['network'], config['network'])}")
    short = config['contract_address']
    lines.append(f"  Contract: `{short[:8]}...{short[-6:]}`")
    lines.append(f"  Min Buy: ${float(config.get('min_buy_usd') or 0):.0f}")
    lines.append(f"  Media: {'✅ Set' if config.get('media_file_id') else '❌ None'}\n")

    # Live data
    lines.append("*Live API Data:*")
    if token_info:
        lines.append(f"  ✅ DexScreener: OK")
        lines.append(f"  Token: {token_info['name']} (${token_info['symbol']})")
        lines.append(f"  Price: ${token_info['price_usd']:.10f}")
        lines.append(f"  MCAP: {format_number(token_info['market_cap'])}")
        lines.append(f"  5m Buys: {token_info['buys_m5']}  5m Sells: {token_info['sells_m5']}")
        lines.append(f"  5m Volume: {format_number(token_info['volume_m5'])}\n")
    else:
        lines.append("  ❌ DexScreener: FAILED (no data returned)\n")

    # Monitor state
    lines.append("*Monitor State:*")
    if state:
        import time
        ago = int(time.time() - state.last_poll_ts) if state.last_poll_ts else -1
        network = config.get("network", "?")
        lines.append(f"  Mode: {'Solana RPC' if network == 'SOL' else 'EVM (DexScreener)'}")
        lines.append(f"  Last poll: {ago}s ago")
        if network == "SOL":
            sig = state.last_signature
            lines.append(f"  Last sig: `{sig[:12] + '...' if sig else 'none'}`")
            lines.append(f"  Seen sigs: {len(state.seen_signatures)}")
        else:
            lines.append(f"  Baseline buys_m5: {state.last_buys_m5}")
            lines.append(f"  Baseline vol_m5: ${state.last_volume_m5:.2f}")
        lines.append(f"  Consecutive errors: {state.consecutive_errors}")
    else:
        lines.append("  ⚠️ Not yet polled (bot may have just started)")

    lines.append("\n_Run /testbuy to test Telegram sending._")

    await status_msg.edit_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_username = context.bot.username
    await update.message.reply_text(
        "🤖 *Buy Bot — Commands*\n"
        "─────────────────────────\n\n"
        "🔧 *Admin Commands:*\n"
        "/setup — Configure the bot for your group\n"
        "/settings — Open the settings dashboard\n"
        "/testbuy — Fire a test buy alert right now\n"
        "/diag — Show diagnostics & monitor state\n\n"
        "📊 *Token Commands:*\n"
        "/price — Current price, MCAP, 5m buys/sells\n\n"
        "🤖 *AI Commands:*\n"
        "/ask [question] — Ask the AI assistant\n"
        "/draw [prompt] — Generate an AI image\n\n"
        "💬 *AI Chat:*\n"
        f"Mention @{bot_username} with any question!\n\n"
        "─────────────────────────\n"
        "Supports: ETH \\| SOL \\| BSC \\| Base\n"
        "_Powered by DexScreener \\+ OpenAI_",
        parse_mode=ParseMode.MARKDOWN,
    )


def get_ai_handlers():
    return [
        CommandHandler("draw", draw_command),
        CommandHandler("ask", ask_command),
        CommandHandler("price", price_command),
        CommandHandler("testbuy", testbuy_command),
        CommandHandler("diag", diag_command),
        CommandHandler("help", help_command),
        CommandHandler("start", help_command),
    ]
