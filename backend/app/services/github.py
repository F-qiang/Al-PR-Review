from typing import Any

import httpx

from app.config import settings
from app.schemas import FileDiff, PullRequestInfo
from app.services.pr_parser import ParsedPR


class GitHubError(Exception):
    pass


def build_headers(token: str | None = None) -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    effective_token = token or settings.github_token
    if effective_token:
        headers["Authorization"] = f"Bearer {effective_token}"
    return headers


async def fetch_pull_request(parsed: ParsedPR, token: str | None = None) -> PullRequestInfo:
    base = f"https://api.github.com/repos/{parsed.owner}/{parsed.repo}"
    headers = build_headers(token)

    async with httpx.AsyncClient(timeout=30.0) as client:
        pr_resp = await client.get(f"{base}/pulls/{parsed.number}", headers=headers)
        if pr_resp.status_code == 404:
            raise GitHubError("PR 不存在或无权访问，请检查链接或配置 GitHub Token")
        pr_resp.raise_for_status()
        pr_data = pr_resp.json()

    return PullRequestInfo(
        owner=parsed.owner,
        repo=parsed.repo,
        number=parsed.number,
        title=pr_data.get("title", ""),
        author=pr_data.get("user", {}).get("login", "unknown"),
        body=pr_data.get("body") or "",
        url=pr_data.get("html_url", ""),
        additions=pr_data.get("additions", 0),
        deletions=pr_data.get("deletions", 0),
        changed_files=pr_data.get("changed_files", 0),
    )


async def fetch_pr_files(parsed: ParsedPR, token: str | None = None) -> list[FileDiff]:
    base = f"https://api.github.com/repos/{parsed.owner}/{parsed.repo}"
    headers = build_headers(token)
    files: list[FileDiff] = []
    page = 1

    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            resp = await client.get(
                f"{base}/pulls/{parsed.number}/files",
                headers=headers,
                params={"per_page": 100, "page": page},
            )
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break

            for item in batch:
                files.append(
                    FileDiff(
                        filename=item.get("filename", ""),
                        status=item.get("status", "modified"),
                        patch=item.get("patch"),
                        additions=item.get("additions", 0),
                        deletions=item.get("deletions", 0),
                    )
                )

            if len(batch) < 100:
                break
            page += 1

    return files


def file_diffs_to_dict(files: list[FileDiff]) -> list[dict[str, Any]]:
    return [file.model_dump() for file in files]


async def post_pr_comment(
    parsed: ParsedPR,
    body: str,
    token: str | None = None,
) -> str:
    effective_token = token or settings.github_token
    if not effective_token:
        raise GitHubError("未配置 GitHub Token，无法发布 PR 评论")

    url = f"https://api.github.com/repos/{parsed.owner}/{parsed.repo}/issues/{parsed.number}/comments"
    headers = build_headers(effective_token)

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=headers, json={"body": body})
        if response.status_code == 403:
            raise GitHubError("GitHub Token 权限不足，需要 repo 或 pull_requests 写权限")
        response.raise_for_status()
        data = response.json()

    return data.get("html_url", "")
