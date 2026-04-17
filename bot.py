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

# Loglama ayarı
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = Database()

# Geçici durum takibi (setup ve ayarlar için)
user_states = {}

# --- YARDIMCI FONKSİYONLAR ---
async def check_admin(update: Update):
    """Kullanıcının admin olup olmadığını kontrol eder."""
    if update.effective_chat.type == "private":
        return True
    member = await update.effective_chat.get_member(update.effective_user.id)
    return member.status in ["administrator", "creator"]

# --- KOMUT HANDLERLARI ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🦊 *Hopterix Buy Bot Hazır!*\n\n"
        "Grup alımlarını takip etmek ve yapay zeka özelliklerini kullanmak için komutları inceleyin.\n\n"
        "🔧 /setup — Token takibi başlat\n"
        "⚙️ /settings — Grup ve bildirim ayarları\n"
        "📊 /status — Güncel durum ve ekli tokenlar\n"
        "🤖 /sor <soru> — Yapay zekaya danış\n"
        "🎨 /draw <metin> — AI ile görsel oluştur"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🆘 *Yardım Menüsü*\n\n"
        "*/setup* : Önce ağ seçin, sonra token adresini (CA) gönderin.\n"
        "*/settings* : Emoji, minimum alım ve medya (GIF/Video) ayarları.\n"
        "*/status* : İzlenen tokenları ve aktif ayarları gösterir.\n"
        "*/sor* : Irvus AI asistanına soru sorar.\n"
        "*/draw* : Yazdığınız metni görsele dönüştürür."
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cfg = db.get_group_config(chat_id)
    tokens = db.get_tokens(chat_id)

    lines = [f"📊 *Grup Durumu (ID: {chat_id})*\n"]
    if tokens:
        for t in tokens:
            lines.append(f"• `{t['ca']}` — {t['chain'].upper()}")
    else:
        lines.append("⚠️ İzlenen token yok — /setup ile ekleyin")

    lines.append(f"\n{cfg.get('emoji','🟢')} Emoji: {cfg.get('emoji','🟢')}")
    lines.append(f"💰 Min Alım: ${cfg.get('min_buy', 0)}")
    lines.append(f"🎬 Medya: {'✅ Yüklendi' if cfg.get('media_file_id') else '❌ Yok'}")
    
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def sor_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🤖 Kullanım: `/sor Solana nedir?`", parse_mode="Markdown")
        return
    
    soru = " ".join(context.args)
    msg = await update.message.reply_text("🤖 Düşünüyorum...")
    cevap = await ask_ai(soru)
    await msg.edit_text(f"🤖 *Yapay Zeka Cevabı:*\n\n{cevap}", parse_mode="Markdown")

async def draw_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🎨 Kullanım: `/draw uzayda koşan bir tilki`", parse_mode="Markdown")
        return

    prompt = " ".join(context.args)
    msg = await update.message.reply_text("🎨 Görsel hazırlanıyor...")
    image_url = await draw_image(prompt)
    
    if image_url:
        await update.message.reply_photo(photo=image_url, caption=f"🎨 *{prompt}*", parse_mode="Markdown")
        await msg.delete()
    else:
        await msg.edit_text("❌ Görsel oluşturulamadı.")

