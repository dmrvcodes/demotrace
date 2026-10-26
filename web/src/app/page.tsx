"use client";

import { useEffect, useRef, useState } from "react";
import { ClaimsView } from "@/components/claims-view";
import { ResultsView } from "@/components/results-view";
import { UploadView } from "@/components/upload-view";
import { WaitingView } from "@/components/waiting-view";
import { createJob, getJob, startAnalysis, uploadVideo, type JobStatus } from "@/lib/api";
import { loadSavedAnalysis, saveAnalysis } from "@/lib/saved-analysis";
import { SAMPLE_VIDEO, sampleAnalysis } from "@/lib/sample";
import { isHevcMp4 } from "@/lib/video-codec";

export default function Home() {
  const isLive = Boolean(process.env.NEXT_PUBLIC_API_BASE_URL);
  const [restored] = useState(() => loadSavedAnalysis());
  const restoredCompleted = restored?.job.status === "completed" && Boolean(restored.result);
  const restoredWaiting = restored?.job.status === "queued" || restored?.job.status === "processing";
  const [screen, setScreen] = useState<"upload" | "claims" | "waiting" | "results">(
    restoredCompleted ? "results" : restoredWaiting ? "waiting" : "upload",
  );
  const [activeClaimId, setActiveClaimId] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [file, setFile] = useState<File | null>(null);
  // A restored live job (finished or still running) must ask for its own video, never fall back to the sample.
  const [videoSrc, setVideoSrc] = useState(restoredCompleted || restoredWaiting ? "" : SAMPLE_VIDEO);
  const [claims, setClaims] = useState(restored?.claims ?? ["", "", ""]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [job, setJob] = useState<{ id: string; token: string; status: JobStatus } | null>(
    restoredWaiting || restoredCompleted ? restored!.job : null,
  );
  const [result, setResult] = useState(restored?.result ?? sampleAnalysis);
  const [isSample, setIsSample] = useState(!restored);
  const [attachSavedVideo, setAttachSavedVideo] = useState(false);

  useEffect(() => () => { if (videoSrc.startsWith("blob:")) URL.revokeObjectURL(videoSrc); }, [videoSrc]);
  useEffect(() => {
    if (isSample || !job || job.status === "failed") return;
    saveAnalysis({ savedAt: Date.now(), claims, job, result: job.status === "completed" ? result : undefined });
  }, [claims, isSample, job, result]);
  useEffect(() => {
    if (screen !== "waiting" || !job) return;
    let cancelled = false;
    const poll = async () => {
      try {
        const next = await getJob(job.id, job.token);
        if (cancelled) return;
        setJob((current) => current ? { ...current, status: next.status } : current);
        if (next.status === "completed" && next.result) { setResult(next.result); setScreen("results"); }
        if (next.status === "failed") { setError(next.error_message ?? "Analysis failed"); setScreen("claims"); }
      } catch (pollError) {
        if (!cancelled) { setError(pollError instanceof Error ? pollError.message : "Polling failed"); setScreen("claims"); }
      }
    };
    void poll();
    const pollId = window.setInterval(() => { void poll(); }, 2_000);
    return () => { cancelled = true; window.clearInterval(pollId); };
  }, [job, screen]);

  const selectFile = async (selected: File) => {
    setError(null);
    if (selected.size > 150 * 1024 * 1024) return setError("Video exceeds 150 MB.");
    if (selected.type && selected.type !== "video/mp4") return setError("Use an H.264 MP4 video.");
    if (await isHevcMp4(selected)) return setError("This looks like HEVC. Re-export as H.264 MP4 before uploading.");
    const url = URL.createObjectURL(selected);
    const probe = document.createElement("video");
    probe.preload = "metadata";
    probe.src = url;
    probe.onloadedmetadata = () => {
      if (probe.duration > 180.5) { URL.revokeObjectURL(url); return setError("Video is longer than 3 minutes."); }
      setFile(selected); setVideoSrc(url); setIsSample(false);
      if (attachSavedVideo) {
        setAttachSavedVideo(false); setScreen("results");
      } else {
        setScreen("claims");
      }
    };
    probe.onerror = () => { URL.revokeObjectURL(url); setError("Video metadata could not be read. Re-export as H.264 MP4."); };
  };
  const runLiveAnalysis = async () => { if (!file) return; setBusy(true); setError(null); try { const created = await createJob(); await uploadVideo(created, file); const queued = await startAnalysis(created.job_id, created.job_token, claims); setJob({ id: created.job_id, token: created.job_token, status: queued.status }); setScreen("waiting"); } catch (runError) { setError(runError instanceof Error ? runError.message : "Could not start analysis"); } finally { setBusy(false); } };

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
        <span className="environment-label">{isLive ? "LIVE ANALYSIS" : "LOCAL DEVELOPMENT"}</span>
      </header>
      <main>
        {screen === "upload" && <UploadView error={error} fileName={file?.name ?? null} onFileSelected={selectFile} onTrySample={() => { setResult(sampleAnalysis); setVideoSrc(SAMPLE_VIDEO); setIsSample(true); setAttachSavedVideo(false); setScreen("results"); }} />}
        {screen === "claims" && <ClaimsView busy={busy} claims={claims} error={error} onChange={setClaims} onStart={runLiveAnalysis} />}
        {screen === "waiting" && <WaitingView status={job?.status === "processing" ? "processing" : "queued"} />}
        {screen === "results" && (
          <ResultsView
            activeClaimId={activeClaimId}
            currentTime={currentTime}
            onEvidenceClick={seekToEvidence}
            onTimeUpdate={setCurrentTime}
            onRecheck={() => { setAttachSavedVideo(false); setScreen("upload"); }}
            onAttachSavedVideo={() => { setAttachSavedVideo(true); setScreen("upload"); }}
            result={result}
            isSample={isSample}
            videoRef={videoRef}
            videoSrc={videoSrc}
          />
        )}
      </main>
    </div>
  );
}
