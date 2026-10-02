from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from app.bot.keyboards.main import get_back_keyboard
from app.database.models import User
from app.database.repository import Repository
from app.database.session import get_db_session

router = Router(name="status")


async def build_status_text(telegram_id: int) -> str:
    """Build status summary text for user."""
    async with get_db_session() as session:
        repo = Repository(session)
        counts = await repo.get_user_job_stats(telegram_id)

    return (
        "📊 *Status Dokumen Kamu:*\n\n"
        f"⏳ Antrian (Queue) : *{counts.get('queued', 0)}*\n"
        f"⚙️ Sedang Diproses : *{counts.get('processing', 0)}*\n"
        f"✅ Selesai         : *{counts.get('completed', 0)}*\n"
        f"❌ Gagal           : *{counts.get('failed', 0)}*\n"
    )


@router.message(Command("status"))
async def cmd_status(message: Message, user: User) -> None:
    """Handle /status command."""
    text = await build_status_text(message.from_user.id)
    await message.answer(
        text=text,
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown",
    )


@router.callback_query(lambda c: c.data == "menu_status")
async def cb_menu_status(callback: CallbackQuery) -> None:
    """Handle status button callback from main menu."""
    text = await build_status_text(callback.from_user.id)
    if callback.message:
        await callback.message.edit_text(
            text=text,
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown",
        )
    await callback.answer()
