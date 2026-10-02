from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from app.config.settings import settings
from app.database.repository import Repository
from app.database.session import get_db_session

router = Router(name="admin")


def is_admin(user_id: int) -> bool:
    """Check if the given Telegram user ID is an admin."""
    return user_id in settings.admin_ids


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    """Handle /admin command."""
    if not is_admin(message.from_user.id):
        return

    text = (
        "👑 *Panel Perintah Administrator:*\n\n"
        "• `/admin` - Tampilkan panduan ini\n"
        "• `/stats` - Tampilkan statistik performa & konversi bot\n"
        "• `/queue` - Tampilkan kondisi antrian & worker saat ini\n"
    )
    await message.answer(text=text, parse_mode="Markdown")


@router.message(Command("stats"))
async def cmd_admin_stats(message: Message) -> None:
    """Handle /stats command for administrators."""
    if not is_admin(message.from_user.id):
        return

    async with get_db_session() as session:
        repo = Repository(session)
        metrics = await repo.get_admin_metrics()

    text = (
        "📈 *Statistik Performa Bot:*\n\n"
        f"👥 Total Pengguna   : *{metrics['total_users']}*\n"
        f"📁 Total Konversi   : *{metrics['total_jobs']}*\n"
        f"✅ Berhasil         : *{metrics['successful_jobs']}*\n"
        f"❌ Gagal            : *{metrics['failed_jobs']}*\n"
        f"🎯 Success Rate     : *{metrics['success_rate']}%*\n\n"
        "🔄 *Distribusi Format:*\n"
        f"• DOCX → PDF       : *{metrics['docx_to_pdf_count']}*\n"
        f"• PDF → DOCX       : *{metrics['pdf_to_docx_count']}*\n\n"
        "⚡ *Kondisi Antrian:*\n"
        f"• Antrian (Queued)  : *{metrics['queued_jobs']}*\n"
        f"• Sedang Diproses   : *{metrics['processing_jobs']}*"
    )
    await message.answer(text=text, parse_mode="Markdown")


@router.message(Command("queue"))
async def cmd_admin_queue(message: Message) -> None:
    """Handle /queue command for administrators."""
    if not is_admin(message.from_user.id):
        return

    async with get_db_session() as session:
        repo = Repository(session)
        queued = await repo.get_active_queue_size()
        processing = await repo.get_concurrent_processing_size()

    text = (
        "📊 *Status Antrian Server:*\n\n"
        f"• Dalam Antrian (Queued) : *{queued}* / {settings.MAX_QUEUE_SIZE}\n"
        f"• Sedang Berjalan        : *{processing}* / {settings.MAX_CONCURRENT_JOBS}\n"
        f"• Redis Queue Enabled    : *{settings.USE_REDIS_QUEUE}*"
    )
    await message.answer(text=text, parse_mode="Markdown")
