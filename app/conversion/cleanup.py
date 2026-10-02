import asyncio
import datetime
import logging
import shutil
from pathlib import Path
from typing import Optional
from app.config.settings import settings

logger = logging.getLogger(__name__)


def cleanup_job_directory(job_dir: Path) -> bool:
    """Safely remove a job's isolated temporary directory."""
    if not job_dir.exists():
        return True

    try:
        shutil.rmtree(job_dir, ignore_errors=True)
        logger.debug(f"Removed job directory: {job_dir}")
        return True
    except Exception as e:
        logger.warning(f"Failed to remove directory {job_dir}: {e}")
        return False


def cleanup_expired_directories(
    temp_dir: Optional[Path] = None, ttl_minutes: Optional[int] = None
) -> int:
    """
    Remove temporary directories that exceed the time-to-live (TTL).
    Prevents orphaned files from consuming server disk space.
    """
    import time
    base_dir = temp_dir or settings.temp_path
    ttl = ttl_minutes or settings.FILE_TTL_MINUTES
    cutoff_time = time.time() - (ttl * 60)

    removed_count = 0
    if not base_dir.exists():
        return 0

    try:
        for item in base_dir.iterdir():
            if item.is_dir():
                try:
                    stat = item.stat()
                    if stat.st_mtime < cutoff_time:
                        shutil.rmtree(item, ignore_errors=True)
                        removed_count += 1
                        logger.info(f"Cleaned up expired directory: {item.name}")
                except Exception as ex:
                    logger.warning(f"Error checking/removing {item}: {ex}")
    except Exception as e:
        logger.error(f"Error during expired directories cleanup: {e}")

    return removed_count


async def run_periodic_cleanup() -> None:
    """Background asyncio task to periodically run directory cleanup."""
    interval_seconds = settings.CLEANUP_INTERVAL_MINUTES * 60
    logger.info(
        f"Starting periodic cleanup worker (interval: {settings.CLEANUP_INTERVAL_MINUTES}m, "
        f"TTL: {settings.FILE_TTL_MINUTES}m)"
    )
    while True:
        try:
            await asyncio.sleep(interval_seconds)
            cleaned = cleanup_expired_directories()
            if cleaned > 0:
                logger.info(f"Periodic cleanup removed {cleaned} expired job directories.")
        except asyncio.CancelledError:
            logger.info("Periodic cleanup worker cancelled.")
            break
        except Exception as e:
            logger.exception(f"Error in periodic cleanup worker: {e}")
