import os
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from database import Database
from ai_handler import ask_ai, draw_image

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = Database()

# Geçici state (setup akışı için)
user_states = {}

# ─── /start ───────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🦊 *IRVUS Buy Bot'a Hoş Geldiniz!*\n\n"
        "📋 *Komutlar:*\n"
        "🔧 /setup — Token kur\n"
        "⚙️ /settings — Grup ayarları\n"
        "📊 /status — Bot durumu\n"
        "🤖 /sor <soru> — Yapay zekaya sor\n"
        "🎨 /draw <prompt> — AI görsel üret\n"
        "❓ /help — Yardım"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ─── /help ────────────────────────────────────────────────────────────────────
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🆘 *Yardım Menüsü*\n\n"
        "*/setup* — Token ekle: ağ seç → CA gir\n"
        "*/settings* — Grup ayarları:\n"
        "  • Telegram / Web / X linkleri\n"
        "  • Özel emoji\n"
        "  • Min alım miktarı ($)\n"
        "  • GIF/Video yükle\n"
        "*/sor <soru>* — Yapay zekaya sor\n"
        "  Örnek: `/sor Bitcoin nedir?`\n"
        "*/draw <metin>* — AI görsel üret\n"
        "  Örnek: `/draw uzayda uçan tilki`\n"
        "*/status* — Token & ayar bilgisi\n\n"
        "💡 Her grup ayrı ayarlarla çalışır."
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ─── /status ──────────────────────────────────────────────────────────────────
async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cfg = db.get_group_config(chat_id)
    tokens = db.get_tokens(chat_id)

    lines = [f"📊 *Grup Durumu*\n"]
    if tokens:
        for t in tokens:
            lines.append(f"• `{t['ca']}` — {t['chain'].upper()}")
    else:
        lines.append("⚠️ Token yok — /setup ile ekleyin")

    lines.append(f"\n{cfg.get('emoji','🟢')} Emoji: {cfg.get('emoji','🟢')}")
    lines.append(f"💰 Min Alım: ${cfg.get('min_buy', 0)}")
    lines.append(f"🎬 Medya: {'✅ Yüklendi' if cfg.get('media_file_id') else '❌ Yok'}")
    lines.append(f"💬 Telegram: {cfg.get('tg_link') or 'Ayarlanmadı'}")
    lines.append(f"🌐 Website: {cfg.get('web_link') or 'Ayarlanmadı'}")
    lines.append(f"✖️ X: {cfg.get('x_link') or 'Ayarlanmadı'}")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

# ─── /sor ─────────────────────────────────────────────────────────────────────
async def sor_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "🤖 *Yapay Zeka*\n\nKullanım: `/sor <sorunuzu yazın>`\n\n"
            "Örnek: `/sor Solana nedir?`",
            parse_mode="Markdown"
        )
        return

    soru = " ".join(context.args)
    msg = await update.message.reply_text("🤖 Düşünüyorum...")

    try:
        cevap = await ask_ai(soru)
        await msg.edit_text(
            f"🤖 *Yapay Zeka Cevabı:*\n\n{cevap}",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"AI error: {e}")
        await msg.edit_text("❌ Yapay zeka şu an yanıt veremiyor.")

# ─── /draw ────────────────────────────────────────────────────────────────────
async def draw_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "🎨 *AI Görsel Üret*\n\nKullanım: `/draw <ne çizmek istiyorsunuz>`\n\n"
            "Örnek: `/draw uzayda uçan tilki`",
            parse_mode="Markdown"
        )
        return

    prompt = " ".join(context.args)
    msg = await update.message.reply_text("🎨 Görsel oluşturuluyor...")

    try:
        image_url = await draw_image(prompt)
        if image_url:
            await update.message.reply_photo(
                photo=image_url,
                caption=f"🎨 *{prompt}*",
                parse_mode="Markdown"
            )
            await msg.delete()
        else:
            await msg.edit_text("❌ Görsel oluşturulamadı, tekrar deneyin.")
    except Exception as e:
        logger.error(f"Draw error: {e}")
        await msg.edit_text("❌ Görsel servisi çalışmıyor.")

