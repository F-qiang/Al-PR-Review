"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export function FloatingPanel() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [demoMode, setDemoMode] = useState(false);

  const demoUrl = useMemo(() => {
    return demoMode ? "https://github.com/python/cpython/pull/1?demo=1" : "https://github.com/python/cpython/pull/1";
  }, [demoMode]);

  return (
    <div className="fixed bottom-4 left-4 z-50">
      {open ? (
        <div className="mb-3 w-72 rounded-2xl border border-slate-200 bg-white/95 p-4 shadow-xl backdrop-blur">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-slate-900">快捷功能面板</p>
              <p className="text-xs text-slate-500">左下角浮窗 · 演示 / 调试快捷入口</p>
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="rounded-full px-2 py-1 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
            >
              ×
            </button>
          </div>

          <div className="mt-4 space-y-3">
            <label className="flex items-center justify-between rounded-xl bg-slate-50 px-3 py-2 text-sm text-slate-700">
              <span>演示模式</span>
              <input
                type="checkbox"
                checked={demoMode}
                onChange={(event) => setDemoMode(event.target.checked)}
                className="h-4 w-4 accent-indigo-600"
              />
            </label>

            <div className="grid grid-cols-2 gap-2 text-sm">
              <button
                type="button"
                onClick={() => router.push("/")}
                className="rounded-xl border border-slate-200 px-3 py-2 text-slate-700 transition hover:bg-slate-50"
              >
                回到首页
              </button>
              <button
                type="button"
                onClick={() => window.location.reload()}
                className="rounded-xl border border-slate-200 px-3 py-2 text-slate-700 transition hover:bg-slate-50"
              >
                刷新页面
              </button>
              <Link
                href={demoUrl}
                className="rounded-xl border border-indigo-200 bg-indigo-50 px-3 py-2 text-center text-indigo-700 transition hover:bg-indigo-100"
              >
                打开演示 PR
              </Link>
              <Link
                href="/docs/测试清单.md"
                className="rounded-xl border border-slate-200 px-3 py-2 text-center text-slate-700 transition hover:bg-slate-50"
              >
                测试清单
              </Link>
            </div>
          </div>
        </div>
      ) : null}

      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className="flex h-12 w-12 items-center justify-center rounded-full bg-indigo-600 text-white shadow-lg transition hover:bg-indigo-500"
        aria-label="打开快捷功能面板"
      >
        ☰
      </button>
    </div>
  );
}
