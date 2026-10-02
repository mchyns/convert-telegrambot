from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from app.database.repository import Repository
from app.database.session import get_db_session

router = Router(name="cancel")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message) -> None:
    """Handle /cancel command to cancel any queued jobs belonging to the user."""
    telegram_id = message.from_user.id
    async with get_db_session() as session:
        repo = Repository(session)
        cancelled_count = await repo.cancel_user_queued_jobs(telegram_id)

    if cancelled_count > 0:
        await message.answer(
            f"✅ Berhasil membatalkan *{cancelled_count}* pekerjaan di dalam antrian.",
            parse_mode="Markdown",
        )
    else:
        await message.answer(
            "ℹ️ Tidak ada dokumen yang sedang berada di antrian untuk dibatalkan.",
            parse_mode="Markdown",
        )
