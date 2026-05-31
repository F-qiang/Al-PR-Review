"use client";

import { useRouter } from "next/navigation";

import { HistoryList } from "@/components/HistoryList";
import type { ReviewListResponse } from "@/lib/types";

export function HistoryPanel({ history }: { history: ReviewListResponse }) {
  const router = useRouter();

  return (
    <div>
      <div className="mb-4 flex items-center justify-between gap-3">
        <h2 className="text-xl font-semibold text-slate-900">最近记录</h2>
      </div>
      <HistoryList
        items={history.items}
        page={history.page}
        totalPages={history.total_pages}
        status={history.status}
        onRefresh={() => router.refresh()}
      />
    </div>
  );
}
