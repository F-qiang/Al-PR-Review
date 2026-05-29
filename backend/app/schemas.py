from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class CreateReviewRequest(BaseModel):
    pr_url: str = Field(..., min_length=5, description="GitHub PR URL 或 owner/repo#123")
    github_token: str | None = Field(default=None, description="可选，临时覆盖服务端 GitHub Token")

    @field_validator("pr_url")
    @classmethod
    def validate_pr_url(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("pr_url 不能为空")
        return value

    @field_validator("github_token")
    @classmethod
    def normalize_github_token(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class PullRequestInfo(BaseModel):
    owner: str
    repo: str
    number: int
    title: str
    author: str
    body: str
    url: str
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0


class FileDiff(BaseModel):
    filename: str
    status: str
    patch: str | None = None
    additions: int = 0
    deletions: int = 0


class RiskItem(BaseModel):
    file: str
    line: int | None = None
    severity: Literal["low", "medium", "high", "critical"]
    category: str
    description: str
    suggestion: str
    source: Literal["rule", "llm"] = "llm"


class SuggestionItem(BaseModel):
    category: str
    content: str
    priority: Literal["low", "medium", "high"] = "medium"


class ReviewResult(BaseModel):
    summary: str
    risks: list[RiskItem]
    suggestions: list[SuggestionItem]
    model_name: str
    token_used: int | None = None
    duration_ms: int | None = None


ReviewTaskStatus = Literal["pending", "fetching", "analyzing", "completed", "failed"]
ReviewListStatus = Literal["pending", "fetching", "analyzing", "completed", "failed"]


class ReviewTaskResponse(BaseModel):
    task_id: str
    status: ReviewTaskStatus
    reused: bool = False
    pr: PullRequestInfo | None = None
    result: ReviewResult | None = None
    error_message: str | None = None
    report_url: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class ReviewListItem(BaseModel):
    task_id: str
    status: str
    pr_url: str
    pr_title: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class ReviewListResponse(BaseModel):
    items: list[ReviewListItem]
    total: int
    page: int
    page_size: int
    total_pages: int
    status: ReviewListStatus | None = None


class StreamEvent(BaseModel):
    event: str
    data: dict[str, Any]
