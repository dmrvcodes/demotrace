import type { AnalysisResult, Evidence } from "./types";

export type JobStatus = "created" | "queued" | "processing" | "completed" | "failed";

export type Job = {
  job_id: string;
  status: JobStatus;
  result?: AnalysisResult;
  error_message?: string;
};

type ApiEvidence = Omit<Evidence, "refId"> & { ref_id: string };
type ApiAnalysisResult = Omit<AnalysisResult, "claims"> & {
  claims: Array<Omit<AnalysisResult["claims"][number], "evidence"> & { evidence: ApiEvidence[] }>;
};

type CreatedJob = { job_id: string; job_token: string; upload_url: string; upload_fields?: Record<string, string> };

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

export async function uploadVideo(created: CreatedJob, file: File): Promise<void> {
  const isControlApiUpload = new URL(created.upload_url).origin === new URL(apiBase).origin;
  const response = created.upload_fields
    ? await fetch(created.upload_url, {
        method: "POST",
        body: (() => {
          const form = new FormData();
          for (const [name, value] of Object.entries(created.upload_fields ?? {})) form.append(name, value);
          form.append("file", file);
          return form;
        })(),
      })
    : await fetch(created.upload_url, {
        method: "PUT",
        headers: {
          ...(isControlApiUpload ? { Authorization: `Bearer ${created.job_token}` } : {}),
          "Content-Type": file.type || "video/mp4",
        },
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
  const job = await apiFetch<Omit<Job, "result"> & { result?: ApiAnalysisResult }>(`/jobs/${jobId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return {
    ...job,
    result: job.result && {
      ...job.result,
      claims: job.result.claims.map((claim) => ({
        ...claim,
        evidence: claim.evidence.map(({ ref_id, ...evidence }) => ({ ...evidence, refId: ref_id })),
      })),
    },
  };
}
