"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createReview } from "@/lib/api";

export function ReviewForm() {
  const router = useRouter();
  const [prUrl, setPrUrl] = useState("");
  const [githubToken, setGithubToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const task = await createReview(prUrl.trim(), githubToken.trim() || undefined);
      const reusedQuery = task.reused ? "&reused=1" : "";
      const demoQuery = "&demo=1";
      router.push(`/review/${task.task_id}?demo=1${reusedQuery}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "提交失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <label htmlFor="pr-url" className="mb-2 block text-sm font-medium text-slate-700">
          GitHub PR 链接
        </label>
        <input
          id="pr-url"
          type="text"
          required
          value={prUrl}
          onChange={(event) => setPrUrl(event.target.value)}
          placeholder="https://github.com/owner/repo/pull/123 或 owner/repo#123"
          className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-slate-900 outline-none ring-indigo-500 transition focus:ring-2"
        />
      </div>

      <div>
        <label htmlFor="github-token" className="mb-2 block text-sm font-medium text-slate-700">
          GitHub Token（可选）
        </label>
        <input
          id="github-token"
          type="password"
          value={githubToken}
          onChange={(event) => setGithubToken(event.target.value)}
          placeholder="私有仓库或提高 API 限额时使用"
          className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-slate-900 outline-none ring-indigo-500 transition focus:ring-2"
        />
      </div>

      {error ? (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <button
        type="submit"
        disabled={loading}
        className="inline-flex w-full items-center justify-center rounded-xl bg-indigo-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {loading ? "创建任务中..." : "开始 AI Review"}
      </button>
    </form>
  );
}
