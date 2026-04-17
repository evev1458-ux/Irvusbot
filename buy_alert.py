def build_buy_message(buy, cfg):
    bar = cfg.get("emoji", "🟢") * 10
    text = (f"*{buy['name']} Buy!*\n{bar}\n\n"
            f"💰 Spent: ${buy['amount_usd']:,.2f}\n"
            f"📊 MCAP: ${buy['mcap']:,.0f}\n"
            f"⛓ Chain: {buy['chain'].upper()}\n"
            f"[🔍 TX](https://dexscreener.com/{buy['chain']}/{buy['ca']})")
    return text, ""
    
