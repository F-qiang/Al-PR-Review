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


def prioritize_files(files: list[dict[str, Any]], max_chars: int = 48000) -> list[dict[str, Any]]:
    def score(item: dict[str, Any]) -> tuple[int, int]:
        ext = "." + item["filename"].split(".")[-1] if "." in item["filename"] else ""
        code_bonus = 0 if ext in CODE_EXTENSIONS else 1
        return (code_bonus, -(item.get("additions", 0) + item.get("deletions", 0)))

    sorted_files = sorted(files, key=score)
    selected: list[dict[str, Any]] = []
    total = 0

    for item in sorted_files:
        patch = item.get("patch") or ""
        chunk_len = len(item["filename"]) + len(patch) + 64
        if total + chunk_len > max_chars and selected:
            break
        selected.append(item)
        total += chunk_len

    return selected or sorted_files[:5]


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


async def analyze_with_llm(
    pr_title: str,
    pr_body: str,
    files: list[dict[str, Any]],
) -> ReviewResult:
    if not settings.llm_api_key:
        raise LLMError("未配置 LLM_API_KEY，请在 backend/.env 中设置")

    selected_files = prioritize_files(files)
    user_prompt = build_user_prompt(pr_title, pr_body, selected_files)

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
    parsed = extract_json(content)

    risks = [RiskItem(**item, source="llm") for item in parsed.get("risks", [])]
    suggestions = [SuggestionItem(**item) for item in parsed.get("suggestions", [])]
    token_used = data.get("usage", {}).get("total_tokens")

    return ReviewResult(
        summary=parsed.get("summary", "未能生成摘要"),
        risks=risks,
        suggestions=suggestions,
        model_name=settings.llm_model,
        token_used=token_used,
    )
