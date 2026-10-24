import type { JobStatus } from "@/lib/api";
import type { AnalysisResult } from "@/lib/types";

const STORAGE_KEY = "demotrace:last-analysis:v1";
const MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000;

export type SavedAnalysis = {
  savedAt: number;
  claims: string[];
  job: { id: string; token: string; status: JobStatus };
  result?: AnalysisResult;
};

function isJobStatus(value: unknown): value is JobStatus {
  return value === "queued" || value === "processing" || value === "completed" || value === "failed";
}

export function loadSavedAnalysis(): SavedAnalysis | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") return null;
    const value = parsed as Partial<SavedAnalysis>;
    if (
      typeof value.savedAt !== "number" || Date.now() - value.savedAt > MAX_AGE_MS ||
      !Array.isArray(value.claims) || !value.job || typeof value.job.id !== "string" ||
      typeof value.job.token !== "string" || !isJobStatus(value.job.status)
    ) {
      window.localStorage.removeItem(STORAGE_KEY);
      return null;
    }
    return value as SavedAnalysis;
  } catch {
    window.localStorage.removeItem(STORAGE_KEY);
    return null;
  }
}

export function saveAnalysis(analysis: SavedAnalysis): void {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(analysis));
}

export function clearSavedAnalysis(): void {
  window.localStorage.removeItem(STORAGE_KEY);
}
