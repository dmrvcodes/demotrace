export type ClaimStatus = "shown" | "told_only" | "missing";

export type Evidence = {
  refId: string;
  kind: "frame" | "speech";
  t: number;
};

export type ClaimResult = {
  claim_id: string;
  text: string;
  status: ClaimStatus;
  explanation: string;
  evidence: Evidence[];
};

export type AnalysisResult = {
  schema_version: number;
  duration_s: number;
  claims: ClaimResult[];
};
