from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from app.bot.keyboards.main import get_back_keyboard
from app.config.settings import settings

router = Router(name="about")

ABOUT_TEXT = (
    f"🤖 *{settings.APP_NAME}*\n"
    "Versi: `1.0.0 (MVP)`\n\n"
    "DocPDF Bot adalah solusi cerdas untuk konversi dokumen dua arah antara *DOCX* dan *PDF* "
    "secara instan melalui Telegram.\n\n"
    "🔒 *Kebijakan Privasi & Keamanan:*\n"
    "• Bot tidak menyimpan dokumen Anda secara permanen.\n"
    "• Setiap pekerjaan diproses dalam direktori terisolasi.\n"
    "• File sementara otomatis dihapus seketika setelah hasil dikirim.\n"
    "• Database hanya menyimpan riwayat status kuota & nomor ID Telegram.\n\n"
    "Dibuat dengan Python, aiogram 3, LibreOffice Headless, pdf2docx, dan Redis Queue."
)


@router.message(Command("about"))
async def cmd_about(message: Message) -> None:
    """Handle /about command."""
    await message.answer(
        text=ABOUT_TEXT,
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown",
    )


@router.callback_query(lambda c: c.data == "menu_about")
async def cb_menu_about(callback: CallbackQuery) -> None:
    """Handle about button callback."""
    if callback.message:
        await callback.message.edit_text(
            text=ABOUT_TEXT,
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown",
        )
    await callback.answer()
