import type { AnalysisResult } from "@/lib/types";
import { SAMPLE_NOTE } from "@/lib/sample";
import { ClaimCard } from "./claim-card";
import { Timeline } from "./timeline";

type ResultsViewProps = {
  activeClaimId: string | null;
  currentTime: number;
  onEvidenceClick: (claimId: string, seconds: number) => void;
  onTimeUpdate: (seconds: number) => void;
  onAttachSavedVideo: () => void;
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
  onAttachSavedVideo,
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
            <p className="eyebrow">{isSample ? "Recorded analysis · sample" : "Live analysis"}</p>
            <h2 id="analysis-title">Evidence map</h2>
            {isSample && <p className="sample-note">{SAMPLE_NOTE}</p>}
          </div>
          <span className="result-count">{result.claims.length} claims</span>
        </div>
        {videoSrc ? (
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
        ) : (
          <div className="video-shell video-shell--saved">
            <p>Your saved report is ready. Reattach the original video to play evidence in the timeline.</p>
            <button className="secondary-button" onClick={onAttachSavedVideo} type="button">Attach original video</button>
          </div>
        )}
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
