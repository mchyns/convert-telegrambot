import asyncio
import logging
import sys
from aiogram import Bot
from app.bot.handlers import setup_dispatcher
from app.config.settings import settings
from app.conversion.cleanup import run_periodic_cleanup
from app.database.session import init_db

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("app.main")


import os
from aiohttp import web

async def _health_handler(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "app": settings.APP_NAME})


async def _start_health_server():
    port_env = os.getenv("PORT")
    if not port_env:
        return None
    try:
        port = int(port_env)
        app = web.Application()
        app.router.add_get("/", _health_handler)
        app.router.add_get("/health", _health_handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        logger.info(f"Render health check HTTP server listening on port {port}")
        return runner
    except Exception as e:
        logger.warning(f"Could not start health check web server: {e}")
        return None


async def main() -> None:
    """Main application lifecycle."""
    logger.info(f"Starting {settings.APP_NAME} in '{settings.APP_ENV}' environment...")

    if not settings.BOT_TOKEN or settings.BOT_TOKEN.startswith("123456789:ABC"):
        logger.warning(
            "⚠️ BOT_TOKEN is empty or still set to the default placeholder in .env! "
            "Please configure a valid token from @BotFather to connect to Telegram."
        )

    # 1. Initialize Database
    try:
        await init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.exception(f"Failed to initialize database: {e}")
        sys.exit(1)

    # 2. Ensure temporary directory exists
    temp_dir = settings.temp_path
    logger.info(f"Temporary file storage initialized at: {temp_dir}")

    # 3. Start periodic background cleanup task & optional health check server for Render
    cleanup_task = asyncio.create_task(run_periodic_cleanup())
    health_runner = await _start_health_server()

    # 4. Initialize Telegram Bot & Dispatcher
    bot = Bot(token=settings.BOT_TOKEN or "dummy_token_for_init")
    dp = setup_dispatcher()

    try:
        if not settings.BOT_TOKEN or settings.BOT_TOKEN.startswith("123456789:ABC"):
            logger.info("Bot is in configuration check mode. Waiting for valid BOT_TOKEN...")
            # Keep alive so periodic background cleanup runs and health checks pass
            await asyncio.Event().wait()
        else:
            bot_info = await bot.get_me()
            logger.info(f"Bot connected successfully as @{bot_info.username} (ID: {bot_info.id})")
            logger.info("Starting Telegram Long Polling...")
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except asyncio.CancelledError:
        logger.info("Received termination signal, shutting down...")
    except Exception as e:
        logger.exception(f"Error during bot execution: {e}")
    finally:
        cleanup_task.cancel()
        if health_runner:
            await health_runner.cleanup()
        await bot.session.close()
        logger.info("Bot application shutdown completed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Process exited.")
