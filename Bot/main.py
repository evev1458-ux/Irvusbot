import asyncio
import logging
import os
import sys

from telegram import Update
from telegram.error import Conflict, NetworkError
from telegram.ext import Application, ContextTypes

from .database import init_db
from .handlers.setup import get_setup_handlers
from .handlers.settings import get_settings_handlers
from .handlers.ai_commands import get_ai_handlers
from .handlers.message_router import get_router_handlers
from .monitor import monitor_loop
from .health import start_health_server

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("aiohttp.access").setLevel(logging.WARNING)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    err = context.error
    if isinstance(err, Conflict):
        logger.warning("[tg] Conflict (old instance still alive) — will self-resolve: %s", err)
        return
    if isinstance(err, NetworkError):
        logger.warning("[tg] Network error (transient): %s", err)
        return
    logger.error("[tg] Unhandled exception: %s", err, exc_info=err)


async def post_init(application: Application):
    await init_db()
    logger.info("Database initialized")

    # Start health-check / keep-alive server (tries 8080, then falls back)
    health_port = int(os.environ.get("HEALTH_PORT", "8080"))
    try:
        await start_health_server(port=health_port)
    except Exception as e:
        logger.warning("[health] Server startup failed (non-fatal): %s", e)

    # Start the buy monitor
    bot = application.bot
    asyncio.create_task(monitor_loop(bot))
    logger.info("Buy monitor started")


def run():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        sys.exit(1)

    logger.info("Starting Buy Bot...")

    application = (
        Application.builder()
        .token(token)
        .post_init(post_init)
        .build()
    )

    for handler in get_setup_handlers():
        application.add_handler(handler)

    for handler in get_settings_handlers():
        application.add_handler(handler)

    for handler in get_ai_handlers():
        application.add_handler(handler)

    # Must be last — catches all unhandled text/media
    for handler in get_router_handlers():
        application.add_handler(handler)

    application.add_error_handler(error_handler)

    logger.info("All handlers registered — polling...")
    application.run_polling(
        allowed_updates=["message", "callback_query", "chat_member"],
        drop_pending_updates=True,
    )
