import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.database.models import Base
from app.database.repository import Repository

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def async_session():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_user_and_job_lifecycle(async_session: AsyncSession):
    repo = Repository(async_session)

    # 1. User registration
    user = await repo.get_or_create_user(
        telegram_id=12345678,
        username="john_doe",
        first_name="John",
        last_name="Doe",
    )
    assert user.id is not None
    assert user.telegram_id == 12345678

    # 2. Create Job
    job = await repo.create_job(
        user_id=user.id,
        job_uuid="test-uuid-1",
        input_filename="proposal.docx",
        output_filename="proposal.pdf",
        input_format="docx",
        output_format="pdf",
        input_size=1024 * 50,
    )
    assert job.status == "queued"
    assert job.job_uuid == "test-uuid-1"

    # 3. Update Job to Processing
    await repo.update_job_status("test-uuid-1", status="processing")
    job = await repo.get_job_by_uuid("test-uuid-1")
    assert job.status == "processing"
    assert job.processing_started_at is not None

    # 4. Update Job to Completed
    await repo.update_job_status("test-uuid-1", status="completed")
    job = await repo.get_job_by_uuid("test-uuid-1")
    assert job.status == "completed"
    assert job.processing_finished_at is not None

    # Check user stats
    stats = await repo.get_user_job_stats(12345678)
    assert stats["completed"] == 1
    assert stats["failed"] == 0

    # 5. Cancel Queued Jobs
    await repo.create_job(
        user_id=user.id,
        job_uuid="test-uuid-2",
        input_filename="draft.pdf",
        output_filename="draft.docx",
        input_format="pdf",
        output_format="docx",
        input_size=1024 * 20,
    )
    cancelled = await repo.cancel_user_queued_jobs(12345678)
    assert cancelled == 1

    job2 = await repo.get_job_by_uuid("test-uuid-2")
    assert job2.status == "cancelled"

    # 6. Admin metrics
    metrics = await repo.get_admin_metrics()
    assert metrics["total_users"] == 1
    assert metrics["total_jobs"] == 2
    assert metrics["successful_jobs"] == 1
