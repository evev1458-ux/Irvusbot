from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def fiyat_gonder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await get_dex_price()
    if data:
        price = data.get("priceUsd", "0")
        change = data.get("priceChange", {}).get("h24", "0")
        dex_url = data.get("url")
        
        text = (
            f"💎 **Irvus Token ($IRVUS)**\n\n"
            f"💵 **Fiyat:** `${float(price):.8f}`\n"
            f"📈 **24s Değişim:** %{change}\n"
        )
        
        # Buton Oluşturma
        keyboard = [[InlineKeyboardButton("📊 DexScreener Grafiği", url=dex_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # disable_web_page_preview=True o büyük resmi kapatır
        await update.message.reply_text(
            text, 
            parse_mode="Markdown", 
            reply_markup=reply_markup,
            disable_web_page_preview=True 
        )
    else:
        await update.message.reply_text("❌ Fiyat verisi şu an çekilemiyor.")
        
