from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class CreateReviewRequest(BaseModel):
    pr_url: str = Field(..., description="GitHub PR URL 或 owner/repo#123")
    github_token: str | None = None


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


class ReviewTaskResponse(BaseModel):
    task_id: str
    status: str
    pr: PullRequestInfo | None = None
    result: ReviewResult | None = None
    error_message: str | None = None
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


class StreamEvent(BaseModel):
    event: str
    data: dict[str, Any]
