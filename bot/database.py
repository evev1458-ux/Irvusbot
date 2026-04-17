import aiosqlite
import os
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "bot.db")


async def get_db():
    return await aiosqlite.connect(DB_PATH)


async def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS group_config (
                group_id INTEGER PRIMARY KEY,
                network TEXT,
                contract_address TEXT,
                token_name TEXT,
                token_symbol TEXT,
                min_buy_usd REAL DEFAULT 0,
                media_file_id TEXT,
                media_type TEXT,
                telegram_link TEXT,
                website_link TEXT,
                x_link TEXT,
                custom_emoji TEXT DEFAULT '🟢',
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS setup_state (
                group_id INTEGER PRIMARY KEY,
                step TEXT,
                network TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS media_awaiting (
                group_id INTEGER PRIMARY KEY,
                admin_id INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tracked_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                contract_address TEXT,
                network TEXT,
                token_name TEXT,
                token_symbol TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(group_id, contract_address, network)
            )
        """)
        await db.commit()
    logger.info("Database initialized at %s", DB_PATH)


async def get_group_config(group_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM group_config WHERE group_id = ?", (group_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def set_group_config(group_id: int, **kwargs):
    existing = await get_group_config(group_id)
    async with aiosqlite.connect(DB_PATH) as db:
        if existing:
            sets = ", ".join(f"{k} = ?" for k in kwargs)
            sets += ", updated_at = CURRENT_TIMESTAMP"
            await db.execute(
                f"UPDATE group_config SET {sets} WHERE group_id = ?",
                (*kwargs.values(), group_id)
            )
        else:
            kwargs["group_id"] = group_id
            cols = ", ".join(kwargs.keys())
            placeholders = ", ".join("?" for _ in kwargs)
            await db.execute(
                f"INSERT INTO group_config ({cols}) VALUES ({placeholders})",
                tuple(kwargs.values())
            )
        await db.commit()


async def get_setup_state(group_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM setup_state WHERE group_id = ?", (group_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def set_setup_state(group_id: int, step: str, network: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO setup_state (group_id, step, network, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(group_id) DO UPDATE SET
                step = excluded.step,
                network = excluded.network,
                updated_at = CURRENT_TIMESTAMP
        """, (group_id, step, network))
        await db.commit()


async def clear_setup_state(group_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM setup_state WHERE group_id = ?", (group_id,))
        await db.commit()


async def set_media_awaiting(group_id: int, admin_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO media_awaiting (group_id, admin_id, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(group_id) DO UPDATE SET
                admin_id = excluded.admin_id,
                updated_at = CURRENT_TIMESTAMP
        """, (group_id, admin_id))
        await db.commit()


async def get_media_awaiting(group_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM media_awaiting WHERE group_id = ?", (group_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def clear_media_awaiting(group_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM media_awaiting WHERE group_id = ?", (group_id,))
        await db.commit()


async def add_tracked_token(group_id: int, contract_address: str, network: str,
                            token_name: str, token_symbol: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO tracked_tokens
            (group_id, contract_address, network, token_name, token_symbol)
            VALUES (?, ?, ?, ?, ?)
        """, (group_id, contract_address, network, token_name, token_symbol))
        await db.commit()


async def remove_tracked_token(group_id: int, contract_address: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            DELETE FROM tracked_tokens
            WHERE group_id = ? AND contract_address = ?
        """, (group_id, contract_address))
        await db.commit()


async def get_tracked_tokens(group_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM tracked_tokens WHERE group_id = ?", (group_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_all_active_groups() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM group_config WHERE active = 1 AND contract_address IS NOT NULL"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
