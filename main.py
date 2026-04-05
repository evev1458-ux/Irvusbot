import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Token ve Zincir Bilgileri
IRVUS_CA = "0x31EDA2dfd01c9C65385cCE6099B24b06ef3aE831"
BASE_SCAN_URL = f"https://basescan.org/token/{IRVUS_CA}"

async def get_v4_price():
    # DexScreener v4 dahil tüm Uniswap sürümlerini tarar
    url = f"https://api.dexscreener.com/latest/dex/tokens/{IRVUS_CA}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                json_data = await response.json()
                pairs = json_data.get("pairs", [])
                if not pairs:
                    return None
                
                # En yüksek likiditeye sahip havuzu seç (Genelde en doğru fiyat budur)
                main_pair = max(pairs, key=lambda x: float(x.get("liquidity", {}).get("usd", 0)))
                return main_pair
    return None

async def fiyat_gonder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pair_data = await get_v4_price()
    
    if not pair_data:
        await update.message.reply_text("⚠️ Havuz verisi bulunamadı. Likidite henüz eklenmemiş olabilir.")
        return

    # Verileri ayıklayalım
    price = pair_data.get("priceUsd", "0")
    h24_change = pair_data.get("priceChange", {}).get("h24", "0")
    liquidity = pair_data.get("liquidity", {}).get("usd", 0)
    mcap = pair_data.get("fdv", 0)
    dex_url = pair_data.get("url")

    # Mesaj içeriği
    text = (
        f"🛡 **Irvus Token ($IRVUS) - Base Chain**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💵 **Fiyat:** `${float(price):.10f}`\n"
        f"📊 **24s Değişim:** `%{h24_change}`\n"
        f"💧 **Likidite:** `${int(float(liquidity)):,}`\n"
        f"📈 **Market Cap:** `${int(float(mcap)):,}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🦄 *Uniswap v4/v3 Optimized Data*"
    )

    # Buton ekleyelim (Şık durması için)
    keyboard = [
        [InlineKeyboardButton("📈 Grafiği Aç (DexScreener)", url=dex_url)],
        [InlineKeyboardButton("🔍 BaseScan", url=BASE_SCAN_URL)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    
