import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode

from ..database import (
    get_setup_state, set_setup_state, clear_setup_state,
    set_group_config, get_group_config, add_tracked_token
)
from ..dex_tracker import validate_contract, NETWORK_DISPLAY

logger = logging.getLogger(__name__)

NETWORKS = ["ETH", "SOL", "BSC", "BASE"]


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if the user is a group admin."""
    user = update.effective_user
    chat = update.effective_chat
    
    if chat.type == "private":
        return True
    
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ("administrator", "creator")
    except Exception:
        return False


async def setup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /setup command."""
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Only group admins can use /setup.")
        return
    
    chat = update.effective_chat
    if chat.type == "private":
        await update.message.reply_text("❌ /setup must be used in a group.")
        return
    
    keyboard = [
        [
            InlineKeyboardButton("⟠ ETH", callback_data="setup_network_ETH"),
            InlineKeyboardButton("◎ SOL", callback_data="setup_network_SOL"),
        ],
        [
            InlineKeyboardButton("⬡ BSC", callback_data="setup_network_BSC"),
            InlineKeyboardButton("🔵 BASE", callback_data="setup_network_BASE"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔧 *Buy Bot Setup*\n\nSelect the blockchain network to monitor:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup,
    )


async def handle_network_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle network selection callback."""
    query = update.callback_query
    await query.answer()
    
    if not await is_admin(update, context):
        await query.answer("❌ Only admins can configure this bot.", show_alert=True)
        return
    
    network = query.data.split("_")[-1]
    group_id = update.effective_chat.id
    
    await set_setup_state(group_id, step="awaiting_ca", network=network)
    
    network_name = NETWORK_DISPLAY.get(network, network)
    await query.edit_message_text(
        f"✅ Network selected: *{network_name}*\n\n"
        f"Now send me the *Contract Address (CA)* to monitor:",
        parse_mode=ParseMode.MARKDOWN,
    )


async def handle_contract_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle contract address input during setup."""
    chat = update.effective_chat
    if chat.type == "private":
        return
    
    group_id = chat.id
    state = await get_setup_state(group_id)
    
    if not state or state.get("step") != "awaiting_ca":
        return
    
    if not await is_admin(update, context):
        return
    
    ca = update.message.text.strip()
    network = state.get("network")
    
    status_msg = await update.message.reply_text(
        f"🔍 Validating contract address on {NETWORK_DISPLAY.get(network, network)}..."
    )
    
    token_info = await validate_contract(ca, network)
    
    if not token_info:
        await status_msg.edit_text(
            f"❌ *Invalid contract address* or token not found on {NETWORK_DISPLAY.get(network, network)}.\n\n"
            f"Please double-check the address and try /setup again.",
            parse_mode=ParseMode.MARKDOWN,
        )
        await clear_setup_state(group_id)
        return
    
    # Save config
    await set_group_config(
        group_id,
        network=network,
        contract_address=ca,
        token_name=token_info["name"],
        token_symbol=token_info["symbol"],
        active=1,
    )
    await add_tracked_token(
        group_id, ca, network, token_info["name"], token_info["symbol"]
    )
    await clear_setup_state(group_id)
    
    mcap = token_info.get("market_cap", 0)
    price = token_info.get("price_usd", 0)
    
    from ..dex_tracker import format_number
    
    await status_msg.edit_text(
        f"✅ *Setup Complete!*\n\n"
        f"🪙 *Token:* {token_info['name']} (${token_info['symbol']})\n"
        f"⛓️ *Network:* {NETWORK_DISPLAY.get(network, network)}\n"
        f"💵 *Price:* ${price:.8f}\n"
        f"📊 *MCAP:* {format_number(mcap)}\n\n"
        f"The bot will now monitor buys in real-time\\! Use /settings to customize the alerts\\.",
        parse_mode=ParseMode.MARKDOWN_V2,
    )


def get_setup_handlers():
    return [
        CommandHandler("setup", setup_command),
        CallbackQueryHandler(handle_network_selection, pattern="^setup_network_"),
    ]
