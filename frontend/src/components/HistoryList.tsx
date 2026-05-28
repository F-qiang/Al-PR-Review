import type { ReviewListItem } from "@/lib/types";
import Link from "next/link";

const statusLabel: Record<string, string> = {
  pending: "等待中",
  fetching: "拉取中",
  analyzing: "分析中",
  completed: "已完成",
  failed: "失败",
};

export function HistoryList({ items }: { items: ReviewListItem[] }) {
  if (items.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-6 py-10 text-center text-sm text-slate-500">
        暂无分析记录，提交第一个 PR 开始体验
      </div>
    );
  }

  return (
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
  );
}
