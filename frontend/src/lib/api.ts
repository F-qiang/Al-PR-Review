import type { ReviewListResponse, ReviewTask, ReviewTaskStatus } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export async function createReview(prUrl: string, githubToken?: string): Promise<ReviewTask> {
  const response = await fetch(`${API_BASE}/api/v1/reviews`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pr_url: prUrl, github_token: githubToken || undefined }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "创建任务失败" }));
    throw new Error(error.detail ?? "创建任务失败");
  }

  return response.json();
}

export async function getReview(taskId: string): Promise<ReviewTask> {
  const response = await fetch(`${API_BASE}/api/v1/reviews/${taskId}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("获取任务失败");
  }

  return response.json();
}

export async function listReviews(params?: {
  page?: number;
  pageSize?: number;
  status?: ReviewTaskStatus;
}): Promise<ReviewListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set("page", String(params.page));
  if (params?.pageSize) searchParams.set("page_size", String(params.pageSize));
  if (params?.status) searchParams.set("status", params.status);

  const query = searchParams.toString();
  const response = await fetch(`${API_BASE}/api/v1/reviews${query ? `?${query}` : ""}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("获取历史记录失败");
  }
  return response.json();
}

export function getStreamUrl(taskId: string): string {
  return `${API_BASE}/api/v1/reviews/${taskId}/stream`;
}

export function getReportDownloadUrl(taskId: string): string {
  return `${API_BASE}/api/v1/reviews/${taskId}/report.md`;
}
