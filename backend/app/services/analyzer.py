import asyncio
import json
import time
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any

from app.config import settings
from app.database import SessionLocal, get_task, update_task
from app.schemas import PullRequestInfo, ReviewResult, ReviewTaskResponse
from app.services.event_bus import event_bus
from app.services.github import GitHubError, fetch_pr_files, fetch_pull_request, file_diffs_to_dict
from app.services.llm import LLMError, analyze_with_llm, split_files_into_chunks, total_patch_chars
from app.services.pr_parser import parse_pr_url
from app.services.rules import merge_risks, scan_file_with_rules


def task_to_response(task) -> ReviewTaskResponse:
    pr = PullRequestInfo(**task.pr_payload) if task.pr_payload else None
    result = ReviewResult(**task.result_payload) if task.result_payload else None
    return ReviewTaskResponse(
        task_id=task.id,
        status=task.status,
        pr=pr,
        result=result,
        error_message=task.error_message,
        created_at=task.created_at,
        completed_at=task.completed_at,
    )


def send(task_id: str, event: str, data: dict[str, Any]) -> None:
    event_bus.emit(task_id, event, data)


def _resolve_github_token(task_token: str | None, override: str | None = None) -> str | None:
    return override or task_token or settings.github_token or None


async def run_review_analysis(
    task_id: str,
    pr_url: str,
    github_token: str | None = None,
) -> None:
    if not event_bus.mark_running(task_id):
        return

    started = time.perf_counter()

    try:
        async with SessionLocal() as session:
            task = await get_task(session, task_id)
            if not task:
                return

            effective_token = _resolve_github_token(task.github_token, github_token)

            send(task_id, "status", {"stage": "parsing", "message": "正在解析 PR 地址..."})
            parsed = parse_pr_url(pr_url)

            send(task_id, "status", {"stage": "fetching", "message": "正在从 GitHub 拉取 PR 数据..."})
            await update_task(session, task, status="fetching")
            pr_info = await fetch_pull_request(parsed, effective_token)
            files = await fetch_pr_files(parsed, effective_token)

            await update_task(
                session,
                task,
                pr_title=pr_info.title,
                pr_author=pr_info.author,
                pr_payload=pr_info.model_dump(),
                status="analyzing",
            )

            file_dicts = file_diffs_to_dict(files)
            patch_chars = total_patch_chars(file_dicts)
            chunk_count = len(split_files_into_chunks(file_dicts)) if patch_chars > 48000 else 1

            send(
                task_id,
                "status",
                {
                    "stage": "analyzing",
                    "message": f"已获取 {len(files)} 个变更文件，{'分 ' + str(chunk_count) + ' 批' if chunk_count > 1 else '开始'}分析...",
                    "files_count": len(files),
                    "chunk_count": chunk_count,
                },
            )
            send(
                task_id,
                "pr_info",
                {
                    "title": pr_info.title,
                    "author": pr_info.author,
                    "url": pr_info.url,
                    "owner": pr_info.owner,
                    "repo": pr_info.repo,
                    "number": pr_info.number,
                    "additions": pr_info.additions,
                    "deletions": pr_info.deletions,
                    "changed_files": pr_info.changed_files,
                },
            )

            rule_risks = []
            for file in files:
                rule_risks.extend(scan_file_with_rules(file.filename, file.patch))

            send(
                task_id,
                "status",
                {
                    "stage": "llm",
                    "message": "正在进行 AI 智能分析..." if chunk_count == 1 else f"正在并行分析 {chunk_count} 批变更...",
                },
            )
            llm_result = await analyze_with_llm(pr_info.title, pr_info.body, file_dicts)

            llm_result.risks = merge_risks(rule_risks, llm_result.risks)
            llm_result.duration_ms = int((time.perf_counter() - started) * 1000)

            send(task_id, "summary", {"content": llm_result.summary})
            for risk in llm_result.risks:
                send(task_id, "risk", risk.model_dump())
            for suggestion in llm_result.suggestions:
                send(task_id, "suggestion", suggestion.model_dump())

            await update_task(
                session,
                task,
                status="completed",
                result_payload=llm_result.model_dump(),
                completed_at=datetime.now(timezone.utc),
            )
            send(
                task_id,
                "done",
                {
                    "task_id": task_id,
                    "duration_ms": llm_result.duration_ms,
                    "risk_count": len(llm_result.risks),
                    "suggestion_count": len(llm_result.suggestions),
                    "chunk_count": chunk_count,
                },
            )
    except (GitHubError, LLMError, ValueError) as exc:
        async with SessionLocal() as session:
            task = await get_task(session, task_id)
            if task:
                await update_task(
                    session,
                    task,
                    status="failed",
                    error_message=str(exc),
                    completed_at=datetime.now(timezone.utc),
                )
        send(task_id, "error", {"message": str(exc)})
    except Exception as exc:  # noqa: BLE001
        async with SessionLocal() as session:
            task = await get_task(session, task_id)
            if task:
                await update_task(
                    session,
                    task,
                    status="failed",
                    error_message=f"分析失败: {exc}",
                    completed_at=datetime.now(timezone.utc),
                )
        send(task_id, "error", {"message": f"分析失败: {exc}"})
    finally:
        event_bus.mark_done(task_id)


async def stream_events(task_id: str) -> AsyncIterator[dict[str, str]]:
    async with SessionLocal() as session:
        task = await get_task(session, task_id)
        if not task:
            yield {"event": "error", "data": json.dumps({"message": "任务不存在"}, ensure_ascii=False)}
            return

        if task.status == "completed" and task.result_payload:
            result = ReviewResult(**task.result_payload)
            if task.pr_payload:
                yield {
                    "event": "pr_info",
                    "data": json.dumps(task.pr_payload, ensure_ascii=False),
                }
            yield {
                "event": "summary",
                "data": json.dumps({"content": result.summary}, ensure_ascii=False),
            }
            for risk in result.risks:
                yield {"event": "risk", "data": json.dumps(risk.model_dump(), ensure_ascii=False)}
            for suggestion in result.suggestions:
                yield {
                    "event": "suggestion",
                    "data": json.dumps(suggestion.model_dump(), ensure_ascii=False),
                }
            yield {
                "event": "done",
                "data": json.dumps(
                    {
                        "task_id": task_id,
                        "cached": True,
                        "duration_ms": result.duration_ms,
                    },
                    ensure_ascii=False,
                ),
            }
            return

        if task.status == "failed":
            yield {
                "event": "error",
                "data": json.dumps({"message": task.error_message or "分析失败"}, ensure_ascii=False),
            }
            return

        task_pr_url = task.pr_url
        task_github_token = task.github_token

    queue = event_bus.get_queue(task_id)
    worker = asyncio.create_task(run_review_analysis(task_id, task_pr_url, task_github_token))

    while True:
        item = await queue.get()
        if item is None:
            break
        event, data = item
        yield {"event": event, "data": json.dumps(data, ensure_ascii=False)}
        if event in {"done", "error"}:
            break

    await worker
