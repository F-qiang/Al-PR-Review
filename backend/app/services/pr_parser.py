import re
from dataclasses import dataclass


@dataclass
class ParsedPR:
    owner: str
    repo: str
    number: int


def parse_pr_url(raw: str) -> ParsedPR:
    text = raw.strip()

    url_match = re.match(
        r"https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)",
        text,
        re.IGNORECASE,
    )
    if url_match:
        return ParsedPR(
            owner=url_match.group("owner"),
            repo=url_match.group("repo"),
            number=int(url_match.group("number")),
        )

    short_match = re.match(
        r"(?P<owner>[^/\s#]+)/(?P<repo>[^/\s#]+)#(?P<number>\d+)",
        text,
    )
    if short_match:
        return ParsedPR(
            owner=short_match.group("owner"),
            repo=short_match.group("repo"),
            number=int(short_match.group("number")),
        )

    raise ValueError("无法解析 PR 地址，请使用 GitHub PR 链接或 owner/repo#123 格式")
