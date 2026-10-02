from aiogram import Dispatcher
from app.bot.handlers import about, admin, cancel, document, help, start, status
from app.bot.middleware import AntiSpamMiddleware, DatabaseUserMiddleware


def setup_dispatcher() -> Dispatcher:
    """Create and configure aiogram Dispatcher with middlewares and routers."""
    dp = Dispatcher()

    # Middlewares
    dp.message.middleware(AntiSpamMiddleware())
    dp.callback_query.middleware(AntiSpamMiddleware())
    dp.message.middleware(DatabaseUserMiddleware())
    dp.callback_query.middleware(DatabaseUserMiddleware())

    # Handlers / Routers
    dp.include_router(start.router)
    dp.include_router(help.router)
    dp.include_router(status.router)
    dp.include_router(cancel.router)
    dp.include_router(about.router)
    dp.include_router(admin.router)
    dp.include_router(document.router)

    return dp
