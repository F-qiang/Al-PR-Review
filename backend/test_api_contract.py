from app.schemas import ReviewTaskResponse


def test_review_task_response_default_reused_false() -> None:
    payload = {
        "task_id": "task-1",
        "status": "pending",
        "created_at": "2026-05-30T12:00:00Z",
        "completed_at": None,
    }
    data = ReviewTaskResponse.model_validate(payload)
    assert data.reused is False


def test_review_task_response_accept_reused_true() -> None:
    payload = {
        "task_id": "task-2",
        "status": "fetching",
        "reused": True,
        "created_at": "2026-05-30T12:00:00Z",
        "completed_at": None,
    }
    data = ReviewTaskResponse.model_validate(payload)
    assert data.reused is True
