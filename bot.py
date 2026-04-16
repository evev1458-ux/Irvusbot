import os
import asyncio
import logging
import aiohttp
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from database import Database
from chain_monitor import ChainMonitor
from buy_alert import BuyAlert

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = Database()
buy_alert_handler = BuyAlert()

# ─────────────────────────────────────────────
# /start
# ─────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🦊 *IRVUS Buy Bot'a Hoş Geldiniz!*\n\n"
        "📋 *Komutlar:*\n"
        "⚙️ /settings — Grup ayarları\n"
        "🔧 /setup — Token kurulumu\n"
        "🎨 /draw <prompt> — AI görsel oluştur\n"
        "🤖 /sor <soru> — Yapay zekaya sor\n"
        "📊 /status — Bot durumu\n"
        "❓ /help — Yardım"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ─────────────────────────────────────────────
# /help
# ─────────────────────────────────────────────
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🆘 *Yardım Menüsü*\n\n"
        "*/setup* — Token ekle (ağ seç → CA gir)\n"
        "*/settings* — Grup ayarlarını düzenle\n"
        "  • Telegram / Web / X linkleri\n"
        "  • Özel emoji\n"
        "  • Min alım miktarı\n"
        "  • GIF/Video yükle\n"
        "*/draw <metin>* — AI ile görsel üret (ücretsiz)\n"
        "*/sor <soru>* — Yapay zeka ile sohbet et (ücretsiz)\n"
        "*/status* — Aktif token & zincir bilgisi\n\n"
        "💡 Her grup *ayrı* ayarlarla çalışır.\n"
        "💡 CA'yı gruba atınca bot otomatik algılar."
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ─────────────────────────────────────────────
# /status
# ─────────────────────────────────────────────
async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cfg = db.get_group_config(chat_id)
    tokens = db.get_tokens(chat_id)

    if not tokens:
        await update.message.reply_text("⚠️ Henüz token eklenmedi. /setup ile ekleyin.")
        return

    lines = ["📊 *Grup Durumu*\n"]
    for t in tokens:
        lines.append(f"• `{t['ca']}` — {t['chain'].upper()}")
    lines.append(f"\n{cfg.get('emoji','🟢')} Emoji: {cfg.get('emoji','🟢')}")
    lines.append(f"💰 Min Alım: ${cfg.get('min_buy', 0)}")
    lines.append(f"🎬 Medya: {'✅ Yüklendi' if cfg.get('media_file_id') else '❌ Yok'}")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

# ─────────────────────────────────────────────
# /sor — Yapay Zeka (Groq, tamamen ücretsiz)
# ─────────────────────────────────────────────
async def sor_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "🤖 Kullanım: /sor <sorunuzu yazın>\n\n"
            "Örnek: /sor Bitcoin ne zaman 100k olur?\n"
            "Örnek: /sor IRVUS token nedir?"
        )
        return

    soru = " ".join(context.args)
    msg = await update.message.reply_text("🤖 Düşünüyorum...")

    groq_api_key = os.getenv("GROQ_API_KEY", "")
    if not groq_api_key:
        await msg.edit_text(
            "❌ GROQ_API_KEY eksik!\n"
            "https://console.groq.com adresinden ücretsiz API key alın\n"
            "ve .env dosyasına ekleyin."
        )
        return

    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": "llama3-8b-8192",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Sen IRVUS Token topluluğunun yapay zeka asistanısın. "
                            "Kripto para, DeFi, Solana, Ethereum, BSC, token analizi konularında uzmansın. "
                            "Her zaman Türkçe yanıt ver. Kısa, net ve faydalı ol. "
                            "Emoji kullan. Yatırım tavsiyesi verme, sadece bilgi ver."
                        )
                    },
                    {"role": "user", "content": soru}
                ],
                "max_tokens": 1024,
                "temperature": 0.7
            }
            headers = {
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json"
            }
            async with session.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    yanit = data["choices"][0]["message"]["content"]
                    await msg.edit_text(
                        f"🤖 *Yapay Zeka:*\n\n{yanit}",
                        parse_mode="Markdown"
                    )
                else:
                    error_text = await resp.text()
                    logger.error(f"Groq API hatası {resp.status}: {error_text}")
                    await msg.edit_text("❌ AI yanıt vermedi. Biraz sonra tekrar dene.")
    except asyncio.TimeoutError:
        await msg.edit_text("⏰ Zaman aşımı. Tekrar dene.")
    except Exception as e:
        logger.error(f"sor_cmd hatası: {e}")
        await msg.edit_text("❌ Bir hata oluştu. Tekrar dene.")

