"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getReportDownloadUrl, getStreamUrl } from "@/lib/api";
import { AnalysisProgress } from "@/components/AnalysisProgress";
import type { DoneEvent, PullRequestInfo, RiskItem, StatusEvent, SuggestionItem } from "@/lib/types";

const severityStyle: Record<string, string> = {
  critical: "bg-red-100 text-red-700 border-red-200",
  high: "bg-orange-100 text-orange-700 border-orange-200",
  medium: "bg-amber-100 text-amber-700 border-amber-200",
  low: "bg-slate-100 text-slate-600 border-slate-200",
};

export function ReviewStream({ taskId }: { taskId: string }) {
  const [status, setStatus] = useState<StatusEvent | null>({
    stage: "pending",
    message: "连接分析服务...",
  });
  const [prInfo, setPrInfo] = useState<PullRequestInfo | null>(null);
  const [summary, setSummary] = useState("");
  const [risks, setRisks] = useState<RiskItem[]>([]);
  const [suggestions, setSuggestions] = useState<SuggestionItem[]>([]);
  const [doneMeta, setDoneMeta] = useState<DoneEvent | null>(null);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const source = new EventSource(getStreamUrl(taskId));

    source.addEventListener("status", (event) => {
      setStatus(JSON.parse(event.data) as StatusEvent);
    });

    source.addEventListener("pr_info", (event) => {
      setPrInfo(JSON.parse(event.data) as PullRequestInfo);
    });

    source.addEventListener("summary", (event) => {
      const data = JSON.parse(event.data) as { content: string };
      setSummary(data.content);
    });

    source.addEventListener("risk", (event) => {
      setRisks((prev) => [...prev, JSON.parse(event.data) as RiskItem]);
    });

    source.addEventListener("suggestion", (event) => {
      setSuggestions((prev) => [...prev, JSON.parse(event.data) as SuggestionItem]);
    });

    source.addEventListener("done", (event) => {
      setDoneMeta(JSON.parse(event.data) as DoneEvent);
      setDone(true);
      source.close();
    });

    source.addEventListener("error", (event) => {
      if (event instanceof MessageEvent) {
        const data = JSON.parse(event.data) as { message: string };
        setError(data.message);
      } else {
        setError("连接中断，请刷新页面重试");
      }
      source.close();
    });

    return () => source.close();
  }, [taskId]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <Link href="/" className="text-sm text-indigo-600 hover:text-indigo-500">
          ← 返回首页
        </Link>
        <div className="flex flex-wrap items-center gap-3">
          {done ? (
            <a
              href={getReportDownloadUrl(taskId)}
              className="rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-sm font-medium text-indigo-700 transition hover:bg-indigo-100"
            >
              下载 Markdown 报告
            </a>
          ) : null}
          {doneMeta?.report_url ? (
            <a
              href={doneMeta.report_url}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-sm font-medium text-emerald-700 transition hover:bg-emerald-100"
            >
              七牛云报告链接
            </a>
          ) : null}
          {doneMeta?.comment_url ? (
            <a
              href={doneMeta.comment_url}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-sm font-medium text-slate-700 transition hover:bg-slate-100"
            >
              查看 PR 评论
            </a>
          ) : null}
          {!done && !error ? (
            <span className="inline-flex items-center gap-2 text-sm text-slate-500">
              <span className="h-2 w-2 animate-pulse rounded-full bg-indigo-500" />
              {status?.message ?? "分析中..."}
            </span>
          ) : null}
        </div>
      </div>

      {error ? (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-red-700">
          {error}
        </div>
      ) : null}

      {!error ? (
        <AnalysisProgress
          stage={status?.stage ?? "pending"}
          done={done}
          message={status?.message}
        />
      ) : null}

      {prInfo ? (
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-sm text-slate-500">
                {prInfo.owner}/{prInfo.repo} #{prInfo.number}
              </p>
              <h2 className="mt-1 text-xl font-semibold text-slate-900">{prInfo.title}</h2>
              <p className="mt-2 text-sm text-slate-600">
                作者 {prInfo.author} · +{prInfo.additions} / -{prInfo.deletions} · {prInfo.changed_files} 个文件
              </p>
            </div>
            <a
              href={prInfo.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
            >
              在 GitHub 查看 →
            </a>
          </div>
        </section>
      ) : null}

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-3 text-lg font-semibold text-slate-900">变更摘要</h2>
        {summary ? (
          <p className="leading-7 whitespace-pre-wrap text-slate-700">{summary}</p>
        ) : (
          <div className="h-20 animate-pulse rounded-xl bg-slate-100" />
        )}
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">风险识别</h2>
          <span className="text-sm text-slate-500">{risks.length} 项</span>
        </div>
        {risks.length === 0 ? (
          <p className="text-sm text-slate-500">
            {done ? "未发现明显风险" : "正在扫描风险点..."}
          </p>
        ) : (
          <div className="space-y-4">
            {risks.map((risk, index) => (
              <article
                key={`${risk.file}-${risk.line}-${index}`}
                className="rounded-xl border border-slate-100 bg-slate-50 p-4"
              >
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <span
                    className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${severityStyle[risk.severity]}`}
                  >
                    {risk.severity}
                  </span>
                  <span className="text-xs text-slate-500">{risk.category}</span>
                  <span className="text-xs text-slate-500">
                    {risk.source === "rule" ? "规则引擎" : "AI 分析"}
                  </span>
                </div>
                <p className="font-medium text-slate-900">
                  {risk.file}
                  {risk.line ? `:${risk.line}` : ""}
                </p>
                <p className="mt-2 text-sm text-slate-700">{risk.description}</p>
                <p className="mt-2 text-sm text-indigo-700">建议：{risk.suggestion}</p>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">Review 建议</h2>
          <span className="text-sm text-slate-500">{suggestions.length} 项</span>
        </div>
        {suggestions.length === 0 ? (
          <p className="text-sm text-slate-500">
            {done ? "暂无额外建议" : "正在生成建议..."}
          </p>
        ) : (
          <ul className="space-y-3">
            {suggestions.map((item, index) => (
              <li
                key={`${item.category}-${index}`}
                className="rounded-xl border border-slate-100 px-4 py-3 text-sm text-slate-700"
              >
                <span className="mr-2 rounded bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700">
                  {item.category}
                </span>
                {item.content}
              </li>
            ))}
          </ul>
        )}
      </section>

      {done && doneMeta ? (
        <p className="text-center text-xs text-slate-400">
          分析完成
          {doneMeta.duration_ms ? ` · 耗时 ${(doneMeta.duration_ms / 1000).toFixed(1)}s` : ""}
          {doneMeta.chunk_count && doneMeta.chunk_count > 1 ? ` · 分 ${doneMeta.chunk_count} 批并行分析` : ""}
        </p>
      ) : null}
    </div>
  );
}
