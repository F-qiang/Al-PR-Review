import hashlib
import hmac
from typing import Any


def verify_signature(payload: bytes, signature: str | None, secret: str) -> bool:
    if not secret:
        return True
    if not signature or not signature.startswith("sha256="):
        return False

    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    received = signature.removeprefix("sha256=")
    return hmac.compare_digest(expected, received)


def parse_pull_request_event(payload: dict[str, Any]) -> dict[str, str] | None:
    if payload.get("action") not in {"opened", "synchronize", "reopened"}:
        return None

    pull_request = payload.get("pull_request")
    if not pull_request:
        return None

    html_url = pull_request.get("html_url")
    if not html_url:
        return None

    return {
        "pr_url": html_url,
        "title": pull_request.get("title", ""),
        "author": (pull_request.get("user") or {}).get("login", "unknown"),
    }
