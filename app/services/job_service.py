import logging
import uuid
from pathlib import Path
from typing import Optional, Tuple
from aiogram import Bot
from app.config.settings import settings
from app.conversion.cleanup import cleanup_job_directory
from app.conversion.validator import (
    ValidationError,
    detect_file_format,
    get_target_filename,
    sanitize_filename,
    validate_file_size,
    validate_input_document,
)
from app.database.models import Job, User
from app.database.repository import Repository
from app.database.session import get_db_session
from app.queue.jobs import enqueue_conversion_job

logger = logging.getLogger(__name__)


class JobLimitError(Exception):
    """Raised when server or user quota limits are exceeded."""
    pass


class JobService:
    """Service to coordinate validation, persistence, file downloading, and dispatching."""

    @staticmethod
    async def prepare_job(
        telegram_id: int,
        user: User,
        raw_filename: str,
        file_size: int,
        mime_type: Optional[str] = None,
    ) -> Tuple[str, str, str, Path, Path, Path]:
        """
        Validate business rules, quotas, limits, formats, create directories, and register job in DB.
        Returns: (job_uuid, input_format, output_format, job_dir, input_path, output_path)
        """
        # 1. User ban check
        if user.is_banned:
            raise JobLimitError("Akun Anda telah dinonaktifkan oleh administrator.")

        # 2. File size check
        validate_file_size(file_size, settings.max_file_size_bytes)

        # 3. Format detection
        input_format = detect_file_format(raw_filename, mime_type or "")
        output_format = "pdf" if input_format == "docx" else "docx"

        # 4. Hourly rate limit check
        async with get_db_session() as session:
            repo = Repository(session)
            recent_jobs = await repo.get_user_jobs_in_last_hour(telegram_id)
            if recent_jobs >= settings.MAX_JOBS_PER_USER_PER_HOUR:
                raise JobLimitError(
                    f"Batas konversi per jam tercapai (maksimal {settings.MAX_JOBS_PER_USER_PER_HOUR} file/jam). "
                    "Silakan coba lagi beberapa saat."
                )

            # 5. Global queue depth check
            queue_size = await repo.get_active_queue_size()
            if queue_size >= settings.MAX_QUEUE_SIZE:
                raise JobLimitError(
                    "Server saat ini sedang sibuk dan antrian penuh. "
                    "Silakan kirimkan kembali file Anda dalam beberapa menit."
                )

            # 6. Generate UUID & isolated job directory per PRD Section 15.1
            job_uuid = str(uuid.uuid4())
            job_dir = settings.temp_path / job_uuid
            input_dir = job_dir / "input"
            output_dir = job_dir / "output"
            input_dir.mkdir(parents=True, exist_ok=True)
            output_dir.mkdir(parents=True, exist_ok=True)

            safe_input_name = sanitize_filename(raw_filename)
            target_filename = get_target_filename(safe_input_name, output_format)

            # Isolated input and output paths (prevent path traversal using UUID stem)
            input_path = input_dir / f"input.{input_format}"
            output_path = output_dir / target_filename

            # 7. Record job in database
            await repo.create_job(
                user_id=user.id,
                job_uuid=job_uuid,
                input_filename=safe_input_name,
                output_filename=target_filename,
                input_format=input_format,
                output_format=output_format,
                input_size=file_size,
            )

        return job_uuid, input_format, output_format, job_dir, input_path, output_path

    @staticmethod
    async def download_and_dispatch(
        bot: Bot,
        file_id: str,
        job_uuid: str,
        telegram_id: int,
        status_message_id: int,
        input_format: str,
        output_format: str,
        original_filename: str,
        target_filename: str,
        job_dir: Path,
        input_path: Path,
        output_path: Path,
        file_size: int,
    ) -> None:
        """Download uploaded file from Telegram API, validate content integrity, and enqueue conversion."""
        try:
            # Download file from Telegram
            file_info = await bot.get_file(file_id)
            if not file_info.file_path:
                raise ValidationError("Gagal mengambil file dari Telegram API.")

            await bot.download_file(file_info.file_path, destination=input_path)

            # Deep document validation (magic bytes, container, corruption, zip bomb)
            validate_input_document(input_path, input_format, settings.max_file_size_bytes)

            # Prepare payload for background worker
            job_payload = {
                "job_uuid": job_uuid,
                "telegram_id": telegram_id,
                "status_message_id": status_message_id,
                "input_path": str(input_path),
                "output_path": str(output_path),
                "input_format": input_format,
                "output_format": output_format,
                "original_filename": original_filename,
                "target_filename": target_filename,
                "job_dir": str(job_dir),
                "file_size": file_size,
            }

            await enqueue_conversion_job(job_payload)

        except Exception as e:
            logger.error(f"Error during download & dispatch for job {job_uuid}: {e}")
            cleanup_job_directory(job_dir)
            async with get_db_session() as session:
                repo = Repository(session)
                await repo.update_job_status(job_uuid, status="failed", error_message=str(e))
            raise
