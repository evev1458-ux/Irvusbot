import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler
from telegram.constants import ParseMode

from ..database import (
    get_group_config, set_group_config, set_media_awaiting,
    get_tracked_tokens, remove_tracked_token
)
from ..dex_tracker import NETWORK_DISPLAY

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


def build_settings_keyboard(config: dict) -> InlineKeyboardMarkup:
    min_buy = config.get("min_buy_usd", 0) or 0
    emoji = config.get("custom_emoji", "🟢")
    media_set = "✅" if config.get("media_file_id") else "➕"

    keyboard = [
        [
            InlineKeyboardButton("📢 Telegram Link", callback_data="settings_tg_link"),
            InlineKeyboardButton("🌐 Website Link", callback_data="settings_web_link"),
        ],
        [
            InlineKeyboardButton("🐦 X/Twitter Link", callback_data="settings_x_link"),
            InlineKeyboardButton(f"Emoji: {emoji}", callback_data="settings_emoji"),
        ],
        [
            InlineKeyboardButton(f"💵 Min Buy: ${min_buy:.0f}", callback_data="settings_min_buy"),
            InlineKeyboardButton(f"{media_set} Media", callback_data="settings_media"),
        ],
        [
            InlineKeyboardButton("➕ Add Token", callback_data="settings_add_token"),
            InlineKeyboardButton("➖ Remove Token", callback_data="settings_remove_token"),
        ],
        [
            InlineKeyboardButton("📋 View Tokens", callback_data="settings_view_tokens"),
            InlineKeyboardButton("🔄 Refresh", callback_data="settings_refresh"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_settings_text(config: dict) -> str:
    network = config.get("network", "Not set")
    token_name = config.get("token_name", "Not set")
    token_symbol = config.get("token_symbol", "")
    contract = config.get("contract_address", "Not set")
    min_buy = config.get("min_buy_usd", 0) or 0
    tg_link = config.get("telegram_link") or "Not set"
    web_link = config.get("website_link") or "Not set"
    x_link = config.get("x_link") or "Not set"
    emoji = config.get("custom_emoji", "🟢")
    media = "✅ Custom media set" if config.get("media_file_id") else "❌ No custom media"

    short_contract = f"{contract[:6]}...{contract[-4:]}" if contract and len(contract) > 10 else contract

    return (
        f"⚙️ *Bot Settings Dashboard*\n"
        f"{'─' * 30}\n\n"
        f"🪙 *Token:* {token_name} {f'(${token_symbol})' if token_symbol else ''}\n"
        f"⛓️ *Network:* {NETWORK_DISPLAY.get(network, network)}\n"
        f"📍 *Contract:* `{short_contract}`\n\n"
        f"{'─' * 30}\n\n"
        f"💵 *Min Buy Alert:* ${min_buy:.0f}\n"
        f"🎯 *Buy Emoji:* {emoji}\n"
        f"🎬 *Media:* {media}\n\n"
        f"{'─' * 30}\n\n"
        f"🔗 *Links:*\n"
        f"   • Telegram: {tg_link}\n"
        f"   • Website: {web_link}\n"
        f"   • X/Twitter: {x_link}\n\n"
        f"_Use the buttons below to configure:_"
    )


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Only group admins can use /settings.")
        return

    chat = update.effective_chat
    if chat.type == "private":
        await update.message.reply_text("❌ /settings must be used in a group.")
        return

    config = await get_group_config(chat.id)
    if not config:
        await update.message.reply_text(
            "❌ Bot not configured yet. Use /setup to get started."
        )
        return

    await update.message.reply_text(
        build_settings_text(config),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_settings_keyboard(config),
    )


async def handle_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not await is_admin(update, context):
        await query.answer("❌ Only admins can change settings.", show_alert=True)
        return

    data = query.data
    group_id = update.effective_chat.id

    if data == "settings_refresh":
        config = await get_group_config(group_id)
        if config:
            await query.edit_message_text(
                build_settings_text(config),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=build_settings_keyboard(config),
            )
        return

    if data == "settings_tg_link":
        context.user_data["awaiting_input"] = ("tg_link", group_id)
        await query.edit_message_text(
            "📢 Send the *Telegram group/channel link* (e.g. https://t.me/yourgroup):",
            parse_mode=ParseMode.MARKDOWN,
        )

    elif data == "settings_web_link":
        context.user_data["awaiting_input"] = ("web_link", group_id)
        await query.edit_message_text(
            "🌐 Send the *Website URL* (e.g. https://yourtoken.com):",
            parse_mode=ParseMode.MARKDOWN,
        )

    elif data == "settings_x_link":
        context.user_data["awaiting_input"] = ("x_link", group_id)
        await query.edit_message_text(
            "🐦 Send the *X/Twitter URL* (e.g. https://x.com/yourtoken):",
            parse_mode=ParseMode.MARKDOWN,
        )

    elif data == "settings_emoji":
        context.user_data["awaiting_input"] = ("emoji", group_id)
        await query.edit_message_text(
            "🎯 Send a *single emoji* to use as the buy indicator (default: 🟢):",
            parse_mode=ParseMode.MARKDOWN,
        )

    elif data == "settings_min_buy":
        context.user_data["awaiting_input"] = ("min_buy", group_id)
        await query.edit_message_text(
            "💵 Send the *minimum buy amount in USD* to trigger alerts (e.g. `100`):\n\n"
            "_Set to 0 to alert on all buys._",
            parse_mode=ParseMode.MARKDOWN,
        )

    elif data == "settings_media":
        await set_media_awaiting(group_id, update.effective_user.id)
        await query.edit_message_text(
            "🎬 *Upload Custom Buy Media*\n\n"
            "Send a *GIF or video* in the next message and it will be used as the "
            "visual for all buy alerts in this group.\n\n"
            "_Tip: Animated GIFs work best for buy bots!_",
            parse_mode=ParseMode.MARKDOWN,
        )

    elif data == "settings_add_token":
        context.user_data["awaiting_input"] = ("add_token", group_id)
        config = await get_group_config(group_id)
        network = config.get("network", "ETH") if config else "ETH"
        await query.edit_message_text(
            f"➕ Send the *contract address* to add "
            f"(monitored on {NETWORK_DISPLAY.get(network, network)}):",
            parse_mode=ParseMode.MARKDOWN,
        )

    elif data == "settings_remove_token":
        tokens = await get_tracked_tokens(group_id)
        if not tokens:
            await query.answer("No tokens to remove.", show_alert=True)
            return
        keyboard = [
            [InlineKeyboardButton(
                f"{t['token_name']} ({t['network']})",
                callback_data=f"remove_token_{t['contract_address'][:20]}"
            )]
            for t in tokens
        ]
        keyboard.append([InlineKeyboardButton("↩ Back", callback_data="settings_refresh")])
        await query.edit_message_text(
            "➖ Select a token to *remove*:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif data == "settings_view_tokens":
        tokens = await get_tracked_tokens(group_id)
        if not tokens:
            await query.answer("No tokens tracked.", show_alert=True)
            return
        lines = ["📋 *Tracked Tokens:*\n"]
        for t in tokens:
            lines.append(
                f"• {t['token_name']} (${t['token_symbol']}) "
                f"— {NETWORK_DISPLAY.get(t['network'], t['network'])}\n"
                f"  `{t['contract_address'][:20]}...`"
            )
        await query.edit_message_text(
            "\n".join(lines),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("↩ Back", callback_data="settings_refresh")
            ]]),
        )

    elif data.startswith("remove_token_"):
        partial = data.replace("remove_token_", "")
        tokens = await get_tracked_tokens(group_id)
        match = next((t for t in tokens if t["contract_address"].startswith(partial)), None)
        if match:
            await remove_tracked_token(group_id, match["contract_address"])
            await query.answer(f"Removed {match['token_name']}", show_alert=False)
        config = await get_group_config(group_id)
        if config:
            await query.edit_message_text(
                build_settings_text(config),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=build_settings_keyboard(config),
            )


def get_settings_handlers():
    return [
        CommandHandler("settings", settings_command),
        CallbackQueryHandler(handle_settings_callback, pattern="^settings_|^remove_token_"),
    ]
