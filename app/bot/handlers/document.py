import logging
from aiogram import F, Router
from aiogram.types import Message
from app.config.settings import settings
from app.conversion.validator import ValidationError, detect_file_format
from app.database.models import User
from app.services.job_service import JobLimitError, JobService

logger = logging.getLogger(__name__)

router = Router(name="document")


def format_file_size(size_bytes: int) -> str:
    """Format bytes into readable MB or KB representation."""
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes} Bytes"


@router.message(F.document)
async def handle_document_upload(message: Message, user: User) -> None:
    """Handle incoming document upload and trigger conversion pipeline."""
    doc = message.document
    if not doc:
        return

    raw_filename = doc.file_name or "document"
    file_size = doc.file_size or 0
    mime_type = doc.mime_type or ""

    # 1. Quick initial format check before downloading
    try:
        input_format = detect_file_format(raw_filename, mime_type)
    except ValidationError:
        await message.reply(
            "⚠️ *Format file belum didukung.*\n\n"
            "Format yang saat ini dapat diproses:\n"
            "• *DOCX* (Microsoft Word Document)\n"
            "• *PDF* (Portable Document Format)\n\n"
            "Silakan kirimkan dokumen dengan ekstensi `.docx` atau `.pdf`.",
            parse_mode="Markdown",
        )
        return

    # 2. Size check
    if file_size > settings.max_file_size_bytes:
        await message.reply(
            f"⚠️ *Ukuran file terlalu besar.*\n\n"
            f"Batas maksimal yang diperbolehkan adalah *{settings.MAX_FILE_SIZE_MB} MB*.\n"
            f"Ukuran file Anda: *{format_file_size(file_size)}*.",
            parse_mode="Markdown",
        )
        return

    # 3. Prepare job (limits check, folder creation, DB record)
    try:
        (
            job_uuid,
            in_fmt,
            out_fmt,
            job_dir,
            input_path,
            output_path,
        ) = await JobService.prepare_job(
            telegram_id=message.from_user.id,
            user=user,
            raw_filename=raw_filename,
            file_size=file_size,
            mime_type=mime_type,
        )
    except JobLimitError as jle:
        await message.reply(f"⚠️ {str(jle)}")
        return
    except Exception as e:
        logger.exception(f"Unexpected error preparing job: {e}")
        await message.reply("Terjadi kendala saat memproses antrian dokumen. Silakan coba lagi nanti.")
        return

    # 4. Immediate user feedback per PRD Section 18.1
    conversion_label = f"{in_fmt.upper()} → {out_fmt.upper()}"
    status_text = (
        "📥 *File diterima.*\n\n"
        f"📄 *Nama:*\n`{raw_filename}`\n\n"
        f"📦 *Ukuran:*\n{format_file_size(file_size)}\n\n"
        f"🔄 *Konversi:*\n*{conversion_label}*\n\n"
        "⏳ *Status:*\nMasuk antrian pemrosesan..."
    )
    status_msg = await message.reply(status_text, parse_mode="Markdown")

    # 5. Download document from Telegram API & dispatch to worker
    try:
        await JobService.download_and_dispatch(
            bot=message.bot,
            file_id=doc.file_id,
            job_uuid=job_uuid,
            telegram_id=message.from_user.id,
            status_message_id=status_msg.message_id,
            input_format=in_fmt,
            output_format=out_fmt,
            original_filename=raw_filename,
            target_filename=output_path.name,
            job_dir=job_dir,
            input_path=input_path,
            output_path=output_path,
            file_size=file_size,
        )
    except ValidationError as ve:
        await status_msg.edit_text(
            f"❌ *Dokumen tidak valid:*\n{str(ve)}\n\nSilakan periksa kembali file Anda."
        )
    except Exception as exc:
        logger.error(f"Failed to download/dispatch document for user {message.from_user.id}: {exc}")
        await status_msg.edit_text(
            "❌ *Gagal mengunduh dokumen.*\n"
            "Terjadi gangguan koneksi saat mengunduh dokumen dari Telegram. Silakan coba kirim ulang."
        )


@router.message(F.photo | F.video | F.audio | F.voice)
async def handle_non_document_media(message: Message) -> None:
    """Prompt user when they send unsupported media instead of documents."""
    await message.reply(
        "ℹ️ File media ini bukan dokumen.\n\n"
        "Kirim file sebagai *Dokumen / File* dengan format `.docx` atau `.pdf` "
        "agar dapat diproses.",
        parse_mode="Markdown",
    )
