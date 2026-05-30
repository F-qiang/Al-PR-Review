import { ReviewStream } from "@/components/ReviewStream";

export default async function ReviewPage({
  params,
  searchParams,
}: {
  params: Promise<{ taskId: string }>;
  searchParams: Promise<{ reused?: string }>;
}) {
  const { taskId } = await params;
  const { reused } = await searchParams;

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <div className="mx-auto max-w-4xl px-6 py-12">
        <header className="mb-8">
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-indigo-600">
            Review Result
          </p>
          <h1 className="mt-2 text-3xl font-bold text-slate-900">PR 分析报告</h1>
          <p className="mt-2 text-sm text-slate-500">任务 ID：{taskId}</p>
        </header>
        {reused === "1" ? (
          <div className="mb-6 rounded-2xl border border-amber-200 bg-amber-50 px-5 py-4 text-sm text-amber-800">
            已复用同一 PR 的进行中或近期评审任务，避免重复分析。
          </div>
        ) : null}
        <ReviewStream taskId={taskId} />
      </div>
    </div>
  );
}
