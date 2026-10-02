from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from app.bot.keyboards.main import get_back_keyboard
from app.config.settings import settings

router = Router(name="help")

HELP_USAGE_TEXT = (
    "📖 *Cara Menggunakan DocPDF Bot:*\n\n"
    "1. *Kirim File:* Lampirkan file dokumen Anda (`.docx` atau `.pdf`) ke chat ini.\n"
    "2. *Deteksi Otomatis:* Bot secara cerdas mengenali format dokumen Anda.\n"
    "3. *Proses Konversi:* Sistem memproses konversi dengan aman di server.\n"
    "4. *Terima Dokumen:* File hasil langsung dikirim kembali ke chat Anda.\n\n"
    "🔒 *Keamanan & Privasi:* Dokumen sementara otomatis dimusnahkan segera setelah "
    "konversi selesai. Server tidak menyimpan dokumen Anda secara permanen."
)

HELP_FORMATS_TEXT = (
    "📄 *Format yang Didukung:*\n\n"
    "• *DOCX → PDF:*\n"
    "  Mengubah file Microsoft Word menjadi dokumen PDF siap kirim atau cetak.\n\n"
    "• *PDF → DOCX:*\n"
    "  Mengubah file PDF digital menjadi dokumen Word yang dapat diedit kembali.\n\n"
    f"⚖️ *Batasan:* Maksimal *{settings.MAX_FILE_SIZE_MB} MB* per dokumen.\n"
    "💡 *Tips:* Pastikan file PDF berbasis teks agar hasil konversi ke Word optimal."
)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle /help command."""
    await message.answer(
        text=HELP_USAGE_TEXT,
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown",
    )


@router.callback_query(lambda c: c.data == "help_usage")
async def cb_help_usage(callback: CallbackQuery) -> None:
    """Handle Cara Menggunakan callback."""
    if callback.message:
        await callback.message.edit_text(
            text=HELP_USAGE_TEXT,
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown",
        )
    await callback.answer()


@router.callback_query(lambda c: c.data == "help_formats")
async def cb_help_formats(callback: CallbackQuery) -> None:
    """Handle Format Didukung callback."""
    if callback.message:
        await callback.message.edit_text(
            text=HELP_FORMATS_TEXT,
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown",
        )
    await callback.answer()
