"""
Unified message router to avoid handler conflicts.
Routes group text messages to the correct handler based on bot state.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from ..database import get_setup_state, get_media_awaiting, get_group_config
from ..dex_tracker import validate_contract, NETWORK_DISPLAY
from ..database import (
    set_group_config, clear_setup_state, add_tracked_token,
    set_media_awaiting, clear_media_awaiting
)

logger = logging.getLogger(__name__)


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    chat = update.effective_chat
    if chat.type == "private":
        return True
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ("administrator", "creator")
    except Exception:
        return False


async def route_group_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route group text messages to appropriate handler."""
    chat = update.effective_chat
    group_id = chat.id

    # 1. Check if we're awaiting a settings text input
    awaiting = context.user_data.get("awaiting_input")
    if awaiting and await is_admin(update, context):
        field, target_group_id = awaiting
        if target_group_id == group_id:
            await handle_settings_input(update, context, field, group_id)
            return

    # 2. Check if we're in setup flow (awaiting CA)
    state = await get_setup_state(group_id)
    if state and state.get("step") == "awaiting_ca" and await is_admin(update, context):
        await handle_ca_input(update, context, state)
        return

    # 3. Check bot mention for AI chat
    message = update.message
    if message and message.text:
        bot_username = context.bot.username
        if f"@{bot_username}" in message.text:
            from .ai_commands import handle_bot_mention
            await handle_bot_mention(update, context)
            return


async def handle_ca_input(update: Update, context: ContextTypes.DEFAULT_TYPE, state: dict):
    """Handle contract address input during /setup."""
    from ..dex_tracker import format_number
    
    group_id = update.effective_chat.id
    ca = update.message.text.strip()
    network = state.get("network")

    status_msg = await update.message.reply_text(
        f"🔍 Validating contract on {NETWORK_DISPLAY.get(network, network)}..."
    )

    token_info = await validate_contract(ca, network)

    if not token_info:
        await status_msg.edit_text(
            f"❌ *Invalid contract address* or token not found on "
            f"{NETWORK_DISPLAY.get(network, network)}.\n\n"
            f"Please double-check and try /setup again.",
            parse_mode="Markdown",
        )
        await clear_setup_state(group_id)
        return

    await set_group_config(
        group_id,
        network=network,
        contract_address=ca,
        token_name=token_info["name"],
        token_symbol=token_info["symbol"],
        active=1,
    )
    await add_tracked_token(group_id, ca, network, token_info["name"], token_info["symbol"])
    await clear_setup_state(group_id)

    mcap = token_info.get("market_cap", 0)
    price = token_info.get("price_usd", 0)

    escaped_note = "The bot will now monitor buys in real\\-time\\! Use /settings to customize alerts\\."
    await status_msg.edit_text(
        f"✅ *Setup Complete\\!*\n\n"
        f"🪙 *Token:* {token_info['name']} \\(${token_info['symbol']}\\)\n"
        f"⛓️ *Network:* {NETWORK_DISPLAY.get(network, network)}\n"
        f"💵 *Price:* ${price:.8f}\n"
        f"📊 *MCAP:* {format_number(mcap)}\n\n"
        f"{escaped_note}",
        parse_mode="MarkdownV2",
    )


async def handle_settings_input(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                 field: str, group_id: int):
    """Handle text input for settings fields."""
    text = update.message.text.strip()
    context.user_data.pop("awaiting_input", None)

    if field == "tg_link":
        await set_group_config(group_id, telegram_link=text)
        await update.message.reply_text(f"✅ Telegram link updated.")

    elif field == "web_link":
        await set_group_config(group_id, website_link=text)
        await update.message.reply_text(f"✅ Website link updated.")

    elif field == "x_link":
        await set_group_config(group_id, x_link=text)
        await update.message.reply_text(f"✅ X/Twitter link updated.")

    elif field == "emoji":
        await set_group_config(group_id, custom_emoji=text)
        await update.message.reply_text(f"✅ Buy emoji updated to: {text}")

    elif field == "min_buy":
        try:
            amount = float(text.replace("$", "").replace(",", ""))
            await set_group_config(group_id, min_buy_usd=amount)
            await update.message.reply_text(f"✅ Minimum buy set to: ${amount:.2f}")
        except ValueError:
            await update.message.reply_text("❌ Invalid amount. Please send a number like `100`.")

    elif field == "add_token":
        config = await get_group_config(group_id)
        network = config.get("network", "ETH") if config else "ETH"
        status_msg = await update.message.reply_text("🔍 Validating contract...")
        token_info = await validate_contract(text, network)
        if token_info:
            await add_tracked_token(
                group_id, text, network,
                token_info["name"], token_info["symbol"]
            )
            await status_msg.edit_text(
                f"✅ Added *{token_info['name']}* (${token_info['symbol']}) to tracked tokens.",
                parse_mode="Markdown",
            )
        else:
            await status_msg.edit_text("❌ Token not found. Please check the contract address.")


async def route_media_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle GIF/video uploads for buy alert media."""
    chat = update.effective_chat
    if chat.type == "private":
        return

    group_id = chat.id
    awaiting = await get_media_awaiting(group_id)

    if not awaiting:
        return

    if not await is_admin(update, context):
        return

    message = update.message
    file_id = None
    media_type = None

    if message.animation:
        file_id = message.animation.file_id
        media_type = "animation"
    elif message.video:
        file_id = message.video.file_id
        media_type = "video"
    elif message.document and message.document.mime_type in ("image/gif", "video/mp4"):
        file_id = message.document.file_id
        media_type = "animation"

    if not file_id:
        return

    await set_group_config(group_id, media_file_id=file_id, media_type=media_type)
    await clear_media_awaiting(group_id)

    await message.reply_text(
        "✅ *Buy alert media saved!*\n\n"
        "This GIF/video will now appear at the top of every buy alert.",
        parse_mode="Markdown",
    )


def get_router_handlers():
    return [
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            route_group_text,
        ),
        MessageHandler(
            (filters.ANIMATION | filters.VIDEO | filters.Document.GIF) & filters.ChatType.GROUPS,
            route_media_upload,
        ),
    ]
