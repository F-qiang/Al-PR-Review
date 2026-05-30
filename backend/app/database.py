import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import JSON, DateTime, Index, Integer, String, Text, and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import settings


class Base(DeclarativeBase):
    pass


class ReviewTaskModel(Base):
    __tablename__ = "review_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    pr_url: Mapped[str] = mapped_column(Text, nullable=False)
    repo_owner: Mapped[str] = mapped_column(String(128), nullable=False)
    repo_name: Mapped[str] = mapped_column(String(256), nullable=False)
    pr_number: Mapped[int] = mapped_column(Integer, nullable=False)
    pr_title: Mapped[str | None] = mapped_column(Text)
    pr_author: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    error_message: Mapped[str | None] = mapped_column(Text)
    github_token: Mapped[str | None] = mapped_column(Text)
    report_url: Mapped[str | None] = mapped_column(Text)
    pr_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    result_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


engine = create_async_engine(settings.database_url, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _migrate_schema(conn)


async def _migrate_schema(conn) -> None:
    result = await conn.execute(text("PRAGMA table_info(review_tasks)"))
    columns = {row[1] for row in result.fetchall()}
    if "github_token" not in columns:
        await conn.execute(text("ALTER TABLE review_tasks ADD COLUMN github_token TEXT"))
    if "report_url" not in columns:
        await conn.execute(text("ALTER TABLE review_tasks ADD COLUMN report_url TEXT"))


async def find_recent_active_task(
    session: AsyncSession,
    *,
    owner: str,
    repo: str,
    number: int,
    within_seconds: int = 180,
) -> ReviewTaskModel | None:
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=within_seconds)
    result = await session.execute(
        select(ReviewTaskModel)
        .where(
            and_(
                ReviewTaskModel.repo_owner == owner,
                ReviewTaskModel.repo_name == repo,
                ReviewTaskModel.pr_number == number,
                or_(ReviewTaskModel.status.in_(["pending", "fetching", "analyzing"]), ReviewTaskModel.created_at >= cutoff),
            )
        )
        .order_by(ReviewTaskModel.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def create_task(
    session: AsyncSession,
    *,
    pr_url: str,
    owner: str,
    repo: str,
    number: int,
    github_token: str | None = None,
) -> ReviewTaskModel:
    task = ReviewTaskModel(
        id=str(uuid.uuid4()),
        pr_url=pr_url,
        repo_owner=owner,
        repo_name=repo,
        pr_number=number,
        github_token=github_token,
        status="pending",
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


async def get_task(session: AsyncSession, task_id: str) -> ReviewTaskModel | None:
    result = await session.execute(select(ReviewTaskModel).where(ReviewTaskModel.id == task_id))
    return result.scalar_one_or_none()


async def list_tasks(
    session: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
) -> tuple[list[ReviewTaskModel], int]:
    offset = (page - 1) * page_size
    base_query = select(ReviewTaskModel)
    total_query = select(func.count()).select_from(ReviewTaskModel)

    if status:
        base_query = base_query.where(ReviewTaskModel.status == status)
        total_query = total_query.where(ReviewTaskModel.status == status)

    total = await session.scalar(total_query)
    result = await session.execute(
        base_query.order_by(ReviewTaskModel.created_at.desc()).offset(offset).limit(page_size)
    )
    return list(result.scalars().all()), int(total or 0)


async def update_task(
    session: AsyncSession,
    task: ReviewTaskModel,
    **fields: Any,
) -> ReviewTaskModel:
    for key, value in fields.items():
        setattr(task, key, value)
    await session.commit()
    await session.refresh(task)
    return task
