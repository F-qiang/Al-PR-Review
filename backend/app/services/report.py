from datetime import datetime

from app.schemas import PullRequestInfo, ReviewResult


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
