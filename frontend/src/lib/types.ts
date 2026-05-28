export interface PullRequestInfo {
  owner: string;
  repo: string;
  number: number;
  title: string;
  author: string;
  body: string;
  url: string;
  additions: number;
  deletions: number;
  changed_files: number;
}

export interface RiskItem {
  file: string;
  line: number | null;
  severity: "low" | "medium" | "high" | "critical";
  category: string;
  description: string;
  suggestion: string;
  source: "rule" | "llm";
}

export interface SuggestionItem {
  category: string;
  content: string;
  priority: "low" | "medium" | "high";
}

export interface ReviewResult {
  summary: string;
  risks: RiskItem[];
  suggestions: SuggestionItem[];
  model_name: string;
  token_used?: number | null;
  duration_ms?: number | null;
}

export interface ReviewTask {
  task_id: string;
  status: string;
  pr: PullRequestInfo | null;
  result: ReviewResult | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface ReviewListItem {
  task_id: string;
  status: string;
  pr_url: string;
  pr_title: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface StatusEvent {
  stage: string;
  message: string;
  files_count?: number;
}
