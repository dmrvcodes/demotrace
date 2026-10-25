# DemoTrace — Video Demo Run Sheet

This is a capture plan, not a spoken script. The submission owner supplies the
spoken words in their own voice. Keep the edit under 90 seconds and make every
screen shown in it an actual product state.

## Prepare before recording

1. Use a clean browser profile or clear only `demotrace:last-analysis:v1` in
   DevTools. Keep the production site at
   [demotrace.vercel.app](https://demotrace.vercel.app), not localhost.
2. Prepare two owned, H.264 MP4 files, each 20–45 seconds and under 150 MB.
   They must show the same TodoMVC flow and support these three claims:

   ```text
   Creating a task increases the items-left counter.
   Selecting Active hides completed tasks.
   Clear completed removes completed tasks.
   ```

   In `weak.mp4`, narrate or hover over **Clear completed** but never click it.
   In `revised.mp4`, perform that click and show the completed item disappear.
   Do not use a promise slide in either recording: the contrast needs to be a
   visible action versus a claim that is merely said.
3. Run `weak.mp4` through the deployed app before the screen recording. Keep
   its completed result open. It must contain two **Shown** cards and one
   **Told only** card. If Claude produces a different verdict, correct the
   footage or claims and run it again; do not stage a result.
4. Start the recorder at 1440×900 or 1920×1080. Hide bookmarks, account names,
   DevTools, terminals, AWS/Vercel dashboards, API errors, job tokens, and
   notifications. Zoom the browser to a readable 100–110%.
5. In a second take, run `revised.mp4` through the real deployed flow. Wait for
   the real completion; it is legitimate to cut out the wait, but never to
   replace the result with the sample. Its third card must be **Shown** before
   you use this take.

## Capture sequence — 75 to 90 seconds

| Time | Screen action | What this shot proves | Your own spoken beat |
| --- | --- | --- | --- |
| 0–4 s | Open the production home screen. Leave `LIVE ANALYSIS` visible. | This is the deployed product, not a mock or local fixture. | Give the project name and the one-sentence problem in your own words. |
| 4–10 s | Show the upload card, then the three short observable claims. | The input is a video plus testable claims, not a generic video summary. | Explain that the product distinguishes a proved outcome from a promise. |
| 10–14 s | Briefly show the live waiting state from the real `weak.mp4` job. | A real analysis was submitted to the backend. | State only what the viewer is about to inspect; do not make model-accuracy claims here. |
| 14–29 s | Cut to the completed `weak.mp4` Evidence map. Point to the two **Shown** cards, then open the **Told only** `Clear completed` card. | The system does not give credit merely for narration or a hover. | Describe the visible distinction between an executed result and a claim that was only said. |
| 29–37 s | Click a timestamp on a **Shown** card. Let the local player seek and visibly show the counter/filter state. | Evidence is grounded in a precise moment, not an unsupported label. | Call out that the timestamp is actionable evidence. |
| 37–46 s | Click **Re-check with new video**. Show the existing three claims still present, select `revised.mp4`, and start the new live analysis. | The intended feedback loop keeps the criteria while the author improves the demo. | State the author action in your own words: fix the weak proof, not the claim wording. |
| 46–51 s | Briefly show the genuine live waiting state for `revised.mp4`. | This is a new job, not the saved report. | No extra narration required. |
| 51–54 s | Use a hard cut only after that exact job has completed. Optionally add a neutral editor caption such as `after the live analysis completed`. | The edit removes idle time without fabricating a result. | No narration required. |
| 54–70 s | Show the completed revised Evidence map. Open the now-**Shown** `Clear completed` card and click its evidence timestamp; show the actual removal in the player. | The same criterion changed from Told only to Shown because the revised video proves it. | Close the core story in your own words. |
| 70–82 s | Keep the evidence map in view; optionally scroll the three status cards and finish on the live header. | The judge can see the concrete outcome and the public app URL. | Give your own closing and invite the judge to try the deployed app. |

## Editing rules

- Keep the status badges and claim text readable for at least two seconds.
- A cut may remove processing time, never alter job status, card text, evidence
  timestamps, or the player state. Use a hard cut rather than a fake progress
  animation.
- Do not show **Try with sample** as if it were the live flow. It is acceptable
  only as a 2–3 second fallback after the main proof and must retain its
  `Recorded analysis · sample` label.
- Do not show credentials, source video content you cannot publish, personal
  account information, AWS dashboards, raw API responses, or terminal output.
- Record a silent backup take of the same screen sequence. It makes later voice
  replacement and subtitles possible without changing the evidence.

## Pre-submit playback check

- The product name and live URL are legible.
- `weak.mp4` shows **Told only** for the unperformed action.
- `revised.mp4` shows **Shown** for that same action.
- At least two timestamp clicks visibly seek the player.
- The recording shows a real live waiting state for each run and no sample is
  labelled as live.
- No secrets or personal data are visible.
