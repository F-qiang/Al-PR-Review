import { ReviewForm } from "@/components/ReviewForm";
import { HistoryList } from "@/components/HistoryList";
import { listReviews } from "@/lib/api";
import type { ReviewListItem } from "@/lib/types";

export default async function HomePage() {
  let history: { items: ReviewListItem[]; total: number } = { items: [], total: 0 };

  try {
    history = await listReviews();
  } catch {
    history = { items: [], total: 0 };
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <div className="mx-auto max-w-5xl px-6 py-12">
        <header className="mb-10">
          <p className="mb-2 text-sm font-medium uppercase tracking-[0.2em] text-indigo-600">
            AI PR Review
          </p>
          <h1 className="text-4xl font-bold tracking-tight text-slate-900">
            智能 Pull Request 评审助手
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-slate-600">
            输入 GitHub PR 链接，自动拉取代码变更，生成变更摘要、风险识别与 Review 建议。
          </p>
        </header>

        <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
          <section className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
            <h2 className="mb-6 text-xl font-semibold text-slate-900">开始分析</h2>
            <ReviewForm />
          </section>

          <section>
            <h2 className="mb-4 text-xl font-semibold text-slate-900">最近记录</h2>
            <HistoryList items={history.items} />
          </section>
        </div>
      </div>
    </div>
  );
}
