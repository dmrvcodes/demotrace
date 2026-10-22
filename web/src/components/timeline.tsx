import { formatTimestamp } from "@/lib/format";
import type { AnalysisResult } from "@/lib/types";

type TimelineProps = {
  result: AnalysisResult;
  currentTime: number;
  onEvidenceClick: (claimId: string, seconds: number) => void;
};

export function Timeline({ result, currentTime, onEvidenceClick }: TimelineProps) {
  return (
    <div className="timeline" aria-label="Evidence timeline">
      <div className="timeline__track">
        <span
          aria-hidden="true"
          className="timeline__playhead"
          style={{ left: `${Math.min(100, (currentTime / result.durationS) * 100)}%` }}
        />
        {result.claims.flatMap((claim) =>
          claim.evidence.map((evidence) => (
            <button
              aria-label={`${claim.claimId} evidence at ${Math.round(evidence.t)} seconds`}
              className={`timeline__marker timeline__marker--${claim.status}`}
              key={`${claim.claimId}-${evidence.refId}`}
              onClick={() => onEvidenceClick(claim.claimId, evidence.t)}
              style={{ left: `${(evidence.t / result.durationS) * 100}%` }}
              type="button"
            />
          )),
        )}
      </div>
      <div className="timeline__labels" aria-hidden="true">
        <span>0:00</span>
        <span>{formatTimestamp(result.durationS / 2)}</span>
        <span>{formatTimestamp(result.durationS)}</span>
      </div>
    </div>
  );
}
