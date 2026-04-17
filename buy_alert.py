def format_number(n: float) -> str:
    """Sayıyı okunabilir formata çevir: 1500000 → 1.5M"""
    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.2f}B"
    elif n >= 1_000_000:
        return f"{n/1_000_000:.2f}M"
    elif n >= 1_000:
        return f"{n/1_000:.2f}K"
    else:
        return f"{n:.2f}"

def format_usd(n: float) -> str:
    """Dolar formatı"""
    if n >= 1_000_000:
        return f"${n/1_000_000:.2f}M"
    elif n >= 1_000:
        return f"${n/1_000:.2f}K"
    else:
        return f"${n:.2f}"

def build_emoji_bar(amount_usd: float, emoji: str = "🟢") -> str:
    """Alım miktarına göre emoji bar oluştur"""
    if amount_usd < 50:
        count = 1
    elif amount_usd < 100:
        count = 3
    elif amount_usd < 500:
        count = 5
    elif amount_usd < 1000:
        count = 8
    elif amount_usd < 5000:
        count = 12
    else:
        count = 15
    return emoji * count

def build_buy_message(buy: dict, cfg: dict) -> tuple:
    """
    Buy alert mesajı oluştur.
    Döndürür: (text, emoji_bar)
    """
    name = buy.get("name", "Token")
    symbol = buy.get("symbol", "???")
    amount_usd = buy.get("amount_usd", 0)
    amount_token = buy.get("amount_token", 0)
    mcap = buy.get("mcap", 0)
    chain = buy.get("chain", "sol").upper()
    ca = buy.get("ca", "")
    tx_hash = buy.get("tx_hash", "")

    emoji = cfg.get("emoji", "🟢")
    tg_link = cfg.get("tg_link")
    web_link = cfg.get("web_link")
    x_link = cfg.get("x_link")

    emoji_bar = build_emoji_bar(amount_usd, emoji)

    # Chain explorer linkleri
    explorer_url = ""
    if chain == "SOL":
        explorer_url = f"https://solscan.io/tx/{tx_hash}"
    elif chain == "ETH":
        explorer_url = f"https://etherscan.io/tx/{tx_hash}"
    elif chain == "BSC":
        explorer_url = f"https://bscscan.com/tx/{tx_hash}"
    elif chain == "BASE":
        explorer_url = f"https://basescan.org/tx/{tx_hash}"

    # Dexscreener linki
    dex_chain_map = {"SOL": "solana", "ETH": "ethereum", "BSC": "bsc", "BASE": "base"}
    dex_chain = dex_chain_map.get(chain, "solana")
    chart_url = f"https://dexscreener.com/{dex_chain}/{ca}"

    text = (
        f"*{name} (${symbol}) Buy!*\n\n"
        f"{emoji_bar}\n\n"
        f"💰 Spent: {format_usd(amount_usd)}\n"
        f"🪙 Got: {format_number(amount_token)} {symbol}\n"
        f"📊 MCAP: {format_usd(mcap)}\n"
        f"⛓ Chain: {chain}\n"
    )

    # Linkler
    links = []
    if explorer_url:
        links.append(f"[🔍 TX]({explorer_url})")
    links.append(f"[📈 Chart]({chart_url})")
    if tg_link:
        links.append(f"[💬 TG]({tg_link})")
    if web_link:
        links.append(f"[🌐 Web]({web_link})")
    if x_link:
        links.append(f"[✖️ X]({x_link})")

    if links:
        text += "\n" + " | ".join(links)

    return text, emoji_bar
    
