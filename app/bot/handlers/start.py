from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from app.bot.keyboards.main import get_main_keyboard

router = Router(name="start")

START_TEXT = (
    "👋 *Halo, selamat datang di DocPDF Bot!*\n\n"
    "Saya adalah asisten konversi dokumen yang cepat, aman, dan mudah digunakan langsung di Telegram.\n\n"
    "🔄 *Konversi yang didukung:*\n"
    "• *DOCX → PDF* (Format Word ke PDF siap cetak/kirim)\n"
    "• *PDF → DOCX* (Format PDF ke Word yang dapat diedit)\n\n"
    "📤 *Cara pakai:* Cukup kirimkan dokumen file (.docx / .pdf) ke chat ini.\n\n"
    "Silakan pilih menu di bawah untuk panduan lengkap:"
)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Handle /start command."""
    await message.answer(
        text=START_TEXT,
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown",
    )


@router.callback_query(lambda c: c.data == "menu_back")
async def cb_menu_back(callback: CallbackQuery) -> None:
    """Return to main menu."""
    if callback.message:
        await callback.message.edit_text(
            text=START_TEXT,
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown",
        )
    await callback.answer()
