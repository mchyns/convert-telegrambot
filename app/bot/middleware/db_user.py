from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser
from app.database.session import get_db_session
from app.database.repository import Repository


class DatabaseUserMiddleware(BaseMiddleware):
    """Middleware to register and fetch the user model for each incoming update."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        tg_user: TgUser | None = data.get("event_from_user")
        if tg_user and not tg_user.is_bot:
            async with get_db_session() as session:
                repo = Repository(session)
                user = await repo.get_or_create_user(
                    telegram_id=tg_user.id,
                    username=tg_user.username,
                    first_name=tg_user.first_name,
                    last_name=tg_user.last_name,
                )
                data["user"] = user
                data["repo"] = repo
                return await handler(event, data)

        return await handler(event, data)
