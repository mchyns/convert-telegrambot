import datetime
import os
import tempfile
import time
from pathlib import Path
from app.conversion.cleanup import cleanup_expired_directories, cleanup_job_directory


def test_cleanup_job_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        job_dir = Path(tmpdir) / "job-123"
        job_dir.mkdir()
        (job_dir / "sample.txt").write_text("temporary data")

        assert job_dir.exists()
        success = cleanup_job_directory(job_dir)
        assert success is True
        assert not job_dir.exists()


def test_cleanup_expired_directories():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        fresh_dir = base_dir / "fresh"
        old_dir = base_dir / "old"

        fresh_dir.mkdir()
        old_dir.mkdir()

        # Set old_dir's mtime to 2 hours ago
        two_hours_ago = time.time() - 7200
        os.utime(str(old_dir), (two_hours_ago, two_hours_ago))

        # Sweep with TTL = 30 minutes
        removed = cleanup_expired_directories(temp_dir=base_dir, ttl_minutes=30)
        assert removed == 1
        assert not old_dir.exists()
        assert fresh_dir.exists()
