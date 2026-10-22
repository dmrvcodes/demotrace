import type { AnalysisResult } from "./types";

export type JobStatus = "created" | "queued" | "processing" | "completed" | "failed";

export type Job = {
  job_id: string;
  status: JobStatus;
  result?: AnalysisResult;
  error_message?: string;
};

type CreatedJob = { job_id: string; job_token: string; upload_url: string };

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, init);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed (${response.status})`);
  }
  return response.status === 204 ? (undefined as T) : response.json() as Promise<T>;
}

export async function createJob(): Promise<CreatedJob> {
  return apiFetch<CreatedJob>("/jobs", { method: "POST" });
}

export async function uploadVideo(uploadUrl: string, token: string, file: File): Promise<void> {
  const response = await fetch(uploadUrl, {
    method: "PUT",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": file.type || "video/mp4" },
    body: file,
  });
  if (!response.ok) throw new Error(`Upload failed (${response.status})`);
}

export async function startAnalysis(jobId: string, token: string, claims: string[]): Promise<Job> {
  return apiFetch<Job>(`/jobs/${jobId}/analyze`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({ claims }),
  });
}

export async function getJob(jobId: string, token: string): Promise<Job> {
  return apiFetch<Job>(`/jobs/${jobId}`, { headers: { Authorization: `Bearer ${token}` } });
}
