import type { AnalysisResult } from "./types";

export const sampleAnalysis: AnalysisResult = {
  schemaVersion: 1,
  durationS: 90,
  claims: [
    {
      claimId: "C1",
      text: "The video visibly shows a rabbit on screen.",
      status: "shown",
      explanation:
        "A rabbit is clearly visible on screen, rather than merely being described or promised.",
      evidence: [{ refId: "F034", kind: "frame", t: 34 }],
    },
    {
      claimId: "C2",
      text: "The app exports reports to Markdown.",
      status: "told_only",
      explanation:
        "The capability is promised on a slide, but the export itself is not demonstrated.",
      evidence: [{ refId: "F002", kind: "frame", t: 2 }],
    },
    {
      claimId: "C3",
      text: "The app supports team invitations.",
      status: "missing",
      explanation:
        "No invitation flow, member list, or team-management result appears in the video.",
      evidence: [],
    },
  ],
};
