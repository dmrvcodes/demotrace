# DemoTrace — final demo-video run sheet (v3)

**Target export:** 2:28, 1920×1080, H.264 + AAC MP4, English narration with an `.srt`
(the hackathon limit is under 3:00; keep 20+ seconds spare).
**Narration:** the script in this sheet, voiced with Amazon Polly **Nate** (generative engine) —
chosen by the submission owner on 26 Oct as the author's voice: an ordinary, non-announcer voice.

## The story in one line

> People judge your product from your demo video. DemoTrace shows which claims that video
> actually proves — and, when one isn't, exactly what to re-record.

The video is built around **one real demo being fixed**, not a feature tour:

1. **What and for whom** — the problem, the audience, the value in one sentence.
2. **Prove it on a real demo** — what the demo contains, a live check, every verdict opened
   at its moment, the gap found, and the change made to the recording.
3. **Prove the fix** — the same claims on the re-recorded demo, live, now all Shown.
4. **Value again** — before → after, why the verdict can be trusted, call to action.

## Audience and value (say it once, show it, repeat it at the end)

| Who | Why a demo video decides for them | What DemoTrace gives them |
| --- | --- | --- |
| Hackathon builders | Judges often score from a 3-minute video and may never run the code. | Every claim in the video backed by a moment on screen before submitting. |
| Founders and PMs | Investors and customers watch the demo before trying the product. | A demo that shows the result instead of promising it. |
| DevRel and sales engineers | Product walkthroughs are reused for months. | A quick check that each walkthrough proves what the copy says. |

Value statement used in the card and the narration:
**"Check what your demo actually proves — before anyone judges it."**

## Material

| Asset | Content | Must be true |
| --- | --- | --- |
| `weak.mp4` (v1, 30 s) | TodoMVC: add a task (0:06, counter 1 → 2), Active filter (0:10.5), All (0:15.5), hover **Clear completed** from 0:18 while the narration says "And Clear completed removes completed tasks." (0:19–0:21.6). Never clicked; the completed task stays. | Live check returns C1 Shown, C2 Shown, **C3 Told only**. |
| `revised.mp4` (v2, 30 s) | Same flow and narration; **Clear completed** is clicked at 0:20.6 with a 1.2 s click ring, the completed task disappears and the list is held unchanged to 0:30. | Live check returns **all three Shown**; C3 evidence includes ~0:21. |
| Production take | One continuous 1920×1080 recording of https://demotrace.vercel.app (browser zoom 125%, no digital zoom) running both live jobs. | Both jobs are genuine; no sample, saved report or fixture appears. |

The three claims, typed identically for both runs:

```text
Creating a task increases the items-left counter.
Selecting Active hides completed tasks.
Clear completed removes completed tasks.
```

## Production-take choreography

Record one continuous take; the edit may hard-cut waiting time but never reorder actions or
change a job's outcome.

| Step | Action in the browser | Mark |
| --- | --- | --- |
| 1 | Load the site, hold 4 s on Upload (`LIVE ANALYSIS` visible). | `home` |
| 2 | Glide to **Choose video**, select `weak.mp4`; claims screen opens. | `weak_claims` |
| 3 | Click each claim field and type the three claims (≈28 ms/char). Click **Start analysis**. | `weak_start` |
| 4 | Leave the waiting screen alone until the result renders. | `weak_waiting`, `weak_results` |
| 5 | Hold 5 s on the evidence map with the cursor away from the cards. | — |
| 6 | **C1:** click the evidence timestamp nearest 0:06, click the player to play ~2.5 s, click to pause. | `weak_c1` |
| 7 | **C2:** evidence nearest 0:11, play ~2 s, pause. | `weak_c2` |
| 8 | **C3:** evidence nearest 0:19, play ~3.5 s (the hover and the spoken line), pause; rest the cursor on the C3 explanation for 6 s. | `weak_c3` |
| 9 | Click **Re-check with new video**, select `revised.mp4`, hold 2.5 s on the retained claims, **Start analysis**. | `recheck`, `revised_start` |
| 10 | Wait for the result; hold 3 s on the map. | `revised_waiting`, `revised_results` |
| 11 | **C3:** evidence nearest 0:21, play ~2.5 s (the click and the removal), pause; hold 4 s. | `revised_c3` |

Scroll the claim list with a visible wheel scroll if an evidence button is below the fold;
never click an off-screen target. The page keeps the last active card highlighted after
Re-check — that is current product behaviour, not something to hide.

