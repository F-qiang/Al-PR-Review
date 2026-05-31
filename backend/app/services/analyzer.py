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
from app.services.github import GitHubError, fetch_pr_files, fetch_pull_request, file_diffs_to_dict, post_pr_comment
from app.services.llm import LLMError, analyze_with_llm, split_files_into_chunks, total_patch_chars
from app.services.pr_parser import parse_pr_url
from app.services.qiniu_storage import QiniuStorageError, is_qiniu_configured, upload_report
from app.services.report import render_markdown_report, render_pr_comment
from app.services.rules import merge_risks, scan_file_with_rules


def task_to_response(task, *, reused: bool = False) -> ReviewTaskResponse:
    pr = PullRequestInfo(**task.pr_payload) if task.pr_payload else None
    result = ReviewResult(**task.result_payload) if task.result_payload else None
    return ReviewTaskResponse(
        task_id=task.id,
        status=task.status,
        reused=reused,
        pr=pr,
        result=result,
        error_message=task.error_message,
        report_url=task.report_url,
        created_at=task.created_at,
        completed_at=task.completed_at,
    )


def send(task_id: str, event: str, data: dict[str, Any]) -> None:
    event_bus.emit(task_id, event, data)


def _resolve_github_token(task_token: str | None, override: str | None = None) -> str | None:
    return override or task_token or settings.github_token or None


async def _upload_report_if_configured(
    task_id: str,
    pr_info: PullRequestInfo,
    result: ReviewResult,
    created_at: datetime,
) -> str | None:
    if not is_qiniu_configured():
        return None

    markdown = render_markdown_report(pr_info, result, task_id=task_id, created_at=created_at)
    object_key = f"reports/{pr_info.owner}/{pr_info.repo}/pr-{pr_info.number}-{task_id[:8]}.md"
    return await upload_report(object_key, markdown)


async def _emit_demo_result(task_id: str, task_pr_url: str) -> None:
    parsed = parse_pr_url(task_pr_url)
    pr_info = PullRequestInfo(
        owner=parsed.owner,
        repo=parsed.repo,
        number=parsed.number,
        title="[演示模式] 示例 PR 评审结果",
        author="demo-bot",
        body="演示模式下的固定 PR 数据，用于稳定展示 UI 与流程。",
        url=task_pr_url,
        additions=12,
        deletions=4,
        changed_files=3,
    )
    result = ReviewResult(
        summary="这是演示模式返回的模拟评审结果，用于在网络不稳定或无 GitHub/LLM 资源时稳定展示项目流程。",
        risks=[],
        suggestions=[
            {
                "category": "demo",
                "content": "演示模式已启用，后续可切换回真实分析流程。",
                "priority": "low",
            }
        ],
        model_name="demo-mode",
        token_used=0,
        duration_ms=1200,
    )
    # 兼容 pydantic 模型
    result = ReviewResult.model_validate(result.model_dump())

    send(task_id, "status", {"stage": "demo", "message": "当前处于演示模式，返回固定评审结果..."})
    send(task_id, "pr_info", pr_info.model_dump())
    send(task_id, "summary", {"content": result.summary})
    for suggestion in result.suggestions:
        send(task_id, "suggestion", suggestion.model_dump())

    send(
        task_id,
        "done",
        {
            "task_id": task_id,
            "duration_ms": result.duration_ms,
            "risk_count": len(result.risks),
            "suggestion_count": len(result.suggestions),
            "report_url": None,
            "comment_url": None,
            "chunk_count": 1,
            "model_name": result.model_name,
            "reused": False,
            "demo_mode": True,
        },
    )


async def run_review_analysis(
    task_id: str,
    pr_url: str,
    github_token: str | None = None,
) -> None:
    if not event_bus.mark_running(task_id):
        return

    started = time.perf_counter()

    try:
        if settings.demo_mode:
            await _emit_demo_result(task_id, pr_url)
            return

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

            report_url = None
            try:
                report_url = await _upload_report_if_configured(
                    task_id,
                    pr_info,
                    llm_result,
                    task.created_at,
                )
            except QiniuStorageError as exc:
                send(task_id, "status", {"stage": "upload", "message": f"报告上传跳过：{exc}"})

            comment_url = None
            if settings.github_auto_comment and effective_token:
                try:
                    send(task_id, "status", {"stage": "comment", "message": "正在发布 PR 评论..."})
                    comment_body = render_pr_comment(pr_info, llm_result, report_url=report_url)
                    comment_url = await post_pr_comment(parsed, comment_body, effective_token)
                except GitHubError as exc:
                    send(task_id, "status", {"stage": "comment", "message": f"PR 评论跳过：{exc}"})

            await update_task(
                session,
                task,
                status="completed",
                result_payload=llm_result.model_dump(),
                report_url=report_url,
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
                    "report_url": report_url,
                    "comment_url": comment_url,
                    "chunk_count": chunk_count,
                    "model_name": llm_result.model_name,
                    "reused": False,
                    "demo_mode": False,
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
                        "report_url": task.report_url,
                        "duration_ms": result.duration_ms,
                        "model_name": result.model_name,
                        "reused": True,
                        "demo_mode": settings.demo_mode,
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
