import type { ClaimStatus } from "@/lib/types";

const labels: Record<ClaimStatus, string> = {
  shown: "Shown",
  told_only: "Told only",
  missing: "Missing",
};

export function StatusBadge({ status }: { status: ClaimStatus }) {
  return (
    <span className={`status-badge status-badge--${status}`}>
      <span aria-hidden="true" className="status-badge__dot" />
      {labels[status]}
    </span>
  );
}
