export type ClaimStatus = "shown" | "told_only" | "missing";

export type Evidence = {
  refId: string;
  kind: "frame" | "speech";
  t: number;
};

export type ClaimResult = {
  claimId: string;
  text: string;
  status: ClaimStatus;
  explanation: string;
  evidence: Evidence[];
};

export type AnalysisResult = {
  schemaVersion: number;
  durationS: number;
  claims: ClaimResult[];
};
