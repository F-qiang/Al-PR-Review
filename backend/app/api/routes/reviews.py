from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.database import SessionLocal, create_task, get_task, list_tasks
from app.schemas import CreateReviewRequest, PullRequestInfo, ReviewListItem, ReviewListResponse, ReviewResult, ReviewTaskResponse
from app.services.analyzer import stream_events, task_to_response
from app.services.pr_parser import parse_pr_url
from app.services.report import render_markdown_report

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])


async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


@router.post("", response_model=ReviewTaskResponse)
async def create_review(
    body: CreateReviewRequest,
    session: AsyncSession = Depends(get_session),
) -> ReviewTaskResponse:
    try:
        parsed = parse_pr_url(body.pr_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    task = await create_task(
        session,
        pr_url=body.pr_url.strip(),
        owner=parsed.owner,
        repo=parsed.repo,
        number=parsed.number,
        github_token=body.github_token,
    )

    return task_to_response(task)


@router.get("", response_model=ReviewListResponse)
async def get_review_history(session: AsyncSession = Depends(get_session)) -> ReviewListResponse:
    tasks = await list_tasks(session)
    items = [
        ReviewListItem(
            task_id=task.id,
            status=task.status,
            pr_url=task.pr_url,
            pr_title=task.pr_title,
            created_at=task.created_at,
            completed_at=task.completed_at,
        )
        for task in tasks
    ]
    return ReviewListResponse(items=items, total=len(items))


@router.get("/{task_id}", response_model=ReviewTaskResponse)
async def get_review(task_id: str, session: AsyncSession = Depends(get_session)) -> ReviewTaskResponse:
    task = await get_task(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task_to_response(task)


@router.get("/{task_id}/report.md", response_class=PlainTextResponse)
async def download_report(task_id: str, session: AsyncSession = Depends(get_session)) -> PlainTextResponse:
    task = await get_task(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if not task.result_payload or not task.pr_payload:
        raise HTTPException(status_code=404, detail="报告尚未生成")

    markdown = render_markdown_report(
        PullRequestInfo(**task.pr_payload),
        ReviewResult(**task.result_payload),
        task_id=task.id,
        created_at=task.created_at,
    )
    filename = f"pr-review-{task.repo_owner}-{task.repo_name}-{task.pr_number}.md"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return PlainTextResponse(markdown, media_type="text/markdown; charset=utf-8", headers=headers)


@router.get("/{task_id}/stream")
async def stream_review(task_id: str) -> EventSourceResponse:
    return EventSourceResponse(stream_events(task_id))
