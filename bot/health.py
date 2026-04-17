"""
Lightweight health-check HTTP server for keep-alive / Replit Always-On.
Runs inside the same asyncio event loop as the bot using aiohttp.
"""
import asyncio
import logging
from aiohttp import web

logger = logging.getLogger(__name__)

_runner = None


async def _health(request):
    return web.Response(text="OK\n", content_type="text/plain")


async def _ready(request):
    return web.Response(text='{"status":"ok","service":"telegram-buy-bot"}\n',
                        content_type="application/json")


_CANDIDATE_PORTS = [8080, 5000, 8000, 6000, 9000, 3000]


async def start_health_server(port: int = 8080):
    global _runner
    app = web.Application()
    app.router.add_get("/", _health)
    app.router.add_get("/health", _health)
    app.router.add_get("/ready", _ready)

    _runner = web.AppRunner(app, access_log=None)
    await _runner.setup()

    candidates = [port] + [p for p in _CANDIDATE_PORTS if p != port]
    for p in candidates:
        site = web.TCPSite(_runner, "0.0.0.0", p)
        try:
            await site.start()
            logger.info("[health] Keep-alive server listening on 0.0.0.0:%d", p)
            return
        except OSError:
            logger.warning("[health] Port %d in use — trying next", p)

    logger.error("[health] Could not bind any health-check port — bot continues without it")


async def stop_health_server():
    global _runner
    if _runner:
        await _runner.cleanup()
