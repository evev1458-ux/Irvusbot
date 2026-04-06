async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    user_text = update.message.text.lower().strip()
    is_reply = update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id
    
    # Botun ismi geçerse veya birisi bota cevap verirse zeka tetiklenir
    if "irvus" in user_text or is_reply:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # SADECE VERİSEL SORGULAR (Burası rakam olduğu için AI uydurmasın diye sabit)
        if any(x in user_text for x in ["bitcoin", "btc", "fiyat"]):
            try:
                res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT").json()
                return await update.message.reply_text(f"📊 **BTC:** `${float(res['price']):,.0f}`. Irvus ile piyasayı takipteyiz! 🚀")
            except: pass

        # DİĞER HER ŞEY İÇİN GERÇEK YAPAY ZEKA (Zephyr)
        try:
            # Yapay zekaya botun karakterini ve Irvus Token asistanı olduğunu öğretiyoruz
            prompt = (
                f"<|system|>\n"
                f"Sen Irvus Token'ın zeki, vizyoner ve samimi asistanısın. "
                f"Kullanıcının her türlü sorusuna (güncel olaylar, felsefe, teknoloji, şaka) "
                f"Irvus topluluğuna yakışır şekilde, Türkçe ve kısa cevap ver. "
                f"Asla 'hazır mesaj' kullanma, her seferinde özgün ol.</s>\n"
                f"<|user|>\n{update.message.text}</s>\n"
                f"<|assistant|>\n"
            )
            
            res = requests.post(CHAT_MODEL, 
                                headers={"Authorization": f"Bearer {HF_TOKEN}"}, 
                                json={"inputs": prompt, "parameters": {"max_new_tokens": 150, "temperature": 0.7}}, 
                                timeout=15).json()
            
            # AI'dan gelen cevabı temizleyip kullanıcıya sunuyoruz
            ans = res[0].get('generated_text', "").split("<|assistant|>")[-1].strip()
            
            if ans:
                return await update.message.reply_text(f"🤖 {ans}")
        except Exception as e:
            print(f"AI Hatası: {e}")
            
        # Eğer AI sistemi o an çökerse veya cevap vermezse (Son Sığınak)
        await update.message.reply_text("💎 Irvus burada! Seni dinliyorum ama şu an sistemlerimi optimize ediyorum. Ne sormuştun?")
        
