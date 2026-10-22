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
          style={{ left: `${Math.min(100, (currentTime / result.duration_s) * 100)}%` }}
        />
        {result.claims.flatMap((claim) =>
          claim.evidence.map((evidence) => (
            <button
              aria-label={`${claim.claim_id} evidence at ${Math.round(evidence.t)} seconds`}
              className={`timeline__marker timeline__marker--${claim.status}`}
              key={`${claim.claim_id}-${evidence.refId}`}
              onClick={() => onEvidenceClick(claim.claim_id, evidence.t)}
              style={{ left: `${(evidence.t / result.duration_s) * 100}%` }}
              type="button"
            />
          )),
        )}
      </div>
      <div className="timeline__labels" aria-hidden="true">
        <span>0:00</span>
        <span>{formatTimestamp(result.duration_s / 2)}</span>
        <span>{formatTimestamp(result.duration_s)}</span>
      </div>
    </div>
  );
}