## Time-coded cut (2:28, as built)

Narration lines are in the next section; `src` means the demo's own soundtrack.

| Time | Picture | Audio | What it proves |
| --- | --- | --- | --- |
| **ACT 1 — what and for whom** | | | |
| 0:00–0:11 | `weak.mp4` 0:13–0:24 in a framed insert labelled **A PRODUCT DEMO · V1** (its spoken line lands at 0:06, after N1). | N1, then `src` "And Clear completed removes completed tasks." | A real demo making a confident claim. |
| 0:11–0:24 | **Value card**: headline, three audience chips, the flow (upload → claims → Shown / Told only / Missing + the moment). | N2 | Who it is for and why it matters. |
| **ACT 2 — prove it on a real demo** | | | |
| 0:24–0:33 | **Storyboard card**: three real frames of v1 at 0:06, 0:11, 0:19 with neutral captions (adds a task · filters to Active · talks about Clear completed). Do not reveal the missing click here. | N3 | What the demo contains, before DemoTrace looks at it. |
| 0:33–0:47 | Production take steps 1–3; URL chip `demotrace.vercel.app · public production site` for the first 3.6 s. | N4, N5 | Real public site, real upload, claims as tests. |
| 0:47–0:52 | Genuine waiting screen of the v1 job. | N6 | The job is live. |
| 0:52–0:54 | Neutral card: `live analysis completed`. | — | Hard cut over processing time, labelled. |
| 0:54–1:01 | Evidence map of v1, all three cards readable. | N7 | Two Shown, one Told only. |
| 1:01–1:08 | Step 6: C1 evidence → player jumps and plays the counter change. | N8 | Evidence is a moment you can open. |
| 1:08–1:14 | Step 7: C2 evidence → the filter hides the completed task. | N9 | Second claim proven on screen. |
| 1:14–1:27 | Step 8: C3 evidence → player plays the hover while the demo says the line; hold on the Told only explanation. | `src` under the play window, then N10 | The gap: said, never shown working. |
| 1:27–1:37 | **Fix card**: v1 and v2 side by side, 0:17–0:27 of each, whole frames scaled to fit. Left **V1 · hovered, never clicked** with its Told only badge; right **V2 · re-recorded with a click**, no badge (not checked yet). | N11 | The change made to the recording, not to the claims. |
| **ACT 3 — prove the fix** | | | |
| 1:37–1:48 | Step 9 + 3 s of the genuine waiting screen of the v2 job. | N12 | Same claims retained; second live run. |
| 1:48–1:50 | Neutral card: `live analysis completed`. | — | |
| 1:50–2:04 | Steps 10–11: v2 map, C3 now **Shown**; its evidence plays the click and the removal. | N13 | Same claim, changed verdict, moment-level proof. |
| **ACT 4 — value again** | | | |
| 2:04–2:14 | **Before → after card** built only from the two genuine reports: v1 *Shown 2 · Told only 1* → v2 *Shown 3*; under it: *found in one live check · fixed with one re-record*. | N14 | The benefit, stated with real numbers. |
| 2:13–2:22 | **Trust card** (250 ms dissolve in): Claude suggests a verdict and evidence IDs → DemoTrace validates every reference and computes timestamps → you open any verdict at its moment. | N15 | Why the verdict can be trusted. |
| 2:22–2:28 | **End card** (250 ms dissolve): DemoTrace, value line, `demotrace.vercel.app`, `github.com/dmrvcodes/demotrace`. | N16 | Call to action. |

## Narration script (Polly Nate, generative)

Start times are from the built cut; generative voices vary slightly per synthesis, so
re-check for overlaps after re-voicing (keep 0.2 s between lines).

