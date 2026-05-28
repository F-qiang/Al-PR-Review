const STAGE_ORDER = ["parsing", "fetching", "analyzing", "llm", "comment", "upload"] as const;

const STAGE_LABELS: Record<string, string> = {
  parsing: "解析 PR",
  fetching: "拉取变更",
  analyzing: "扫描文件",
  llm: "AI 分析",
  comment: "发布评论",
  upload: "上传报告",
};

function stageIndex(stage: string): number {
  const index = STAGE_ORDER.indexOf(stage as (typeof STAGE_ORDER)[number]);
  return index >= 0 ? index : 0;
}

export function AnalysisProgress({
  stage,
  done,
  message,
}: {
  stage: string;
  done: boolean;
  message?: string;
}) {
  const visibleStages = ["parsing", "fetching", "analyzing", "llm"] as const;
  const current = done ? visibleStages.length : stageIndex(stage);

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center justify-between gap-4">
        <h2 className="text-sm font-semibold text-slate-900">分析进度</h2>
        {!done && message ? (
          <span className="text-xs text-slate-500">{message}</span>
        ) : done ? (
          <span className="text-xs text-emerald-600">已完成</span>
        ) : null}
      </div>
      <ol className="flex flex-wrap items-center gap-2">
        {visibleStages.map((item, index) => {
          const completed = done || index < current;
          const active = !done && index === current;

          return (
            <li key={item} className="flex items-center gap-2">
              <span
                className={[
                  "inline-flex h-7 min-w-7 items-center justify-center rounded-full text-xs font-medium",
                  completed
                    ? "bg-indigo-600 text-white"
                    : active
                      ? "border-2 border-indigo-600 text-indigo-600"
                      : "bg-slate-100 text-slate-400",
                ].join(" ")}
              >
                {completed && !active ? "✓" : index + 1}
              </span>
              <span
                className={[
                  "text-sm",
                  completed || active ? "text-slate-900" : "text-slate-400",
                ].join(" ")}
              >
                {STAGE_LABELS[item]}
              </span>
              {index < visibleStages.length - 1 ? (
                <span className="mx-1 hidden text-slate-300 sm:inline">→</span>
              ) : null}
            </li>
          );
        })}
      </ol>
    </section>
  );
}
