async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (f"💎 **IRVUS GLOBAL AI & BUY BOT**\n\n"
           f"🇹🇷 AI, Çizim, Fiyat ve Anlık Alımlar Aktif!\n"
           f"🇺🇸 AI, Draw, Price and Live Buys Active!\n\n"
           f"📄 CA: `{CA}`")
    # Buton tanımlaması tam olarak böyle olmalı:
    kb = [
        [InlineKeyboardButton("🌐 Website", url="https://www.irvustoken.xyz")],
        [InlineKeyboardButton("📊 Chart", url=f"https://dexscreener.com/base/{CA}")]
    ]
    reply_markup = InlineKeyboardMarkup(kb)
    await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode='Markdown')

async def draw_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt: return await update.message.reply_text("Ne çizmemi istersiniz?")
    # Önce mesajı gönderelim
    status_msg = await update.message.reply_text("🎨 Görsel oluşturuluyor, lütfen bekleyin...")
    img_url = f"https://pollinations.ai/p/{quote(prompt)}?width=1024&height=1024&seed=99"
    try:
        # Fotoğrafı gönderirken parse_mode kullanmıyoruz
        await update.message.reply_photo(photo=img_url, caption=f"🖼 **Irvus Art:** {prompt}")
        await status_msg.delete() # 'Çiziliyor' yazısını siler
    except:
        await status_msg.edit_text("🎨 Çizim yapılamadı, lütfen sonra tekrar deneyin.")
        
