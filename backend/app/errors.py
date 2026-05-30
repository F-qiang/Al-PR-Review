from dataclasses import dataclass

from fastapi import HTTPException


@dataclass(frozen=True)
class ErrorCode:
    code: str
    message: str


VALIDATION_ERROR = ErrorCode("VALIDATION_ERROR", "请求参数不合法")
NOT_FOUND = ErrorCode("NOT_FOUND", "资源不存在")
BAD_REQUEST = ErrorCode("BAD_REQUEST", "请求不合法")
UNAUTHORIZED = ErrorCode("UNAUTHORIZED", "未授权请求")


def api_error(status_code: int, error: ErrorCode, detail: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "code": error.code,
            "message": error.message,
            "detail": detail,
        },
    )
