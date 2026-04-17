# Telegram Buy Bot

## Overview

Production-ready Telegram "Buy Bot" and AI Assistant built with Python. Monitors on-chain token swaps across multiple networks and fires real-time buy alerts with a custom high-end UI/UX in Telegram groups.

## Stack

- **Language**: Python 3.11
- **Telegram Framework**: python-telegram-bot v22
- **AI**: OpenAI GPT-4o-mini (chat) + DALL-E 3 (image generation)
- **On-chain data**: DexScreener API (real-time token price + volume)
- **Database**: SQLite via aiosqlite (multi-tenant, per-group isolation)
- **Networks**: Ethereum, Solana, BSC (BNB Chain), Base

## Project Structure

```
bot/
├── main.py              # Bot entry point, handler registration
├── database.py          # SQLite database layer (multi-tenant)
├── dex_tracker.py       # DexScreener API, price data, alert formatting
├── monitor.py           # Background buy monitor loop
├── ai_features.py       # OpenAI chat + DALL-E image generation
├── handlers/
│   ├── setup.py         # /setup command + network selection
│   ├── settings.py      # /settings dashboard + inline buttons
│   ├── ai_commands.py   # /ask, /draw, /price, /help commands
│   └── message_router.py # Unified message routing (text + media)
├── data/
│   └── bot.db           # SQLite database (auto-created)
└── media/               # Reserved for local media assets
run_bot.py               # Entry point
```

## Key Commands (for users in Telegram)

- `/setup` — Select network + enter contract address to start monitoring
- `/settings` — Open the full settings dashboard (admin only)
- `/price` — Show current token price and market data
- `/ask [question]` — Ask the AI assistant anything about crypto
- `/draw [prompt]` — Generate an AI image with DALL-E 3
- `@BotUsername [question]` — Mention the bot to chat with AI

## Running the Bot

```bash
python run_bot.py
```

The "Telegram Buy Bot" workflow runs this automatically.

## Environment Secrets Required

- `TELEGRAM_BOT_TOKEN` — From @BotFather on Telegram
- `OPENAI_API_KEY` — From platform.openai.com

## Features

### Multi-Tenancy
Each Telegram group has isolated config. Group A's tokens/settings never bleed into Group B.

### Buy Alert Format
```
[Custom GIF/Video]
TokenName ($SYMBOL) Buy!
🟢🟢🟢 (dynamic — scales with buy size)

💰 Spent: $500.00
🪙 Got: 50M TOKEN
📊 MCAP: $1.50M
⛓️ Chain: Ethereum

🔗 [Chart] | Telegram | Website | X/Twitter
```

### Settings Dashboard
Inline button panel with: Telegram Link, Website Link, X Link, Custom Emoji, Min Buy ($), Add Media, Add Token, Remove Token.

### AI Features
- Conversational AI in any group (mention the bot)
- /ask command for direct questions
- /draw command for DALL-E image generation

## Monorepo Note

This workspace also contains a TypeScript API server (artifacts/api-server) and a mockup sandbox (artifacts/mockup-sandbox) from the original template — these are unused by the bot.
