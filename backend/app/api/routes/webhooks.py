import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import SessionLocal, create_task
from app.schemas import ReviewTaskResponse
from app.services.analyzer import run_review_analysis, task_to_response
from app.services.github_webhook import parse_pull_request_event, verify_signature
from app.services.pr_parser import parse_pr_url

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


@router.post("/github")
async def github_webhook(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    payload_bytes = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")

    if not verify_signature(payload_bytes, signature, settings.github_webhook_secret):
        raise HTTPException(status_code=401, detail="Webhook 签名校验失败")

    event = request.headers.get("X-GitHub-Event", "")
    if event != "pull_request":
        return JSONResponse({"message": "已忽略非 pull_request 事件"})

    payload = json.loads(payload_bytes)
    pr_data = parse_pull_request_event(payload)
    if not pr_data:
        return JSONResponse({"message": "已忽略该 PR 动作"})

    try:
        parsed = parse_pr_url(pr_data["pr_url"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    task = await create_task(
        session,
        pr_url=pr_data["pr_url"],
        owner=parsed.owner,
        repo=parsed.repo,
        number=parsed.number,
        github_token=settings.github_token or None,
    )

    asyncio.create_task(run_review_analysis(task.id, task.pr_url, settings.github_token or None))
    response: ReviewTaskResponse = task_to_response(task)
    return JSONResponse(response.model_dump(mode="json"))