| ID | Starts | Line |
| --- | --- | --- |
| N1 | 0:00.3 | If you build products, people often judge your demo video before they ever touch your product. |
| N2 | 0:11.4 | DemoTrace is for hackathon builders, founders and DevRel teams. You upload your demo and the claims it makes, and it shows which claims the screen actually proves, and the exact moment that proves them. |
| N3 | 0:24.5 | Here's my demo, version one. I add a task, I filter to active tasks, and I talk about Clear completed. |
| N4 | 0:33.4 | I upload it to DemoTrace and write three claims, as results you should be able to see on screen. |
| N5 | 0:40.2 | Each claim is a test the video has to pass. |
| N6 | 0:47.2 | It reads the frames and the transcript. This is a live run. |
| N7 | 0:54.4 | Two claims pass. One doesn't. |
| N8 | 1:01.6 | Click any evidence, and the video jumps to that moment. Here, the counter goes up. |
| N9 | 1:07.8 | And here, the filter hides the completed task. |
| N10 | 1:19.1 | But this one is only told. I say it, but the list never changes. Nobody watching would see it work. |
| N11 | 1:28.3 | So I fix the recording, not the pitch. Same flow, but this time I actually click it. |
| N12 | 1:37.9 | Same claims, new video, another live check. |
| N13 | 1:55.0 | Now all three claims are shown, and the proof is the exact moment the task disappears. |
| N14 | 2:04.3 | That's the point. Before anyone judges your demo, you know every claim is backed by something on screen, or exactly what to re-record. |
| N15 | 2:14.0 | Claude suggests the verdicts, DemoTrace verifies every reference, and you can check each one with a click. |
| N16 | 2:22.5 | Try it on your next demo, at demotrace dot vercel dot app. |

N10 starts right after the demo's own line in the 1:14 window, so the viewer hears the
claim being *said* first and then why that is not proof. It is worded to stay true whatever
the model's explanation says about the cursor: the observable fact is that the list never
changes.

## Editorial cards

All cards: background `#09090b`, text `#f4f4f5`, muted `#a1a1aa`; green `#10b981` only for
Shown/validated, amber `#f59e0b` only for Told only. Static, readable, no animation beyond
the two dissolves.

- **Value card** — headline *"Check what your demo actually proves — before anyone judges it."*;
  chips *Hackathon builders · Founders & PMs · DevRel & sales engineers*; flow
  *Upload your demo → List the claims it makes → Each claim: Shown / Told only / Missing, linked to its moment*.
- **Storyboard card** — three frames exported from `weak.mp4` (not mock-ups) with timestamps.
- **Fix card** — two synchronized clips; only v1 carries a status badge.
- **Before → after card** — counts copied from the two genuine reports of the final take.
- **Trust card** — three steps, one line each; no service names, accounts, keys or token counts.
- **Neutral cut card** — `live analysis completed`, 2 s.
- **URL chip** — top-left over the first 3.6 s of the production take.

## Non-negotiables

- Both analyses are genuine jobs from the same take; the sample never appears.
- No digital zoom or crop of the product screen (browser zoom 125% only). The fix card may
  scale the demo clips to fit side by side; it must not crop away the list or the button.
- No result is edited, re-typed, re-ordered or re-labelled. Counts on the before → after
  card are copied from the two reports.
- Hard cuts only over waiting time, each labelled by the neutral card; no time-lapse.
- The demo's own soundtrack is used only in the v1 insert and under the C3 play window;
  the Shown play windows stay silent apart from narration.
- No music, no credentials, job tokens, consoles, terminals or raw API responses on screen.

## Recovery plan

| Problem | Correct response |
| --- | --- |
| v1 C3 comes back **Shown** | Re-record `weak.mp4` with the hover further from a click (no press at all); re-run both jobs in a new take. Never weaken the claim. |
| v2 C3 comes back **Told only** | Observed once on 26 Oct when the click fell between frame samples. Re-record `revised.mp4` with the click mid-second, a longer click ring and a longer hold on the changed list; re-run the take. |
| C1 or C2 is not Shown | Re-record the source with a longer hold after the action; re-run. |
| An evidence button is below the fold | Wheel-scroll it into view on camera, then click. |
| Live job slow or failing | Hold the waiting screen 5 s, cut with the neutral card after a genuine completion. On an API error stop the take, fix production, start again. |
| Text unreadable at 1080p | Keep browser zoom at 125%; do not add digital zoom. |
| The model's explanation words something differently from the narration | Never edit the model output; reword the narration so it states only what is observable on screen, re-voice, re-check overlaps. |

## Export and upload checklist

- [ ] 1920×1080 H.264, AAC, ≈2:28, under the 3:00 limit.
- [ ] Act order kept: value → proof on v1 → fix → proof on v2 → value again.
- [ ] Every evidence click in the cut visibly seeks and plays the player.
- [ ] v1 C3 **Told only**, v2 C3 **Shown**, both from the same genuine take.
- [ ] `demotrace.vercel.app` readable in the first 45 seconds and on the end card.
- [ ] `.srt` matches the narration; uploaded to YouTube as **Public**; checked signed out.
- [ ] Description, attribution (TodoMVC demo app at demo.playwright.dev, Amazon Polly voice)
      and Devpost fields written by the submission owner.
