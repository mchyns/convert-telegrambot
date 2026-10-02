import time
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject


class AntiSpamMiddleware(BaseMiddleware):
    """Simple in-memory flood protection middleware for rapid interactions."""

    def __init__(self, min_interval_seconds: float = 0.5):
        self.min_interval = min_interval_seconds
        self.last_action: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id = None
        if isinstance(event, (Message, CallbackQuery)) and event.from_user:
            user_id = event.from_user.id

        if user_id:
            now = time.time()
            last_time = self.last_action.get(user_id, 0)
            if now - last_time < self.min_interval:
                # Silently throttle spam triggers
                return None
            self.last_action[user_id] = now

        return await handler(event, data)