# ─────────────────────────────────────────────
# /draw — AI Görsel (Pollinations, tamamen ücretsiz)
# ─────────────────────────────────────────────
async def draw_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "🎨 Kullanım: /draw <görsel açıklaması>\n\n"
            "Örnek: /draw a cool fox riding a rocket in space, neon colors\n"
            "Örnek: /draw irvus token logo, fox with sunglasses"
        )
        return

    prompt = " ".join(context.args)
    msg = await update.message.reply_text("🎨 Görsel oluşturuluyor... (15-30 saniye)")

    try:
        import urllib.parse
        encoded = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&nologo=true&seed={hash(prompt) % 99999}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    img_data = await resp.read()
                    await msg.delete()
                    await update.message.reply_photo(
                        photo=img_data,
                        caption=f"🎨 *AI Görsel*\n📝 _{prompt}_",
                        parse_mode="Markdown"
                    )
                else:
                    await msg.edit_text("❌ Görsel oluşturulamadı. Tekrar dene.")
    except asyncio.TimeoutError:
        await msg.edit_text("⏰ Zaman aşımı. Tekrar dene.")
    except Exception as e:
        logger.error(f"draw_cmd hatası: {e}")
        await msg.edit_text("❌ Bir hata oluştu. Tekrar dene.")

# ─────────────────────────────────────────────
# /setup — Token Kurulumu
# ─────────────────────────────────────────────
async def setup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("⟠ Ethereum (ETH)", callback_data="setup_chain_eth"),
            InlineKeyboardButton("◎ Solana (SOL)", callback_data="setup_chain_sol"),
        ],
        [
            InlineKeyboardButton("🟡 BSC (BNB)", callback_data="setup_chain_bsc"),
            InlineKeyboardButton("🔵 Base", callback_data="setup_chain_base"),
        ]
    ]
    await update.message.reply_text(
        "🔧 *Token Kurulumu*\n\nHangi ağa kurmak istiyorsunuz?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ─────────────────────────────────────────────
# /settings — Grup Ayarları
# ─────────────────────────────────────────────
async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cfg = db.get_group_config(chat_id)
    tokens = db.get_tokens(chat_id)

    text = (
        f"⚙️ *Settings for this group*\n\n"
        f"📱 Telegram: {cfg.get('tg_link','Not set')}\n"
        f"🌐 Website: {cfg.get('web_link','Not set')}\n"
        f"✖️ X: {cfg.get('x_link','Not set')}\n"
        f"😀 Emoji: {cfg.get('emoji','🟢')}\n"
        f"💰 Min Buy: ${cfg.get('min_buy',0)}\n"
        f"🎬 Media: {'✅ Uploaded' if cfg.get('media_file_id') else '❌ Not set'}\n"
        f"🪙 Tokens tracked: {len(tokens) if tokens else 0}\n\n"
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
            InlineKeyboardButton("➕ Add Token", callback_data="add_token"),
            InlineKeyboardButton("🗑️ Remove Token", callback_data="remove_token"),
        ]
    ]
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ─────────────────────────────────────────────
# Callback Handler
# ─────────────────────────────────────────────
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    data = query.data

    chain_names = {"eth": "Ethereum", "sol": "Solana", "bsc": "BSC", "base": "Base"}

    if data.startswith("setup_chain_") or data.startswith("addtoken_"):
        chain = data.split("_")[-1]
        context.user_data["pending_chain"] = chain
        context.user_data["pending_chat_id"] = chat_id
        await query.edit_message_text(
            f"✅ *{chain_names.get(chain, chain)}* seçildi!\n\n"
            f"Şimdi token contract adresini (CA) bu gruba yazın.\n"
            f"Bot otomatik algılayacak. 🚀",
            parse_mode="Markdown"
        )

    elif data == "set_tg":
        context.user_data[f"awaiting_{chat_id}"] = "tg_link"
        await query.edit_message_text("📱 Telegram grup/kanal linkini yazın:\nÖrnek: https://t.me/grupadi")

    elif data == "set_web":
        context.user_data[f"awaiting_{chat_id}"] = "web_link"
        await query.edit_message_text("🌐 Website linkini yazın:\nÖrnek: https://irvustoken.com")

    elif data == "set_x":
        context.user_data[f"awaiting_{chat_id}"] = "x_link"
        await query.edit_message_text("✖️ X linkini yazın:\nÖrnek: https://x.com/irvustoken")

    elif data == "set_emoji":
        context.user_data[f"awaiting_{chat_id}"] = "emoji"
        await query.edit_message_text("😀 Alım bildirimlerinde gösterilecek emojiyi gönderin:\nÖrnek: 🚀 🦊 💎 🌙")

    elif data == "set_minbuy":
        context.user_data[f"awaiting_{chat_id}"] = "min_buy"
        await query.edit_message_text("💰 Minimum alım $ miktarını yazın:\nÖrnek: 10\n(0 = hepsini göster)")

    elif data == "set_media":
        cfg = db.get_group_config(chat_id)
        cfg["awaiting_media"] = True
        db.save_group_config(chat_id, cfg)
        await query.edit_message_text("🎬 GIF veya Video gönderin.\nAlım bildirimlerinin başında gösterilecek.")

    elif data == "add_token":
        keyboard = [
            [
                InlineKeyboardButton("⟠ ETH", callback_data="addtoken_eth"),
                InlineKeyboardButton("◎ SOL", callback_data="addtoken_sol"),
            ],
            [
                InlineKeyboardButton("🟡 BSC", callback_data="addtoken_bsc"),
                InlineKeyboardButton("🔵 Base", callback_data="addtoken_base"),
            ]
        ]
        await query.edit_message_text(
            "➕ *Token Ekle* — Hangi ağ?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif data == "remove_token":
        tokens = db.get_tokens(chat_id)
        if not tokens:
            await query.edit_message_text("❌ Silinecek token yok.")
            return
        buttons = []
        for t in tokens:
            short = t['ca'][:8] + "..." + t['ca'][-4:]
            buttons.append([InlineKeyboardButton(
                f"🗑️ {short} ({t['chain'].upper()})",
                callback_data=f"deltoken_{t['ca']}"
            )])
        await query.edit_message_text("🗑️ Silmek istediğiniz token:", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("deltoken_"):
        ca = data.replace("deltoken_", "")
        db.remove_token(chat_id, ca)
        await query.edit_message_text(f"✅ Token silindi: `{ca}`", parse_mode="Markdown")

    elif data.startswith("autoaddtoken_"):
        parts = data.split("_", 3)
        chain = parts[2]
        ca = parts[3]
        db.add_token(chat_id, ca, chain)
        await query.edit_message_text(
            f"✅ Token eklendi!\n🪙 `{ca}`\n🌐 {chain.upper()}\n\nAlımlar izleniyor 🚀",
            parse_mode="Markdown"
        )

# ─────────────────────────────────────────────
# Media Handler
# ─────────────────────────────────────────────
async def media_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cfg = db.get_group_config(chat_id)

    if not cfg.get("awaiting_media"):
        return

    file_id = None
    media_type = None
    if update.message.animation:
        file_id = update.message.animation.file_id
        media_type = "gif"
    elif update.message.video:
        file_id = update.message.video.file_id
        media_type = "video"

    if file_id:
        cfg["media_file_id"] = file_id
        cfg["media_type"] = media_type
        cfg.pop("awaiting_media", None)
        db.save_group_config(chat_id, cfg)
        await update.message.reply_text("✅ Medya kaydedildi! Alım bildirimlerinde gösterilecek. 🎬")

# ─────────────────────────────────────────────
# Text Message Handler
# ─────────────────────────────────────────────
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat_id = update.effective_chat.id
    text = update.message.text.strip()

    # Ayar inputu bekleniyor mu?
    awaiting_key = f"awaiting_{chat_id}"
    if awaiting_key in context.user_data:
        field = context.user_data.pop(awaiting_key)
        cfg = db.get_group_config(chat_id)

        if field == "min_buy":
            try:
                val = float(text)
                cfg["min_buy"] = val
                db.save_group_config(chat_id, cfg)
                await update.message.reply_text(f"✅ Min alım ${val} olarak ayarlandı.")
            except ValueError:
                await update.message.reply_text("❌ Geçerli bir sayı girin. Örnek: 10")
        else:
            cfg[field] = text
            db.save_group_config(chat_id, cfg)
            labels = {"tg_link": "Telegram linki", "web_link": "Website", "x_link": "X linki", "emoji": "Emoji"}
            await update.message.reply_text(f"✅ {labels.get(field, field)} kaydedildi!")
        return

    # CA bekleniyor mu? (setup/addtoken sonrası)
    pending_chain = context.user_data.get("pending_chain")
    pending_chat = context.user_data.get("pending_chat_id")

    if pending_chain and pending_chat == chat_id:
        if is_valid_ca(text, pending_chain):
            db.add_token(chat_id, text, pending_chain)
            context.user_data.pop("pending_chain", None)
            context.user_data.pop("pending_chat_id", None)
            await update.message.reply_text(
                f"✅ *Token eklendi!*\n\n"
                f"🪙 CA: `{text}`\n"
                f"🌐 Zincir: {pending_chain.upper()}\n\n"
                f"Alımlar izleniyor 🚀",
                parse_mode="Markdown"
            )
            return

    # Otomatik CA algılama
    for word in text.split():
        for chain in ["eth", "bsc", "base", "sol"]:
            if is_valid_ca(word, chain):
                tokens = db.get_tokens(chat_id)
                if not any(t['ca'].lower() == word.lower() for t in tokens):
                    keyboard = [[
                        InlineKeyboardButton(
                            f"✅ {chain.upper()} olarak ekle",
                            callback_data=f"autoaddtoken_x_{chain}_{word}"
                        )
                    ]]
                    await update.message.reply_text(
                        f"🔍 *CA tespit edildi!*\n`{word}`\n\nBu token'ı eklemek ister misiniz?",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode="Markdown"
                    )
                return

def is_valid_ca(ca: str, chain: str) -> bool:
    ca = ca.strip()
    if chain in ("eth", "bsc", "base"):
        return bool(re.match(r'^0x[0-9a-fA-F]{40}$', ca))
    elif chain == "sol":
        return bool(re.match(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$', ca))
    return False

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("❌ TELEGRAM_BOT_TOKEN bulunamadı! .env dosyasını kontrol edin.")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("sor", sor_cmd))
    app.add_handler(CommandHandler("draw", draw_cmd))
    app.add_handler(CommandHandler("setup", setup_cmd))
    app.add_handler(CommandHandler("settings", settings_cmd))

    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.ANIMATION | filters.VIDEO, media_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    monitor = ChainMonitor(db, app.bot, buy_alert_handler)
    asyncio.create_task(monitor.start_monitoring())

    logger.info("🦊 IRVUS Buy Bot başlatıldı!")
    await app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