# ─── /setup ───────────────────────────────────────────────────────────────────
async def setup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("⚡ Solana", callback_data="setup_sol"),
            InlineKeyboardButton("🔷 Ethereum", callback_data="setup_eth"),
        ],
        [
            InlineKeyboardButton("🟡 BSC", callback_data="setup_bsc"),
            InlineKeyboardButton("🔵 Base", callback_data="setup_base"),
        ]
    ]
    await update.message.reply_text(
        "🔧 *Token Kurulumu*\n\nHangi ağa kurmak istiyorsunuz?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ─── /settings ────────────────────────────────────────────────────────────────
async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cfg = db.get_group_config(chat_id)
    tokens = db.get_tokens(chat_id)

    text = (
        f"⚙️ *Settings for this group*\n\n"
        f"📱 Telegram: {cfg.get('tg_link') or 'Not set'}\n"
        f"🌐 Website: {cfg.get('web_link') or 'Not set'}\n"
        f"✖️ X: {cfg.get('x_link') or 'Not set'}\n"
        f"😀 Emoji: {cfg.get('emoji', '🟢')}\n"
        f"💰 Min Buy: ${cfg.get('min_buy', 0)}\n"
        f"🎬 Media: {'✅ Uploaded' if cfg.get('media_file_id') else '❌ Not set'}\n"
        f"🔗 Tokens tracked: {len(tokens)}\n\n"
        f"Select an option to configure:"
    )

    keyboard = [
        [
            InlineKeyboardButton("📱 Telegram Link", callback_data="set_tg"),
            InlineKeyboardButton("🌐 Website Link", callback_data="set_web"),
        ],
        [
            InlineKeyboardButton("✖️ X Link", callback_data="set_x"),
            InlineKeyboardButton("😀 Custom Emoji", callback_data="set_emoji"),
        ],
        [
            InlineKeyboardButton("💰 Min Buy ($)", callback_data="set_minbuy"),
            InlineKeyboardButton("🎬 Add Media", callback_data="set_media"),
        ],
        [
            InlineKeyboardButton("➕ Add Token", callback_data="set_addtoken"),
            InlineKeyboardButton("🗑️ Remove Token", callback_data="set_removetoken"),
        ],
    ]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ─── Callback handler ─────────────────────────────────────────────────────────
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_id = query.from_user.id
    data = query.data

    # ── Setup: zincir seç ──
    if data.startswith("setup_") and data in ["setup_sol", "setup_eth", "setup_bsc", "setup_base"]:
        chain = data.replace("setup_", "")
        user_states[user_id] = {"action": "awaiting_ca", "chain": chain}
        chain_names = {"sol": "Solana", "eth": "Ethereum", "bsc": "BSC", "base": "Base"}
        await query.edit_message_text(
            f"✅ *{chain_names[chain]}* seçildi.\n\n"
            f"Şimdi token contract adresini (CA) gönderin:",
            parse_mode="Markdown"
        )

    # ── Settings: link/emoji/minbuy ayarla ──
    elif data == "set_tg":
        user_states[user_id] = {"action": "set_tg", "chat_id": chat_id}
        await query.edit_message_text("📱 Telegram grup linkini gönderin:\nÖrnek: https://t.me/grupadi")

    elif data == "set_web":
        user_states[user_id] = {"action": "set_web", "chat_id": chat_id}
        await query.edit_message_text("🌐 Website linkini gönderin:\nÖrnek: https://siteniz.com")

    elif data == "set_x":
        user_states[user_id] = {"action": "set_x", "chat_id": chat_id}
        await query.edit_message_text("✖️ X (Twitter) linkini gönderin:\nÖrnek: https://x.com/hesabiniz")

    elif data == "set_emoji":
        user_states[user_id] = {"action": "set_emoji", "chat_id": chat_id}
        await query.edit_message_text("😀 Kullanmak istediğiniz emojiyi gönderin:\nÖrnek: 🚀 veya 💎")

    elif data == "set_minbuy":
        user_states[user_id] = {"action": "set_minbuy", "chat_id": chat_id}
        await query.edit_message_text("💰 Minimum alım miktarını $ olarak gönderin:\nÖrnek: 50")

    elif data == "set_media":
        user_states[user_id] = {"action": "set_media", "chat_id": chat_id}
        await query.edit_message_text(
            "🎬 GIF, video veya fotoğraf gönderin.\n"
            "Bu medya her alım bildiriminin üstünde görünecek."
        )

    elif data == "set_addtoken":
        keyboard = [
            [
                InlineKeyboardButton("⚡ Solana", callback_data="setup_sol"),
                InlineKeyboardButton("🔷 Ethereum", callback_data="setup_eth"),
            ],
            [
                InlineKeyboardButton("🟡 BSC", callback_data="setup_bsc"),
                InlineKeyboardButton("🔵 Base", callback_data="setup_base"),
            ]
        ]
        await query.edit_message_text(
            "➕ *Token Ekle*\n\nHangi ağa eklemek istiyorsunuz?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif data == "set_removetoken":
        tokens = db.get_tokens(chat_id)
        if not tokens:
            await query.edit_message_text("⚠️ Silinecek token yok.")
            return
        keyboard = []
        for t in tokens:
            short_ca = t['ca'][:8] + "..."
            keyboard.append([
                InlineKeyboardButton(
                    f"🗑️ {t['chain'].upper()} - {short_ca}",
                    callback_data=f"rmtoken_{t['ca']}"
                )
            ])
        await query.edit_message_text(
            "🗑️ Hangi tokeni silmek istiyorsunuz?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("rmtoken_"):
        ca = data.replace("rmtoken_", "")
        removed = db.remove_token(chat_id, ca)
        if removed:
            await query.edit_message_text(f"✅ Token silindi:\n`{ca}`", parse_mode="Markdown")
        else:
            await query.edit_message_text("❌ Token bulunamadı.")

# ─── Mesaj handler (state akışı) ──────────────────────────────────────────────
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if user_id not in user_states:
        return

    state = user_states[user_id]
    action = state.get("action")

    # CA bekleniyor (setup akışı)
    if action == "awaiting_ca":
        ca = update.message.text.strip()
        chain = state.get("chain")
        target_chat = state.get("chat_id", chat_id)

        if len(ca) < 20:
            await update.message.reply_text("❌ Geçersiz CA. Lütfen doğru contract adresini girin.")
            return

        added = db.add_token(target_chat, ca, chain)
        del user_states[user_id]

        if added:
            await update.message.reply_text(
                f"✅ *Token eklendi!*\n\n"
                f"⛓ Zincir: {chain.upper()}\n"
                f"📋 CA: `{ca}`\n\n"
                f"Alımlar artık bu gruba bildirilecek.",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("⚠️ Bu token zaten ekli.")

    elif action == "set_tg":
        val = update.message.text.strip()
        db.set_group_config(state["chat_id"], "tg_link", val)
        del user_states[user_id]
        await update.message.reply_text(f"✅ Telegram linki ayarlandı: {val}")

    elif action == "set_web":
        val = update.message.text.strip()
        db.set_group_config(state["chat_id"], "web_link", val)
        del user_states[user_id]
        await update.message.reply_text(f"✅ Website linki ayarlandı: {val}")

    elif action == "set_x":
        val = update.message.text.strip()
        db.set_group_config(state["chat_id"], "x_link", val)
        del user_states[user_id]
        await update.message.reply_text(f"✅ X linki ayarlandı: {val}")

    elif action == "set_emoji":
        val = update.message.text.strip()
        db.set_group_config(state["chat_id"], "emoji", val)
        del user_states[user_id]
        await update.message.reply_text(f"✅ Emoji ayarlandı: {val}")

    elif action == "set_minbuy":
        try:
            val = float(update.message.text.strip().replace("$", ""))
            db.set_group_config(state["chat_id"], "min_buy", val)
            del user_states[user_id]
            await update.message.reply_text(f"✅ Minimum alım: ${val}")
        except ValueError:
            await update.message.reply_text("❌ Geçersiz miktar. Sadece sayı girin: örnek 50")

    elif action == "set_media":
        msg = update.message
        file_id = None
        media_type = None

        if msg.animation:
            file_id = msg.animation.file_id
            media_type = "animation"
        elif msg.video:
            file_id = msg.video.file_id
            media_type = "video"
        elif msg.photo:
            file_id = msg.photo[-1].file_id
            media_type = "photo"

        if file_id:
            db.set_group_config(state["chat_id"], "media_file_id", file_id)
            db.set_group_config(state["chat_id"], "media_type", media_type)
            del user_states[user_id]
            await update.message.reply_text(f"✅ Medya yüklendi! ({media_type})")
        else:
            await update.message.reply_text("❌ GIF, video veya fotoğraf gönderin.")


def register_handlers(app: Application):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("sor", sor_cmd))
    app.add_handler(CommandHandler("draw", draw_cmd))
    app.add_handler(CommandHandler("setup", setup_cmd))
    app.add_handler(CommandHandler("settings", settings_cmd))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND | filters.ANIMATION | filters.VIDEO | filters.PHOTO,
        message_handler
    ))
        
