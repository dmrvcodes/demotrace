import { formatTimestamp } from "@/lib/format";
import type { ClaimResult } from "@/lib/types";
import { StatusBadge } from "./status-badge";

type ClaimCardProps = {
  claim: ClaimResult;
  isActive: boolean;
  onEvidenceClick: (claimId: string, seconds: number) => void;
};

export function ClaimCard({ claim, isActive, onEvidenceClick }: ClaimCardProps) {
  return (
    <article
      className={`claim-card claim-card--${claim.status} ${isActive ? "claim-card--active" : ""}`}
      aria-current={isActive ? "true" : undefined}
    >
      <div className="claim-card__header">
        <p className="claim-card__id">{claim.claimId}</p>
        <StatusBadge status={claim.status} />
      </div>
      <h3>{claim.text}</h3>
      <p className="claim-card__explanation">{claim.explanation}</p>
      {claim.evidence.length > 0 ? (
        <div className="claim-card__evidence" aria-label="Evidence timestamps">
          {claim.evidence.map((evidence) => (
            <button
              className="timestamp-button"
              key={evidence.refId}
              onClick={() => onEvidenceClick(claim.claimId, evidence.t)}
              type="button"
            >
              [{formatTimestamp(evidence.t)}]
            </button>
          ))}
        </div>
      ) : (
        <p className="claim-card__no-evidence">No evidence found</p>
      )}
    </article>
  );
}
