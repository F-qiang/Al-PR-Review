from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_get_reviews_reject_invalid_status_param() -> None:
    response = client.get("/api/v1/reviews", params={"status": "running"})
    assert response.status_code == 422
    body = response.json()
    assert body["message"] == "请求参数不合法"


def test_create_review_reuse_existing_task(monkeypatch) -> None:
    parsed = SimpleNamespace(owner="octocat", repo="hello", number=1)
    task = SimpleNamespace(
        id="task-1",
        status="pending",
        pr_payload=None,
        result_payload=None,
        error_message=None,
        report_url=None,
        created_at="2026-05-30T12:00:00Z",
        completed_at=None,
    )

    async def fake_parse_pr_url(pr_url: str):
        _ = pr_url
        return parsed

    async def fake_find_recent_active_task(session, *, owner: str, repo: str, number: int):
        _ = (session, owner, repo, number)
        return task

    async def fake_create_task(*args, **kwargs):
        raise AssertionError("命中复用时不应创建新任务")

    monkeypatch.setattr("app.api.routes.reviews.parse_pr_url", lambda pr_url: parsed)
    monkeypatch.setattr("app.api.routes.reviews.find_recent_active_task", fake_find_recent_active_task)
    monkeypatch.setattr("app.api.routes.reviews.create_task", fake_create_task)

    response = client.post("/api/v1/reviews", json={"pr_url": "https://github.com/octocat/hello/pull/1"})
    assert response.status_code == 200
    body = response.json()
    assert body["task_id"] == "task-1"
    assert body["reused"] is True
