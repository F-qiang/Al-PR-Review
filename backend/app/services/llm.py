import asyncio
import json
import re
from typing import Any

import httpx

from app.config import settings
from app.prompts.review import SYSTEM_PROMPT, build_user_prompt
from app.schemas import ReviewResult, RiskItem, SuggestionItem


class LLMError(Exception):
    pass


CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".go",
    ".java",
    ".rs",
    ".cpp",
    ".c",
    ".h",
    ".cs",
    ".rb",
    ".php",
    ".swift",
    ".kt",
}

SINGLE_CALL_MAX_CHARS = 48000
CHUNK_MAX_CHARS = 16000
PARALLEL_LIMIT = 3


def _file_size(item: dict[str, Any]) -> int:
    return len(item.get("filename", "")) + len(item.get("patch") or "") + 64


def _file_score(item: dict[str, Any]) -> tuple[int, int]:
    filename = item.get("filename", "")
    ext = "." + filename.split(".")[-1] if "." in filename else ""
    code_bonus = 0 if ext in CODE_EXTENSIONS else 1
    changes = item.get("additions", 0) + item.get("deletions", 0)
    return (code_bonus, -changes)


def sort_files(files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(files, key=_file_score)


def prioritize_files(files: list[dict[str, Any]], max_chars: int = SINGLE_CALL_MAX_CHARS) -> list[dict[str, Any]]:
    sorted_files = sort_files(files)
    selected: list[dict[str, Any]] = []
    total = 0

    for item in sorted_files:
        chunk_len = _file_size(item)
        if total + chunk_len > max_chars and selected:
            break
        selected.append(item)
        total += chunk_len

    return selected or sorted_files[:5]


def split_files_into_chunks(
    files: list[dict[str, Any]],
    max_chars: int = CHUNK_MAX_CHARS,
) -> list[list[dict[str, Any]]]:
    sorted_files = sort_files(files)
    chunks: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_size = 0

    for item in sorted_files:
        size = _file_size(item)
        if current and current_size + size > max_chars:
            chunks.append(current)
            current = [item]
            current_size = size
        else:
            current.append(item)
            current_size += size

    if current:
        chunks.append(current)

    return chunks


def total_patch_chars(files: list[dict[str, Any]]) -> int:
    return sum(_file_size(item) for item in files)


def extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise LLMError("LLM 返回内容无法解析为 JSON") from None
        return json.loads(match.group())


async def _call_llm(user_prompt: str) -> tuple[dict[str, Any], int | None]:
    if not settings.llm_api_key:
        raise LLMError("未配置 LLM_API_KEY，请在 backend/.env 中设置")

    payload = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }

    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{settings.llm_base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    content = data["choices"][0]["message"]["content"]
    token_used = data.get("usage", {}).get("total_tokens")
    return extract_json(content), token_used


def _parse_llm_result(parsed: dict[str, Any]) -> ReviewResult:
    risks = [RiskItem(**item, source="llm") for item in parsed.get("risks", [])]
    suggestions = [SuggestionItem(**item) for item in parsed.get("suggestions", [])]
    return ReviewResult(
        summary=parsed.get("summary", "未能生成摘要"),
        risks=risks,
        suggestions=suggestions,
        model_name=settings.llm_model,
    )


def _merge_chunk_results(results: list[ReviewResult]) -> ReviewResult:
    if not results:
        return ReviewResult(summary="未能生成摘要", risks=[], suggestions=[], model_name=settings.llm_model)

    if len(results) == 1:
        return results[0]

    summaries = [item.summary for item in results if item.summary]
    merged_summary = "\n\n".join(f"- {text}" for text in summaries)

    seen_risks: set[tuple[str, int | None, str, str]] = set()
    merged_risks: list[RiskItem] = []
    for result in results:
        for risk in result.risks:
            key = (risk.file, risk.line, risk.category, risk.description[:60])
            if key not in seen_risks:
                seen_risks.add(key)
                merged_risks.append(risk)

    seen_suggestions: set[tuple[str, str]] = set()
    merged_suggestions: list[SuggestionItem] = []
    for result in results:
        for suggestion in result.suggestions:
            key = (suggestion.category, suggestion.content[:80])
            if key not in seen_suggestions:
                seen_suggestions.add(key)
                merged_suggestions.append(suggestion)

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    merged_risks.sort(key=lambda item: severity_order.get(item.severity, 99))

    total_tokens = sum(item.token_used or 0 for item in results) or None

    return ReviewResult(
        summary=merged_summary,
        risks=merged_risks,
        suggestions=merged_suggestions,
        model_name=settings.llm_model,
        token_used=total_tokens,
    )


async def _analyze_batch(
    pr_title: str,
    pr_body: str,
    files: list[dict[str, Any]],
    *,
    chunk_index: int | None = None,
    chunk_total: int | None = None,
) -> ReviewResult:
    prefix = ""
    if chunk_index is not None and chunk_total is not None:
        prefix = f"【注意：这是 PR 变更的第 {chunk_index}/{chunk_total} 批文件，请仅分析本批文件】\n\n"

    user_prompt = prefix + build_user_prompt(pr_title, pr_body, files)
    parsed, token_used = await _call_llm(user_prompt)
    result = _parse_llm_result(parsed)
    result.token_used = token_used
    return result


async def analyze_with_llm(
    pr_title: str,
    pr_body: str,
    files: list[dict[str, Any]],
) -> ReviewResult:
    if total_patch_chars(files) <= SINGLE_CALL_MAX_CHARS:
        selected_files = prioritize_files(files, SINGLE_CALL_MAX_CHARS)
        return await _analyze_batch(pr_title, pr_body, selected_files)

    chunks = split_files_into_chunks(files)
    semaphore = asyncio.Semaphore(PARALLEL_LIMIT)

    async def run_chunk(index: int, chunk_files: list[dict[str, Any]]) -> ReviewResult:
        async with semaphore:
            return await _analyze_batch(
                pr_title,
                pr_body,
                chunk_files,
                chunk_index=index,
                chunk_total=len(chunks),
            )

    chunk_results = await asyncio.gather(*(run_chunk(index + 1, chunk) for index, chunk in enumerate(chunks)))
    return _merge_chunk_results(list(chunk_results))
