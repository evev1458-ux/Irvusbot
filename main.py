async def draw_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = " ".join(context.args)
    if not p: 
        return await update.message.reply_text("Ne çizelim? Örnek: /ciz uzaylı kedi")
    
    # Bilgi mesajı
    msg = await update.message.reply_text("🎨 Irvus AI görseli hazırlıyor...")
    
    # 1. Her seferinde tamamen benzersiz bir sayı (seed)
    # 2. nologo=true ile logoyu kaldırma
    # 3. Parametrelerin sırasını değiştirerek Telegram'ı kandırma
    random_id = random.randint(1, 999999)
    url = f"https://image.pollinations.ai/prompt/{quote(p)}?seed={random_id}&width=1024&height=1024&nologo=true&no_cache={random_id}"
    
    try:
        # Fotoğrafı gönderirken linkin sonuna anlık zaman ekleyerek cache'i kırıyoruz
        await update.message.reply_photo(
            photo=url, 
            caption=f"🖼 **Irvus Art:** {p}\n🚀 *Model: Irvus-Gen-V1*"
        )
        await msg.delete()
    except Exception as e:
        print(f"Hata: {e}")
        await msg.edit_text("🎨 Görsel oluşturulurken bir teknik sorun oluştu.")
        
