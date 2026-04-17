import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from database import db
from ai_handler import ask_ai, draw_image

logger = logging.getLogger(__name__)
user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🦊 *Irvus Buy Bot Hazır!*\n/setup ile başlayın.", parse_mode="Markdown")

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cfg = db.get_group_config(chat_id)
    tokens = db.get_tokens(chat_id)
    text = f"📊 *Durum*\nEmoji: {cfg.get('emoji')}\nMin Buy: ${cfg.get('min_buy')}\n\nTokenlar:\n"
    for t in tokens: text += f"• `{t['ca']}` ({t['chain'].upper()})\n"
    await update.message.reply_text(text or "Token yok.", parse_mode="Markdown")

async def setup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("Solana", callback_data="setup_sol"), InlineKeyboardButton("Base", callback_data="setup_base")]]
    await update.message.reply_text("Ağ seçin:", reply_markup=InlineKeyboardMarkup(kb))

async def sor_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    ans = await ask_ai(" ".join(context.args))
    await update.message.reply_text(f"🤖 {ans}")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    if query.data.startswith("setup_"):
        user_states[query.from_user.id] = {"action": "ca", "chain": query.data.split("_")[1], "chat_id": query.message.chat_id}
        await query.edit_message_text("CA gönderin:")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in user_states and user_states[uid]["action"] == "ca":
        db.add_token(user_states[uid]["chat_id"], update.message.text.strip(), user_states[uid]["chain"])
        await update.message.reply_text("✅ Kaydedildi."); del user_states[uid]

def register_handlers(app: Application):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("setup", setup_cmd))
    app.add_handler(CommandHandler("sor", sor_cmd))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
