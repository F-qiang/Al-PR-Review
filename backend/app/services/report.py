from datetime import datetime

from app.schemas import PullRequestInfo, ReviewResult

MAX_COMMENT_RISKS = 5
MAX_COMMENT_SUGGESTIONS = 3


def render_markdown_report(
    pr: PullRequestInfo,
    result: ReviewResult,
    *,
    task_id: str,
    created_at: datetime | None = None,
) -> str:
    lines = [
        f"# PR Review 报告",
        "",
        f"- **仓库**：{pr.owner}/{pr.repo}",
        f"- **PR**：#{pr.number} {pr.title}",
        f"- **作者**：{pr.author}",
        f"- **链接**：{pr.url}",
        f"- **变更**：+{pr.additions} / -{pr.deletions}，{pr.changed_files} 个文件",
        f"- **模型**：{result.model_name}",
    ]

    if result.duration_ms:
        lines.append(f"- **耗时**：{result.duration_ms} ms")
    if created_at:
        lines.append(f"- **分析时间**：{created_at.isoformat()}")
    lines.append(f"- **任务 ID**：{task_id}")
    lines.extend(["", "## 变更摘要", "", result.summary, "", "## 风险识别", ""])

    if not result.risks:
        lines.append("未发现明显风险。")
    else:
        for index, risk in enumerate(result.risks, start=1):
            location = f"{risk.file}:{risk.line}" if risk.line else risk.file
            lines.extend(
                [
                    f"### {index}. [{risk.severity.upper()}] {location}",
                    "",
                    f"- **类别**：{risk.category}",
                    f"- **来源**：{'规则引擎' if risk.source == 'rule' else 'AI 分析'}",
                    f"- **描述**：{risk.description}",
                    f"- **建议**：{risk.suggestion}",
                    "",
                ]
            )

    lines.extend(["## Review 建议", ""])

    if not result.suggestions:
        lines.append("暂无额外建议。")
    else:
        for index, item in enumerate(result.suggestions, start=1):
            lines.append(f"{index}. **[{item.category}]** ({item.priority}) {item.content}")

    lines.append("")
    return "\n".join(lines)


def render_pr_comment(
    pr: PullRequestInfo,
    result: ReviewResult,
    *,
    report_url: str | None = None,
) -> str:
    """生成适合贴在 PR 下的精简评论。"""
    lines = [
        "## 🤖 AI PR Review",
        "",
        "### 变更摘要",
        result.summary,
        "",
    ]

    high_risks = [risk for risk in result.risks if risk.severity in {"critical", "high"}]
    display_risks = high_risks[:MAX_COMMENT_RISKS] or result.risks[:MAX_COMMENT_RISKS]

    lines.append("### 风险识别")
    if not display_risks:
        lines.append("未发现明显高风险项。")
    else:
        for risk in display_risks:
            location = f"`{risk.file}`" + (f":{risk.line}" if risk.line else "")
            lines.append(f"- **[{risk.severity}]** {location} — {risk.description}")

    lines.extend(["", "### Review 建议"])
    if not result.suggestions:
        lines.append("暂无额外建议。")
    else:
        for item in result.suggestions[:MAX_COMMENT_SUGGESTIONS]:
            lines.append(f"- **[{item.category}]** {item.content}")

    if report_url:
        lines.extend(["", f"📄 [查看完整报告]({report_url})"])

    lines.extend(
        [
            "",
            "---",
            f"*由 {result.model_name} 自动生成 · {pr.owner}/{pr.repo}#{pr.number}*",
        ]
    )
    return "\n".join(lines)
