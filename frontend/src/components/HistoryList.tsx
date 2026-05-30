import type { ReviewListItem } from "@/lib/types";
import Link from "next/link";

const statusLabel: Record<string, string> = {
  pending: "等待中",
  fetching: "拉取中",
  analyzing: "分析中",
  completed: "已完成",
  failed: "失败",
};

export function HistoryList({
  items,
  page,
  totalPages,
  status,
}: {
  items: ReviewListItem[];
  page: number;
  totalPages: number;
  status: string | null;
}) {
  const statusOptions = [
    { value: "", label: "全部" },
    { value: "pending", label: "等待中" },
    { value: "fetching", label: "拉取中" },
    { value: "analyzing", label: "分析中" },
    { value: "completed", label: "已完成" },
    { value: "failed", label: "失败" },
  ];

  const buildHref = (nextPage: number, nextStatus = status) => {
    const params = new URLSearchParams();
    if (nextPage > 1) params.set("page", String(nextPage));
    if (nextStatus) params.set("status", nextStatus);
    const query = params.toString();
    return query ? `/?${query}` : "/";
  };

  if (items.length === 0) {
    return (
      <div className="space-y-4">
        <div className="flex flex-wrap gap-2">
          {statusOptions.map((option) => (
            <Link
              key={option.value || "all"}
              href={buildHref(1, option.value || null)}
              className={`rounded-full px-3 py-1 text-xs transition ${
                (status ?? "") === option.value
                  ? "bg-indigo-600 text-white"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {option.label}
            </Link>
          ))}
        </div>
        <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-6 py-10 text-center text-sm text-slate-500">
          暂无分析记录，提交第一个 PR 开始体验
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {statusOptions.map((option) => (
          <Link
            key={option.value || "all"}
            href={buildHref(1, option.value || null)}
            className={`rounded-full px-3 py-1 text-xs transition ${
              (status ?? "") === option.value
                ? "bg-indigo-600 text-white"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            {option.label}
          </Link>
        ))}
      </div>
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
        <ul className="divide-y divide-slate-100">
        {items.map((item) => (
          <li key={item.task_id}>
            <Link
              href={`/review/${item.task_id}`}
              className="flex items-center justify-between gap-4 px-5 py-4 transition hover:bg-slate-50"
            >
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-slate-900">
                  {item.pr_title || item.pr_url}
                </p>
                <p className="truncate text-xs text-slate-500">{item.pr_url}</p>
              </div>
              <span className="shrink-0 rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600">
                {statusLabel[item.status] ?? item.status}
              </span>
            </Link>
          </li>
        ))}
        </ul>
      </div>
      {totalPages > 1 ? (
        <div className="flex items-center justify-between text-sm text-slate-500">
          <Link
            href={buildHref(Math.max(page - 1, 1))}
            className={`rounded-lg border px-3 py-2 transition ${
              page <= 1
                ? "pointer-events-none border-slate-100 text-slate-300"
                : "border-slate-200 text-slate-600 hover:bg-slate-50"
            }`}
          >
            上一页
          </Link>
          <span>
            第 {page} / {totalPages} 页
          </span>
          <Link
            href={buildHref(Math.min(page + 1, totalPages))}
            className={`rounded-lg border px-3 py-2 transition ${
              page >= totalPages
                ? "pointer-events-none border-slate-100 text-slate-300"
                : "border-slate-200 text-slate-600 hover:bg-slate-50"
            }`}
          >
            下一页
          </Link>
        </div>
      ) : null}
    </div>
  );
}
