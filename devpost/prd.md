---
doc: prd
status: approved
---

# DemoTrace — Product Requirements

DemoTrace shows a hackathon participant which claims about their product the demo video actually *proves* and which it only *says*, with a click that jumps the video to the evidence.
Source: `scope.md > The Unique Kernel`, `scope.md > Who It's For`.

## The Core Journey
Source: `scope.md > The Core Loop`, `scope.md > What "Working" Looks Like`.

1. The author opens DemoTrace and lands on the Upload screen.
2. They drop a video of up to 3 minutes, or click **Try with sample** to skip the upload.
3. They write 3–5 claims about the product, each as something observable ("the user can do X and sees Y").
4. They start the analysis and see a clear status: first waiting to be processed, then analyzing.
5. The Results screen shows the video with a timeline under it, and one card per claim next to it, each marked **Shown**, **Told only** or **Missing**.
6. They click a timestamp on a card, or a marker on the timeline. The player jumps to that second and the related card is highlighted.
7. For every claim that is not Shown, they re-record the weak part and click **Re-check with new video**. It returns to the upload step with the claims already filled in, so they only drop the updated MP4.

Success: after the re-record, every claim is Shown, and each one has a click that lands on the exact moment where the feature works on screen.

## Screens and Layout
Four steps, one after another. No other screens are planned.

- **Upload** — a drop-zone for the video with the limits written in it (video up to 3 minutes, English narration only), a **Try with sample** button, and a line saying what happens to the video: *"Video is deleted right after processing. If processing fails, it is removed automatically within a few days."*
- **Claims** — 3–5 claim fields, with a hint to write an observable result.
- **Waiting** — the current status of the analysis in plain words, including "waiting to be processed" when other analyses are ahead.
- **Results** — the video player with an interactive timeline under it, and next to it one card per claim. A **Re-check with new video** button, and a visible note: *"AI assessment — click the evidence to verify."*

## Look and Feel
Source: `scope.md > Inspiration & Identity`. Direction set by the learner:

