import logging
from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


def format_number(num: float) -> str:
    """Sayıyı okunabilir formata çevir: 1500000 → 1.5M, 150000 → 150K"""
    if num >= 1_000_000_000:
        return f"{num/1_000_000_000:.2f}B"
    elif num >= 1_000_000:
        return f"{num/1_000_000:.2f}M"
    elif num >= 1_000:
        return f"{num/1_000:.2f}K"
    else:
        return f"{num:.2f}"


def format_tokens(num: float) -> str:
    """Token miktarını formatla: 1000000 → 1,000,000"""
    if num >= 1_000_000_000:
        return f"{num/1_000_000_000:.2f}B"
    elif num >= 1_000_000:
        return f"{num/1_000_000:.2f}M"
    elif num >= 1_000:
        return f"{num/1_000:.2f}K"
    else:
        return f"{num:,.0f}"


def build_emoji_bar(amount_usd: float, emoji: str = "🟢") -> str:
    """Alım miktarına göre emoji bar oluştur"""
    if amount_usd < 50:
        count = 3
    elif amount_usd < 100:
        count = 5
    elif amount_usd < 500:
        count = 8
    elif amount_usd < 1000:
        count = 10
    elif amount_usd < 5000:
        count = 12
    else:
        count = 15
    return emoji * count


def get_chain_info(chain: str) -> dict:
    chains = {
        "eth":  {"name": "Ethereum", "icon": "⟠", "explorer": "https://etherscan.io/tx/"},
        "sol":  {"name": "Solana",   "icon": "◎", "explorer": "https://solscan.io/tx/"},
        "bsc":  {"name": "BSC",      "icon": "🟡", "explorer": "https://bscscan.com/tx/"},
        "base": {"name": "Base",     "icon": "🔵", "explorer": "https://basescan.org/tx/"},
    }
    return chains.get(chain, {"name": chain.upper(), "icon": "🌐", "explorer": ""})


class BuyAlert:
    async def send_buy_alert(self, bot: Bot, chat_id: int, tx_data: dict, config: dict):
        """Güzel formatlı alım bildirimi gönder"""
        try:
            token_name   = tx_data.get("token_name", "Unknown")
            token_symbol = tx_data.get("token_symbol", "???")
            amount_usd   = float(tx_data.get("amount_usd", 0))
            tokens_rcvd  = float(tx_data.get("tokens_received", 0))
            mcap         = float(tx_data.get("mcap", 0))
            chain        = tx_data.get("chain", "eth")
            pair_url     = tx_data.get("pair_url", "")

            emoji      = config.get("emoji", "🟢")
            media_id   = config.get("media_file_id")
            media_type = config.get("media_type", "gif")
            tg_link    = config.get("tg_link", "")
            web_link   = config.get("web_link", "")
            x_link     = config.get("x_link", "")

            chain_info = get_chain_info(chain)
            emoji_bar  = build_emoji_bar(amount_usd, emoji)

            # ─── Mesaj metni ───
            text_lines = [
                f"*{token_name} (${token_symbol}) Buy!*\n",
                f"{emoji_bar}\n",
                f"💰 Spent: *${amount_usd:,.2f}*",
                f"🪙 Got: *{format_tokens(tokens_rcvd)} {token_symbol}*",
            ]

            if mcap > 0:
                text_lines.append(f"📊 MCAP: *${format_number(mcap)}*")

            text_lines.append(f"🔗 Chain: *{chain_info['name']}*")

            # Linkler
            link_parts = []
            if pair_url:
                link_parts.append(f"[📈 Chart]({pair_url})")
            if tg_link:
                link_parts.append(f"[📱 Telegram]({tg_link})")
            if web_link:
                link_parts.append(f"[🌐 Web]({web_link})")
            if x_link:
                link_parts.append(f"[✖️ X]({x_link})")

            if link_parts:
                text_lines.append("\n" + " | ".join(link_parts))

            caption = "\n".join(text_lines)

            # ─── Medya ile gönder ───
            if media_id:
                if media_type == "gif":
                    await bot.send_animation(
                        chat_id=chat_id,
                        animation=media_id,
                        caption=caption,
                        parse_mode="Markdown"
                    )
                else:
                    await bot.send_video(
                        chat_id=chat_id,
                        video=media_id,
                        caption=caption,
                        parse_mode="Markdown"
                    )
            else:
                # Medya yoksa düz mesaj gönder
                await bot.send_message(
                    chat_id=chat_id,
                    text=caption,
                    parse_mode="Markdown",
                    disable_web_page_preview=False
                )

            logger.info(f"✅ Buy alert gönderildi: chat={chat_id}, token={token_symbol}, amount=${amount_usd:.2f}")

        except TelegramError as e:
            logger.error(f"Telegram hatası (buy alert): {e}")
        except Exception as e:
            logger.error(f"Buy alert hatası: {e}")
