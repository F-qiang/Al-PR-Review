import re
from typing import Any

from app.schemas import RiskItem

RULE_PATTERNS: list[tuple[str, str, str, re.Pattern[str]]] = [
    (
        "security",
        "high",
        "检测到可能的硬编码密钥或 Token",
        re.compile(
            r"(?i)(api[_-]?key|secret|password|token|private[_-]?key)\s*[:=]\s*['\"][^'\"]{8,}['\"]"
        ),
    ),
    (
        "security",
        "high",
        "检测到 SQL 字符串拼接，可能存在 SQL 注入风险",
        re.compile(r"(?i)(execute|query|raw)\s*\(\s*f?['\"].*\{.*\}.*['\"]"),
    ),
    (
        "security",
        "medium",
        "使用了 eval/exec，存在代码注入风险",
        re.compile(r"\b(eval|exec)\s*\("),
    ),
    (
        "security",
        "medium",
        "检测到禁用 TLS 证书验证",
        re.compile(r"verify\s*=\s*False"),
    ),
    (
        "logic",
        "medium",
        "捕获了过于宽泛的异常，可能掩盖真实错误",
        re.compile(r"except\s*:\s*$|except\s+Exception\s*:\s*$"),
    ),
]


def scan_file_with_rules(filename: str, patch: str | None) -> list[RiskItem]:
    if not patch:
        return []

    risks: list[RiskItem] = []
    current_line: int | None = None

    for line in patch.splitlines():
        if line.startswith("@@"):
            match = re.search(r"\+(\d+)", line)
            current_line = int(match.group(1)) if match else None
            continue

        if not line.startswith("+") or line.startswith("+++"):
            if line.startswith("-") and not line.startswith("---"):
                continue
            if current_line is not None and not line.startswith("-"):
                current_line += 1
            continue

        content = line[1:]
        for category, severity, description, pattern in RULE_PATTERNS:
            if pattern.search(content):
                risks.append(
                    RiskItem(
                        file=filename,
                        line=current_line,
                        severity=severity,  # type: ignore[arg-type]
                        category=category,
                        description=description,
                        suggestion="请审查该行变更，确认是否存在真实风险并修复",
                        source="rule",
                    )
                )
                break

        if current_line is not None:
            current_line += 1

    return risks


def merge_risks(rule_risks: list[RiskItem], llm_risks: list[RiskItem]) -> list[RiskItem]:
    merged = list(rule_risks)
    seen = {(item.file, item.line, item.category, item.description[:40]) for item in rule_risks}

    for risk in llm_risks:
        key = (risk.file, risk.line, risk.category, risk.description[:40])
        if key not in seen:
            merged.append(risk)
            seen.add(key)

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    merged.sort(key=lambda item: severity_order.get(item.severity, 99))
    return merged
