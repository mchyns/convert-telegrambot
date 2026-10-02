import datetime
from typing import Dict, List, Optional
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import Job, User


class Repository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> User:
        """Get an existing user or create a new user record."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            # Update user profile info if changed
            if (
                user.username != username
                or user.first_name != first_name
                or user.last_name != last_name
            ):
                user.username = username
                user.first_name = first_name
                user.last_name = last_name
                user.updated_at = datetime.datetime.now(datetime.timezone.utc)
                await self.session.flush()
            return user

        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_job(
        self,
        user_id: int,
        job_uuid: str,
        input_filename: str,
        output_filename: str,
        input_format: str,
        output_format: str,
        input_size: int,
    ) -> Job:
        job = Job(
            job_uuid=job_uuid,
            user_id=user_id,
            input_filename=input_filename,
            output_filename=output_filename,
            input_format=input_format,
            output_format=output_format,
            input_size=input_size,
            status="queued",
        )
        self.session.add(job)

        # Increment total_jobs on user
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                total_jobs=User.total_jobs + 1,
                updated_at=datetime.datetime.now(datetime.timezone.utc),
            )
        )
        await self.session.flush()
        return job

    async def get_job_by_uuid(self, job_uuid: str) -> Optional[Job]:
        stmt = select(Job).where(Job.job_uuid == job_uuid)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_job_status(
        self,
        job_uuid: str,
        status: str,
        error_message: Optional[str] = None,
        output_filename: Optional[str] = None,
    ) -> Optional[Job]:
        job = await self.get_job_by_uuid(job_uuid)
        if not job:
            return None

        now = datetime.datetime.now(datetime.timezone.utc)
        job.status = status
        job.updated_at = now

        if output_filename:
            job.output_filename = output_filename

        if status == "processing" and not job.processing_started_at:
            job.processing_started_at = now
        elif status in ("completed", "failed", "cancelled"):
            job.processing_finished_at = now
            if error_message:
                job.error_message = error_message

            # Update User stats
            if status == "completed":
                await self.session.execute(
                    update(User)
                    .where(User.id == job.user_id)
                    .values(
                        successful_jobs=User.successful_jobs + 1,
                        updated_at=now,
                    )
                )
            elif status == "failed":
                await self.session.execute(
                    update(User)
                    .where(User.id == job.user_id)
                    .values(
                        failed_jobs=User.failed_jobs + 1,
                        updated_at=now,
                    )
                )

        await self.session.flush()
        return job

    async def get_user_job_stats(self, telegram_id: int) -> Dict[str, int]:
        """Returns counts for queued, processing, completed, failed for a user."""
        stmt = (
            select(Job.status, func.count(Job.id))
            .join(User, Job.user_id == User.id)
            .where(User.telegram_id == telegram_id)
            .group_by(Job.status)
        )
        result = await self.session.execute(stmt)
        counts = {"queued": 0, "processing": 0, "completed": 0, "failed": 0, "cancelled": 0}
        for status, count in result.fetchall():
            if status in counts:
                counts[status] = count
        return counts

    async def cancel_user_queued_jobs(self, telegram_id: int) -> int:
        """Cancel all jobs for a user that are still queued."""
        user = await self.get_user_by_telegram_id(telegram_id)
        if not user:
            return 0

        stmt = (
            update(Job)
            .where(Job.user_id == user.id, Job.status == "queued")
            .values(
                status="cancelled",
                error_message="Dibatalkan oleh pengguna",
                processing_finished_at=datetime.datetime.now(datetime.timezone.utc),
                updated_at=datetime.datetime.now(datetime.timezone.utc),
            )
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount

    async def get_user_jobs_in_last_hour(self, telegram_id: int) -> int:
        """Count jobs created by user in the last hour for rate limiting."""
        one_hour_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
        stmt = (
            select(func.count(Job.id))
            .join(User, Job.user_id == User.id)
            .where(User.telegram_id == telegram_id, Job.created_at >= one_hour_ago)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0

    async def get_active_queue_size(self) -> int:
        """Get number of jobs currently in queued status."""
        stmt = select(func.count(Job.id)).where(Job.status == "queued")
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0

    async def get_concurrent_processing_size(self) -> int:
        """Get number of jobs currently in processing status."""
        stmt = select(func.count(Job.id)).where(Job.status == "processing")
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0

    async def get_admin_metrics(self) -> Dict[str, any]:
        """Aggregate stats for admin dashboard/command."""
        total_users_stmt = select(func.count(User.id))
        total_jobs_stmt = select(func.count(Job.id))
        successful_jobs_stmt = select(func.count(Job.id)).where(Job.status == "completed")
        failed_jobs_stmt = select(func.count(Job.id)).where(Job.status == "failed")
        queued_jobs_stmt = select(func.count(Job.id)).where(Job.status == "queued")
        processing_jobs_stmt = select(func.count(Job.id)).where(Job.status == "processing")

        docx_to_pdf_stmt = select(func.count(Job.id)).where(Job.input_format == "docx")
        pdf_to_docx_stmt = select(func.count(Job.id)).where(Job.input_format == "pdf")

        total_users = (await self.session.execute(total_users_stmt)).scalar_one() or 0
        total_jobs = (await self.session.execute(total_jobs_stmt)).scalar_one() or 0
        successful = (await self.session.execute(successful_jobs_stmt)).scalar_one() or 0
        failed = (await self.session.execute(failed_jobs_stmt)).scalar_one() or 0
        queued = (await self.session.execute(queued_jobs_stmt)).scalar_one() or 0
        processing = (await self.session.execute(processing_jobs_stmt)).scalar_one() or 0
        docx_count = (await self.session.execute(docx_to_pdf_stmt)).scalar_one() or 0
        pdf_count = (await self.session.execute(pdf_to_docx_stmt)).scalar_one() or 0

        success_rate = round((successful / total_jobs * 100), 1) if total_jobs > 0 else 100.0

        return {
            "total_users": total_users,
            "total_jobs": total_jobs,
            "successful_jobs": successful,
            "failed_jobs": failed,
            "queued_jobs": queued,
            "processing_jobs": processing,
            "docx_to_pdf_count": docx_count,
            "pdf_to_docx_count": pdf_count,
            "success_rate": success_rate,
        }
