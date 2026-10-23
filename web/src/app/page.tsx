"use client";

import { useEffect, useRef, useState } from "react";
import { ClaimsView } from "@/components/claims-view";
import { ResultsView } from "@/components/results-view";
import { UploadView } from "@/components/upload-view";
import { WaitingView } from "@/components/waiting-view";
import { createJob, getJob, startAnalysis, uploadVideo, type JobStatus } from "@/lib/api";
import { sampleAnalysis } from "@/lib/sample";

export default function Home() {
  const [screen, setScreen] = useState<"upload" | "claims" | "waiting" | "results">("upload");
  const [activeClaimId, setActiveClaimId] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [videoSrc, setVideoSrc] = useState("/samples/demotrace-sample.mp4");
  const [claims, setClaims] = useState(["", "", ""]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [job, setJob] = useState<{ id: string; token: string; status: JobStatus } | null>(null);
  const [result, setResult] = useState(sampleAnalysis);

  useEffect(() => () => { if (videoSrc.startsWith("blob:")) URL.revokeObjectURL(videoSrc); }, [videoSrc]);
  useEffect(() => {
    if (screen !== "waiting" || !job) return;
    const poll = window.setInterval(async () => { try { const next = await getJob(job.id, job.token); setJob((current) => current ? { ...current, status: next.status } : current); if (next.status === "completed" && next.result) { setResult(next.result); setScreen("results"); } if (next.status === "failed") { setError(next.error_message ?? "Analysis failed"); setScreen("claims"); } } catch (pollError) { setError(pollError instanceof Error ? pollError.message : "Polling failed"); setScreen("claims"); } }, 350);
    return () => window.clearInterval(poll);
  }, [job, screen]);

  const selectFile = async (selected: File) => { setError(null); if (selected.size > 150 * 1024 * 1024) return setError("Video exceeds 150 MB."); if (selected.type && selected.type !== "video/mp4") return setError("Use an H.264 MP4 video."); const url = URL.createObjectURL(selected); setFile(selected); setVideoSrc(url); setScreen("claims"); };
  const runLocalAnalysis = async () => { if (!file) return; setBusy(true); setError(null); try { const created = await createJob(); await uploadVideo(created, file); const queued = await startAnalysis(created.job_id, created.job_token, claims); setJob({ id: created.job_id, token: created.job_token, status: queued.status }); setScreen("waiting"); } catch (runError) { setError(runError instanceof Error ? runError.message : "Could not start analysis"); } finally { setBusy(false); } };

  const seekToEvidence = (claimId: string, seconds: number) => {
    setActiveClaimId(claimId || null);
    setCurrentTime(seconds);

    if (videoRef.current) {
      videoRef.current.currentTime = seconds;
    }
  };

  return (
    <div className="app-shell">
      <header className="site-header">
        <button className="wordmark" onClick={() => setScreen("upload")} type="button">
          <span className="wordmark__mark">D</span>
          <span>DemoTrace</span>
        </button>
        <span className="environment-label">LOCAL FIXTURE MODE</span>
      </header>
      <main>
        {screen === "upload" && <UploadView error={error} fileName={file?.name ?? null} onFileSelected={selectFile} onTrySample={() => { setResult(sampleAnalysis); setVideoSrc("/samples/demotrace-sample.mp4"); setScreen("results"); }} />}
        {screen === "claims" && <ClaimsView busy={busy} claims={claims} error={error} onChange={setClaims} onStart={runLocalAnalysis} />}
        {screen === "waiting" && <WaitingView status={job?.status === "processing" ? "processing" : "queued"} />}
        {screen === "results" && (
          <ResultsView
            activeClaimId={activeClaimId}
            currentTime={currentTime}
            onEvidenceClick={seekToEvidence}
            onTimeUpdate={setCurrentTime}
            onRecheck={() => setScreen("upload")}
            result={result}
            videoRef={videoRef}
            videoSrc={videoSrc}
          />
        )}
      </main>
    </div>
  );
}
