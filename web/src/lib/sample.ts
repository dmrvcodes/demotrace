import type { AnalysisResult } from "./types";

// A real, recorded analysis — not a mock. It is what the deployed Worker (claude-sonnet-4-6)
// returned on 23 October 2026 for the scripted TodoMVC demo in /samples/todomvc-sample.mp4
// (job 8c1087c1-964a-4245-b42a-19d2f0349b51); evidence times are exactly as returned.
export const SAMPLE_VIDEO = "/samples/todomvc-sample.mp4";

export const SAMPLE_NOTE =
  "Recorded Claude analysis of a scripted TodoMVC demo — upload your own video for a live one.";

export const sampleAnalysis: AnalysisResult = {
  schema_version: 1,
  duration_s: 65,
  claims: [
    {
      claim_id: "C1",
      text: "Adding a task increases the 'items left' counter.",
      status: "shown",
      explanation:
        "Frame F008 shows the counter updated to '2 items left' immediately after 'Prepare demo' was added to the list, compared to '1 item left' in earlier frames. This demonstrates the counter incrementing upon task addition.",
      evidence: [{ refId: "F008", kind: "frame", t: 16 }, { refId: "F010", kind: "frame", t: 18 }],
    },
    {
      claim_id: "C2",
      text: "The Active filter hides completed tasks.",
      status: "shown",
      explanation:
        "After clicking 'Active' filter (visible as selected in F013), the list shows only 'Buy milk' and 'Prepare demo' with the completed 'Book flights' task hidden, demonstrating the filter works in the live interface.",
      evidence: [{ refId: "F013", kind: "frame", t: 24 }, { refId: "F014", kind: "frame", t: 25 }, { refId: "F015", kind: "frame", t: 32 }],
    },
    {
      claim_id: "C3",
      text: "'Clear completed' removes all finished tasks.",
      status: "told_only",
      explanation:
        "The narrator states 'clear completed removes all finished tasks' (S07) and the cursor hovers over 'Clear completed' in F016/F018, but the video never shows the button being clicked and the completed task actually disappearing from the list.",
      evidence: [{ refId: "F016", kind: "frame", t: 33 }, { refId: "S07", kind: "speech", t: 34.88 }, { refId: "F018", kind: "frame", t: 52.8 }],
    },
    {
      claim_id: "C4",
      text: "Users get due-date reminders.",
      status: "told_only",
      explanation:
        "Frame F017 is a title card reading 'Coming soon: due-date reminders' — this is a slide announcing a future feature, not a working demonstration of reminders in the product.",
      evidence: [{ refId: "F017", kind: "frame", t: 43.333 }],
    },
    {
      claim_id: "C5",
      text: "Tasks can be exported to CSV.",
      status: "missing",
      explanation:
        "No mention or demonstration of CSV export appears anywhere in the frames or transcript.",
      evidence: [],
    },
  ],
};