async def setup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update): return
    
    keyboard = [
        [InlineKeyboardButton("⚡ Solana", callback_data="setup_sol"), InlineKeyboardButton("🔷 Ethereum", callback_data="setup_eth")],
        [InlineKeyboardButton("🟡 BSC", callback_data="setup_bsc"), InlineKeyboardButton("🔵 Base", callback_data="setup_base")]
    ]
    await update.message.reply_text("🔧 *Token Kurulumu*\nLütfen ağ seçin:", 
                                  reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update): return
    
    keyboard = [
        [InlineKeyboardButton("😀 Emoji Değiştir", callback_data="set_emoji"), InlineKeyboardButton("💰 Min Alım ($)", callback_data="set_minbuy")],
        [InlineKeyboardButton("🎬 Medya (GIF/Video) Ekle", callback_data="set_media")],
        [InlineKeyboardButton("🗑️ Token Sil", callback_data="set_removetoken")]
    ]
    await update.message.reply_text("⚙️ *Grup Ayarları*\nDüzenlemek istediğiniz alanı seçin:", 
                                  reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# --- CALLBACK VE MESAJ YÖNETİMİ ---

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    data = query.data

    if data.startswith("setup_"):
        chain = data.replace("setup_", "")
        user_states[user_id] = {"action": "awaiting_ca", "chain": chain, "chat_id": chat_id}
        await query.edit_message_text(f"✅ *{chain.upper()}* seçildi. Şimdi token adresini (CA) gönderin:")

    elif data == "set_emoji":
        user_states[user_id] = {"action": "set_emoji", "chat_id": chat_id}
        await query.edit_message_text("😀 Kullanmak istediğiniz emojiyi gönderin (Örn: 🔥):")

    elif data == "set_minbuy":
        user_states[user_id] = {"action": "set_minbuy", "chat_id": chat_id}
        await query.edit_message_text("💰 Minimum alım miktarını sayı olarak gönderin (Örn: 50):")

    elif data == "set_media":
        user_states[user_id] = {"action": "set_media", "chat_id": chat_id}
        await query.edit_message_text("🎬 Bildirimlerde görünecek GIF veya Videoyu buraya gönderin:")

    elif data == "set_removetoken":
        tokens = db.get_tokens(chat_id)
        if not tokens:
            await query.edit_message_text("⚠️ Silinecek token bulunamadı.")
            return
        keyboard = [[InlineKeyboardButton(f"🗑️ {t['chain'].upper()}: {t['ca'][:6]}...", callback_data=f"rm_{t['ca']}")] for t in tokens]
        await query.edit_message_text("Silmek istediğiniz tokenı seçin:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("rm_"):
        ca = data.replace("rm_", "")
        db.remove_token(chat_id, ca)
        await query.edit_message_text(f"✅ Token silindi: `{ca}`", parse_mode="Markdown")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_states: return

    state = user_states[user_id]
    chat_id = state["chat_id"]
    action = state["action"]

    if action == "awaiting_ca":
        ca = update.message.text.strip()
        if len(ca) < 20:
            await update.message.reply_text("❌ Geçersiz CA adresi.")
            return
        db.add_token(chat_id, ca, state["chain"])
        await update.message.reply_text(f"✅ Token eklendi: `{ca}`", parse_mode="Markdown")

    elif action == "set_emoji":
        db.set_group_config(chat_id, "emoji", update.message.text.strip())
        await update.message.reply_text("✅ Emoji güncellendi.")

    elif action == "set_minbuy":
        try:
            val = float(update.message.text.strip())
            db.set_group_config(chat_id, "min_buy", val)
            await update.message.reply_text(f"✅ Min alım ${val} olarak ayarlandı.")
        except:
            await update.message.reply_text("❌ Geçersiz sayı.")

    elif action == "set_media":
        msg = update.message
        f_id, m_type = None, None
        if msg.animation: f_id, m_type = msg.animation.file_id, "animation"
        elif msg.video: f_id, m_type = msg.video.file_id, "video"
        elif msg.photo: f_id, m_type = msg.photo[-1].file_id, "photo"
        
        if f_id:
            db.set_group_config(chat_id, "media_file_id", f_id)
            db.set_group_config(chat_id, "media_type", m_type)
            await update.message.reply_text(f"✅ Medya kaydedildi ({m_type}).")
    
    del user_states[user_id]

# --- KAYIT FONKSİYONU ---
def register_handlers(app: Application):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("sor", sor_cmd))
    app.add_handler(CommandHandler("draw", draw_cmd))
    app.add_handler(CommandHandler("setup", setup_cmd))
    app.add_handler(CommandHandler("settings", settings_cmd))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND | filters.ANIMATION | filters.VIDEO | filters.PHOTO, message_handler))
    
