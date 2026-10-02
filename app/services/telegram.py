import logging
from pathlib import Path
from typing import Optional
from aiogram import Bot
from aiogram.types import FSInputFile
from app.config.settings import settings

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Helper service to send messages and documents directly via Bot API."""

    def __init__(self, bot_token: Optional[str] = None):
        self.bot_token = bot_token or settings.BOT_TOKEN
        self._bot: Optional[Bot] = None

    def get_bot(self) -> Bot:
        if not self._bot:
            if not self.bot_token:
                raise ValueError("BOT_TOKEN is not configured in settings.")
            self._bot = Bot(token=self.bot_token)
        return self._bot

    async def send_message(self, chat_id: int, text: str, reply_to_message_id: Optional[int] = None) -> Optional[int]:
        """Send a text message and return the sent message ID."""
        try:
            bot = self.get_bot()
            msg = await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_to_message_id=reply_to_message_id,
                parse_mode="Markdown",
            )
            return msg.message_id
        except Exception as e:
            logger.warning(f"Failed to send Telegram message to {chat_id}: {e}")
            return None

    async def edit_message(self, chat_id: int, message_id: int, text: str) -> bool:
        """Edit an existing message text."""
        try:
            bot = self.get_bot()
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                parse_mode="Markdown",
            )
            return True
        except Exception as e:
            logger.debug(f"Could not edit message {message_id} for chat {chat_id}: {e}")
            return False

    async def send_document(
        self,
        chat_id: int,
        file_path: Path,
        filename: str,
        caption: str = "",
        reply_to_message_id: Optional[int] = None,
    ) -> bool:
        """Send document file to user."""
        try:
            bot = self.get_bot()
            input_file = FSInputFile(path=str(file_path), filename=filename)
            await bot.send_document(
                chat_id=chat_id,
                document=input_file,
                caption=caption,
                reply_to_message_id=reply_to_message_id,
                parse_mode="Markdown",
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send document to {chat_id}: {e}")
            return False

    async def close(self) -> None:
        if self._bot:
            await self._bot.session.close()
            self._bot = None


notifier = TelegramNotifier()
