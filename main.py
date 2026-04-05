async def fiyat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Linki 'pairs' olarak güncelledik (DexScreener için en garanti yol budur)
        url = f"https://api.dexscreener.com/latest/dex/pairs/base/{TOKEN_ADRESI}"
        r = requests.get(url, timeout=15).json()
        
        if 'pair' in r:
            p = r['pair']
        elif 'pairs' in r and len(r['pairs']) > 0:
            p = r['pairs'][0]
        else:
            return await update.message.reply_text("❌ Token verisi bulunamadı. CA kontrol et.")

        fiyat_usd = p.get('priceUsd', '0')
        degisim = p.get('priceChange', {}).get('h24', '0')
        grafik = p.get('url', '')

        msg = (f"💎 **Irvus Token ($IRVUS)**\n"
               f"━━━━━━━━━━━━━━━━━━\n"
               f"💰 Fiyat: `${fiyat_usd}`\n"
               f"📈 24s Değişim: `%{degisim}`\n"
               f"━━━━━━━━━━━━━━━━━━")
        
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📊 DexScreener Grafiği", url=grafik)]])
        await update.message.reply_text(msg, reply_markup=kb, parse_mode='Markdown')
        
    except Exception as e:
        print(f"Fiyat Hatası: {e}")
        await update.message.reply_text("⚠️ Fiyat şu an çekilemedi, lütfen 10 saniye sonra tekrar dene.")
        
