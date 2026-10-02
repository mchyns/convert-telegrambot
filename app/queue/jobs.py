import asyncio
import logging
import time
from pathlib import Path
from typing import Any, Dict
from redis import Redis
from rq import Queue
from app.config.settings import settings
from app.conversion.cleanup import cleanup_job_directory
from app.conversion.docx_to_pdf import ConversionError, convert_docx_to_pdf
from app.conversion.pdf_to_docx import convert_pdf_to_docx
from app.database.session import get_db_session
from app.database.repository import Repository
from app.services.telegram import notifier

logger = logging.getLogger("app.jobs")

REDIS_QUEUE_NAME = "docpdf_conversions"


def get_redis_connection() -> Redis:
    return Redis.from_url(settings.REDIS_URL)


def get_rq_queue() -> Queue:
    conn = get_redis_connection()
    return Queue(REDIS_QUEUE_NAME, connection=conn, default_timeout=settings.JOB_TIMEOUT_SECONDS + 30)


async def _async_process_job(job_data: Dict[str, Any]) -> None:
    """Async worker implementation handling full lifecycle of a conversion job."""
    job_uuid = job_data["job_uuid"]
    telegram_id = job_data["telegram_id"]
    status_msg_id = job_data.get("status_message_id")
    input_path = Path(job_data["input_path"])
    output_path = Path(job_data["output_path"])
    input_format = job_data["input_format"]
    output_format = job_data["output_format"]
    original_filename = job_data["original_filename"]
    target_filename = job_data["target_filename"]
    job_dir = Path(job_data["job_dir"])
    file_size = job_data.get("file_size", 0)

    start_time = time.time()
    logger.info(
        f"job={job_uuid} telegram_id={telegram_id} format={input_format}_to_{output_format} "
        f"size={file_size} status=processing"
    )

    # 1. Update Database status to 'processing'
    async with get_db_session() as session:
        repo = Repository(session)
        # Check if job was cancelled by user
        job = await repo.get_job_by_uuid(job_uuid)
        if job and job.status == "cancelled":
            logger.info(f"Job {job_uuid} was cancelled before processing started.")
            cleanup_job_directory(job_dir)
            return

        await repo.update_job_status(job_uuid, status="processing")

    # 2. Inform user that processing has started
    if status_msg_id:
        await notifier.edit_message(
            chat_id=telegram_id,
            message_id=status_msg_id,
            text=f"Sedang mengonversi *{original_filename}*...\nMohon tunggu sebentar ⏳",
        )

    # 3. Perform conversion
    conversion_error: str | None = None
    try:
        if input_format == "docx" and output_format == "pdf":
            convert_docx_to_pdf(input_path, output_path)
        elif input_format == "pdf" and output_format == "docx":
            convert_pdf_to_docx(input_path, output_path)
        else:
            raise ConversionError(f"Kombinasi format {input_format} ke {output_format} tidak didukung.")

        # 4. Conversion succeeded: Send result document to user
        caption = f"✨ *Konversi selesai!*\n\n📄 File hasil: `{target_filename}`"
        if input_format == "pdf" and output_format == "docx":
            caption += (
                "\n\n_Catatan: Tata letak (layout) PDF kompleks mungkin sedikit "
                "berbeda setelah dikonversi ke DOCX._"
            )

        sent = await notifier.send_document(
            chat_id=telegram_id,
            file_path=output_path,
            filename=target_filename,
            caption=caption,
        )

        if not sent:
            logger.error(f"Failed to send result document to Telegram user {telegram_id}")

        # Remove or update progress message
        if status_msg_id:
            await notifier.edit_message(
                chat_id=telegram_id,
                message_id=status_msg_id,
                text=f"✅ Konversi *{original_filename}* selesai dikirim.",
            )

        duration = round(time.time() - start_time, 2)
        logger.info(
            f"job={job_uuid} telegram_id={telegram_id} format={input_format}_to_{output_format} "
            f"size={file_size} status=completed duration={duration}s"
        )

        # Update DB to completed
        async with get_db_session() as session:
            repo = Repository(session)
            await repo.update_job_status(
                job_uuid,
                status="completed",
                output_filename=target_filename,
            )

    except Exception as exc:
        duration = round(time.time() - start_time, 2)
        error_msg = str(exc)
        logger.warning(
            f"job={job_uuid} telegram_id={telegram_id} format={input_format}_to_{output_format} "
            f"size={file_size} status=failed duration={duration}s error=\"{error_msg}\""
        )

        # Update DB to failed
        async with get_db_session() as session:
            repo = Repository(session)
            await repo.update_job_status(
                job_uuid,
                status="failed",
                error_message=error_msg,
            )

        # Notify user of failure without leaking internal stack trace (per PRD Section 18.4 & 34)
        user_failure_text = (
            "❌ *Konversi gagal.*\n\n"
            "Dokumen tidak dapat dikonversi. Kemungkinan penyebab:\n"
            "• File dokumen rusak atau terproteksi password\n"
            "• Struktur dokumen atau layout tidak didukung\n"
            "• Waktu konversi habis (timeout)\n\n"
            "Silakan coba kirim file dokumen lainnya."
        )
        if status_msg_id:
            await notifier.edit_message(
                chat_id=telegram_id,
                message_id=status_msg_id,
                text=user_failure_text,
            )
        else:
            await notifier.send_message(
                chat_id=telegram_id,
                text=user_failure_text,
            )

    finally:
        # 5. Always cleanup isolated temporary directory per PRD Section 1.2, 15.1, 28
        cleanup_job_directory(job_dir)


def rq_worker_job_entry(job_data: Dict[str, Any]) -> None:
    """Synchronous entry point called by RQ worker processes."""
    asyncio.run(_async_process_job(job_data))


async def enqueue_conversion_job(job_data: Dict[str, Any]) -> str:
    """
    Enqueue a conversion job into RQ if Redis queue is enabled,
    otherwise run asynchronously via asyncio task for lightweight local development.
    """
    if settings.USE_REDIS_QUEUE:
        try:
            q = get_rq_queue()
            job = q.enqueue(rq_worker_job_entry, job_data, job_id=job_data["job_uuid"])
            logger.info(f"Enqueued job {job_data['job_uuid']} to Redis queue '{REDIS_QUEUE_NAME}'.")
            return job.id
        except Exception as e:
            logger.warning(
                f"Failed to enqueue to Redis queue ({e}). Falling back to local async runner."
            )

    # Fallback / standalone mode: run directly in background asyncio task
    asyncio.create_task(_async_process_job(job_data))
    return job_data["job_uuid"]
