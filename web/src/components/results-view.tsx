import type { AnalysisResult } from "@/lib/types";
import { ClaimCard } from "./claim-card";
import { Timeline } from "./timeline";

type ResultsViewProps = {
  activeClaimId: string | null;
  currentTime: number;
  onEvidenceClick: (claimId: string, seconds: number) => void;
  onTimeUpdate: (seconds: number) => void;
  onRecheck: () => void;
  result: AnalysisResult;
  isSample: boolean;
  videoSrc: string;
  videoRef: React.RefObject<HTMLVideoElement | null>;
};

export function ResultsView({
  activeClaimId,
  currentTime,
  onEvidenceClick,
  onTimeUpdate,
  onRecheck,
  result,
  isSample,
  videoSrc,
  videoRef,
}: ResultsViewProps) {
  return (
    <section className="results-layout" aria-labelledby="analysis-title">
      <div className="results-main">
        <div className="results-heading">
          <div>
            <p className="eyebrow">{isSample ? "Example analysis" : "Live analysis"}</p>
            <h2 id="analysis-title">Evidence map</h2>
          </div>
          <span className="result-count">{result.claims.length} claims</span>
        </div>
        <div className="video-shell">
          <video
            controls
            onTimeUpdate={(event) => onTimeUpdate(event.currentTarget.currentTime)}
            preload="metadata"
            ref={videoRef}
            src={videoSrc}
          >
            <track kind="captions" />
          </video>
        </div>
        <Timeline currentTime={currentTime} onEvidenceClick={onEvidenceClick} result={result} />
        <div className="result-legend" aria-label="Assessment legend"><span><i className="legend-dot legend-dot--shown" />Shown</span><span><i className="legend-dot legend-dot--told" />Told only</span><span><i className="legend-dot legend-dot--missing" />Missing</span></div>
        <div className="assessment-note">
          <span aria-hidden="true">i</span>
          AI assessment — click the evidence to verify.
        </div>
        <button className="secondary-button" onClick={onRecheck} type="button">
          Re-check with new video
        </button>
      </div>
      <aside className="claim-list" aria-label="Claim assessments">
        {result.claims.map((claim) => (
          <ClaimCard
            claim={claim}
            isActive={claim.claim_id === activeClaimId}
            key={claim.claim_id}
            onEvidenceClick={onEvidenceClick}
          />
        ))}
      </aside>
    </section>
  );
}
