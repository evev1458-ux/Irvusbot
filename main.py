async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    user_text = update.message.text.lower().strip()
    
    # Botun ismi geçerse veya bota cevap verilirse tetiklenir
    is_reply = update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id
    if "irvus" in user_text or is_reply:
        # "Yazıyor..." efekti vererek botun düşündüğünü hissettirelim
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # 1. VERİSEL SORGU (Sadece Rakamlar İçin)
        if any(x in user_text for x in ["bitcoin", "btc", "fiyat"]):
            try:
                res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5).json()
                price = float(res['price'])
                return await update.message.reply_text(f"📊 **BTC:** `${price:,.0f}`. Irvus ile piyasayı anlık izliyorum! 🚀")
            except: pass

        # 2. GERÇEK YAPAY ZEKA (Her Türlü Soruya Özgün Cevap)
        try:
            # Yapay zekaya karakter yüklüyoruz: Zeki, vizyoner ve Irvus asistanı.
            prompt = (
                f"<|system|>\n"
                f"Sen Irvus Token'ın zeki, vizyoner ve samimi asistanısın. "
                f"Kullanıcının her türlü sorusuna (güncel olaylar, felsefe, şaka, gelecek planları) "
                f"Irvus topluluğuna yakışır şekilde, Türkçe ve kısa cevap ver. "
                f"Hazır kalıplar kullanma, her seferinde farklı ve zekice konuş.</s>\n"
                f"<|user|>\n{update.message.text}</s>\n"
                f"<|assistant|>\n"
            )
            
            res = requests.post(CHAT_MODEL, 
                                headers={"Authorization": f"Bearer {HF_TOKEN}"}, 
                                json={"inputs": prompt, "parameters": {"max_new_tokens": 150, "temperature": 0.8}}, 
                                timeout=15).json()
            
            ans = res[0].get('generated_text', "").split("<|assistant|>")[-1].strip()
            
            if ans:
                return await update.message.reply_text(f"🤖 {ans}")
        except Exception as e:
            print(f"AI Hatası: {e}")
            
        # AI o an cevap vermezse yedek (Irvus ruhunu koru)
        await update.message.reply_text("💎 Irvus burada! Seni duyuyorum dostum, gelecek bizimle başlıyor.")
        
