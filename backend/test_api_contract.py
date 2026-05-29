from app.schemas import ReviewListResponse, ReviewTaskResponse


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


def test_review_list_response_accept_valid_status() -> None:
    payload = {
        "items": [],
        "total": 0,
        "page": 1,
        "page_size": 20,
        "total_pages": 0,
        "status": "completed",
    }
    data = ReviewListResponse.model_validate(payload)
    assert data.status == "completed"


def test_review_list_response_reject_invalid_status() -> None:
    payload = {
        "items": [],
        "total": 0,
        "page": 1,
        "page_size": 20,
        "total_pages": 0,
        "status": "running",
    }
    try:
        ReviewListResponse.model_validate(payload)
        assert False, "应当抛出状态枚举校验错误"
    except Exception as exc:  # noqa: BLE001
        assert "pending" in str(exc)