- **Character:** strict, utilitarian, an "engineering" tool — in the spirit of [Linear](https://linear.app), [GitHub Actions](https://github.com/features/actions) and [Raycast](https://www.raycast.com), not a colorful marketing landing page.
- **Colors:** a dark neutral base (zinc/slate: `#09090b`, `#18181b`). Color is used only for the meaning of the evidence:
  - **Shown** — emerald green `#10b981`
  - **Told only** — amber (warning) `#f59e0b`
  - **Missing** — ash neutral `#71717a`
- **Typography:** a strict sans-serif for the interface (Inter or the system sans-serif stack). Timestamps and status labels in a monospace font (JetBrains Mono or Geist Mono) to underline the precision of the seconds.
- **Avoid:** "magic" purple gradients, neon glow, and sparkle or star icons. This is a fact-checking tool, not "AI magic".

The tone from scope still holds: evidence over verdicts — no score, nothing that looks like a grade.

## Features and Behavior

### Upload
Source: `scope.md > The POC Boundary`.

- As a hackathon participant, I want to give DemoTrace my draft video so that it can be checked against my claims.
  - [ ] A video of up to 3 minutes can be dropped onto the drop-zone, and its name is shown after it is added.
  - [ ] The drop-zone itself states the limits (3 minutes, English narration only), and the line about video deletion is visible before anything is uploaded.
  - [ ] A video longer than 3 minutes is blocked before upload, with a clear error.
  - [ ] A video the browser cannot play (HEVC or MOV) gets a warning that suggests re-exporting as H.264 MP4.

### Try with sample
- As a judge or the author, I want to try DemoTrace in one click so that I can see what it does without a video of my own.
  - [ ] Clicking **Try with sample** opens the Results screen for a prepared sample video and its saved analysis, without uploading anything and without waiting.
  - [ ] Click-to-seek works on the sample exactly as it does on an analysis of the author's own video.

The sample is a demo aid only. Analysis of the author's own video must work too (`scope.md > What "Working" Looks Like`).

### Claims
- As a hackathon participant, I want to state what my product does so that DemoTrace checks exactly those points.
  - [ ] The analysis can start only with 3 to 5 claims filled in.
  - [ ] A visible hint tells the author to write an observable result, not a promise.

### Waiting for the analysis
- As a hackathon participant, I want to see what is happening so that I know it has not stalled.
  - [ ] After starting, the screen shows a status in plain words: waiting to be processed, then analyzing.
  - [ ] If the analysis cannot finish, the author sees a clear failure message instead of an endless wait, and can start again.

### Results and evidence
Source: `scope.md > The Unique Kernel`.

- As a hackathon participant, I want each claim marked Shown, Told only or Missing so that I know which parts of my demo do not prove anything yet.
  - [ ] There is exactly one card per claim. Each card holds: the claim as the author wrote it, a color-coded status badge, clickable timestamps (for example `[0:42]`, `[1:18]`, in monospace), and a short explanation of one or two sentences.
  - [ ] **Shown** means the result is visible on screen. The explanation says what exactly is visible.
  - [ ] **Told only** means the claim is made in speech or on a slide, but the result is not shown. A slide that promises a feature never counts as Shown. The explanation says why it is a slide, not a demonstration.
  - [ ] **Missing** means the claim is nowhere in the video.
  - [ ] No confidence percentage is shown anywhere. The author trusts the click on a timestamp, not a number.
  - [ ] Clicking a timestamp on a card moves the player to that second.
  - [ ] The timeline under the video has colored markers at the evidence moments. Clicking a marker moves the player to that second and highlights the related card. Clicking a timestamp on a card does the same in the other direction.
  - [ ] The note "AI assessment — click the evidence to verify" is visible on the Results screen.

### Re-checking after a re-record
- As a hackathon participant, I want to check a new version of my video without retyping my claims so that the loop from weak to Shown is quick.
  - [ ] The Results screen has a **Re-check with new video** button.
  - [ ] It returns to the upload step with the claims already filled in; the author only drops the updated video.

### Returning to a result
- As a hackathon participant, I want to come back to my analysis after closing the tab so that I do not lose it.
  - [ ] The claims and the analysis are remembered in the author's browser on that device.
  - [ ] If the tab is closed while the analysis is running, coming back resumes showing its status, and then the result.
  - [ ] After the analysis, reopening the page shows the saved report: cards, statuses, timestamps and explanations.
  - [ ] The video itself is not kept after processing. Reopening shows the saved report with the message "Drop the video file again to enable the interactive player". After the author drops the file, click-to-seek works again.

## States and Boundaries

- **First use** — the Upload screen with an empty drop-zone and the sample button.
- **No audio** — the analysis still runs. A claim made only on a slide can still be Told only.
- **Unsupported format (HEVC, MOV)** — a warning before the analysis, suggesting H.264 MP4.
- **Longer than 3 minutes** — blocked before upload, with a clear error that states the limit.
- **Non-English speech** — the proof of concept supports English only, and the drop-zone on the Upload screen says so.
- **Vague claim** — the hint on the Claims screen steers the author toward an observable result. No further handling is planned.
- **Static video, nothing changes on screen** — the analysis notes the absence of changes, and such claims come out as Told only or Missing.
- **The model refuses to answer, the analysis times out, or it fails** — a clear message that the analysis failed and the video will be removed automatically; the author can try again.
- **Daily limits reached** — a banner says the demo is at capacity and switches the author to the interactive sample.
- **Privacy** — the video is deleted right after processing, and the author's results are visible only to the person who started that analysis.
- **What persists between visits** — the claims and the saved report stay in the author's browser on that device. On another device, or after clearing the browser's data, they are gone. The video is never kept.

## Product Decisions

- Three statuses — Shown, Told only, Missing — because the point is to separate what a demo says from what it shows.
- A slide that promises a feature is Told only, not Shown — the promise is not proof.
- No numeric score and no confidence percentage — a percentage turns the tool into a judge and starts arguments about numbers; the author should trust a click on a timestamp, not a percent ("evidence over verdicts").
- DemoTrace labels its result as an AI assessment and asks the author to click the evidence — the model's output is not proven correct.
- Each claim card has the claim, a status badge, clickable timestamps and a one-to-two sentence explanation of what is visible, or why it is a slide rather than a demonstration.
- The timeline has colored evidence markers, and the link between marker and card works both ways.
- **Re-check with new video** returns to the upload step and keeps the claims — the author only drops the updated MP4.
- The browser keeps the claims and the text report, but the video is never stored and is deleted right after processing for privacy. On return, the interface honestly asks the author to drop the video file again to turn the player back on.
- Color is used only for the meaning of the evidence; no gradients, glow or sparkle icons — this is a fact-checking tool, not "AI magic".
- Video up to 3 minutes and 3–5 claims — a small, checkable proof of concept.
- English narration only — proof-of-concept boundary.
- Analysis of the author's own video must work; the sample is only a demo aid — the sample on its own would not prove the product.
- The video is deleted after processing and the interface says so plainly — the author can trust what happens to it.

## What We're Building
Source: `scope.md > The POC Boundary`.

- Analysis of a video up to 3 minutes against 3–5 claims.
- Three statuses with evidence: Shown, Told only, Missing, on claim cards with clickable timestamps and short explanations.
- Click-to-seek from a card's timestamp or a timeline marker to that moment, with the related card highlighted.
- **Try with sample**, on a prepared video with its saved analysis.
- **Re-check with new video**, which keeps the claims.
- Clear waiting and failure messages, resuming the status after the tab is closed, and the saved report on return.
- Deletion of the video after analysis.
- The visual direction described in Look and Feel.

## Deferred From the POC
Source: `scope.md > The POC Boundary`.

- Frame thumbnails — nice-to-have, the first to go; a text timestamp is enough.
- Export of the report to Markdown — nice-to-have, the first to go.
- Accounts and history — implied by re-checking, but the proof works without them; the browser only keeps the latest analysis on that device.
- Sharing by link — implied by showing results to others, out until the core is proven.

## Possible Later Enhancements
Source: `scope.md > Later`.

Script generation, video editing, collaboration, YouTube links, voice and gestures, comparing videos, suggesting claims automatically.

## Non-Goals
Source: `scope.md > Explicitly Cut`.

- No numeric score and no confidence percentage — the point is evidence, not a grade.
- No proof that the AI's assessment is correct — the author verifies by clicking the evidence.
- No non-English speech in the proof of concept.
- Not a tool for judges — DemoTrace works for the author before submission.

## Open Questions
None. The questions raised earlier — card contents, timeline, re-checking, closing the tab, look and feel — are answered above. How the browser stores the saved report is a `4-spec` matter.
