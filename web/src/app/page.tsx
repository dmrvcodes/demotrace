"use client";

import { useRef, useState } from "react";
import { ResultsView } from "@/components/results-view";
import { UploadView } from "@/components/upload-view";
import { sampleAnalysis } from "@/lib/sample";

export default function Home() {
  const [screen, setScreen] = useState<"upload" | "results">("upload");
  const [activeClaimId, setActiveClaimId] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const videoRef = useRef<HTMLVideoElement>(null);

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
        {screen === "upload" ? (
          <UploadView onTrySample={() => setScreen("results")} />
        ) : (
          <ResultsView
            activeClaimId={activeClaimId}
            currentTime={currentTime}
            onEvidenceClick={seekToEvidence}
            onTimeUpdate={setCurrentTime}
            onRecheck={() => setScreen("upload")}
            result={sampleAnalysis}
            videoRef={videoRef}
          />
        )}
      </main>
    </div>
  );
}
