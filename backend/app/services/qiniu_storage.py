import base64
import hashlib
import hmac
import time
from urllib.parse import quote

import httpx

from app.config import settings


class QiniuStorageError(Exception):
    pass


def is_qiniu_configured() -> bool:
    return bool(
        settings.qiniu_access_key
        and settings.qiniu_secret_key
        and settings.qiniu_bucket
    )


def _upload_token(key: str, expires: int = 3600) -> str:
    deadline = int(time.time()) + expires
    put_policy = (
        f'{{"scope":"{settings.qiniu_bucket}:{key}","deadline":{deadline}}}'
    )
    encoded_policy = base64.urlsafe_b64encode(put_policy.encode()).decode()
    sign = hmac.new(
        settings.qiniu_secret_key.encode(),
        encoded_policy.encode(),
        hashlib.sha1,
    ).digest()
    encoded_sign = base64.urlsafe_b64encode(sign).decode()
    return f"{settings.qiniu_access_key}:{encoded_sign}:{encoded_policy}"


def _public_url(key: str) -> str:
    domain = settings.qiniu_domain.rstrip("/")
    safe_key = quote(key, safe="/")
    return f"{domain}/{safe_key}"


async def upload_report(key: str, content: str, content_type: str = "text/markdown") -> str:
    if not is_qiniu_configured():
        raise QiniuStorageError("未配置七牛云存储，请在 backend/.env 中设置 QINIU_* 变量")

    token = _upload_token(key)
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://upload.qiniup.com",
            data={"token": token, "key": key},
            files={"file": (key.split("/")[-1], content.encode("utf-8"), content_type)},
        )
        if response.status_code >= 400:
            raise QiniuStorageError(f"七牛云上传失败：{response.text}")
        payload = response.json()

    uploaded_key = payload.get("key", key)
    return _public_url(uploaded_key)
