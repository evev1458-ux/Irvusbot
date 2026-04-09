async def ask_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query: return
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # Yeni ve sorunsuz AI modeli (Llama-3 kullanıyoruz)
    url = f"https://text.pollinations.ai/{quote(query)}?model=llama&system={quote('You are Irvus AI. Expert in crypto and friendly.')}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=20) as r:
                ans = await r.text()
                # Eğer Pollinations uyarı verirse temizle
                if "IMPORTANT NOTICE" in ans:
                    ans = "🤖 Irvus AI is updating... Please try again in a moment."
                await update.message.reply_text(f"🤖 **Irvus AI:**\n\n{ans}")
    except:
        await update.message.reply_text("⚠️ AI Connection Error.")

async def draw_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = " ".join(context.args)
    if not p: return await update.message.reply_text("Ne çizelim?")
    
    status_msg = await update.message.reply_text("🎨 Görsel oluşturuluyor...")
    
    # Rastgele seed ve nologo ile Telegram önizleme sorununu çözüyoruz
    seed = random.randint(1, 999999)
    img_url = f"https://pollinations.ai/p/{quote(p)}?width=1024&height=1024&seed={seed}&nologo=true"
    
    try:
        await update.message.reply_photo(photo=img_url, caption=f"🖼 **Art:** {p}")
        await status_msg.delete()
    except:
        await status_msg.edit_text("🎨 Görsel hazırlanamadı.")
        
