# DemoTrace — final demo-video director's script

**Target export:** 1:35–1:50, 1920×1080 H.264 MP4. The video must prove the
complete author loop — an unproven claim is found, the recording is fixed, and
the same claim becomes proven. Spoken narration is written and recorded by the
submission owner; this document prescribes the exact visual sequence, proof
points, and narration intent.

The final cut demonstrates a real production analysis first. A recorded sample
is useful for judges who open the website without a video, but it is not the
hero path and must never be represented as a live result.

## Editorial decision: the story is one changed verdict

Do not make the video a feature tour, a Lambda walkthrough, or a list of AWS
services. The strongest proof is one stable criterion with two honest outcomes:

```text
Weak recording     “Clear completed removes completed tasks” → TOLD ONLY
Revised recording  “Clear completed removes completed tasks” → SHOWN
```

Everything in the edit serves that contrast. The first video says or hints at
the feature but never performs it. The revised video performs the same action
and leaves the resulting state visible. This is the product's difference:
DemoTrace marks what the screen proves, not what the narrator promises.

## Before recording

1. Work at [demotrace.vercel.app](https://demotrace.vercel.app), never
   localhost. Start in a clean browser profile, or remove only
   `demotrace:last-analysis:v1` in DevTools before the first take.
2. Create two publishable, owned H.264 MP4 files, each 20–45 seconds and under
   150 MB. Use the same TodoMVC state and the exact same three claims:

   ```text
   Creating a task increases the items-left counter.
   Selecting Active hides completed tasks.
   Clear completed removes completed tasks.
   ```

   `weak.mp4`: add a task and apply Active; narrate or hover over **Clear
   completed**, but never click it. Keep a completed task in the list.

   `revised.mp4`: perform the same first two actions; click **Clear completed**
   and hold the frame where the completed task has actually disappeared. Do not
   use a promise slide: this comparison is action-versus-claim, not a slide
   test.
3. Run both files through the live site before recording. Keep both completed
   reports open in separate browser profiles or tabs with their respective
   local source files attached. Validate the cards manually:

   | File | Required result |
   | --- | --- |
   | `weak.mp4` | Claim 1 and 2 are **Shown**; claim 3 is **Told only**. |
   | `revised.mp4` | All three claims are **Shown**; claim 3 cites the actual removal. |

   If either report differs, change the footage or the observable claim and
   re-run it. Never edit, crop, rename, or stage a model result to fit this
   script.
4. Record the browser at 1920×1080 or 1440×900. For the first two seconds,
   leave enough browser chrome visible to establish the public URL; then use a
   stable 16:9 crop of the site. Set browser zoom to 100–110% so card text and
   status badges are readable.
5. Close notifications and hide bookmarks, account names, DevTools, terminals,
   AWS/Vercel consoles, request payloads, job tokens, error traces and any
   source footage you cannot publish. Do not record an API failure as part of
   the hero take.
6. Record the voice-over separately. Add readable subtitles if the final
   platform supports them. Do not use background music that competes with card
   copy or carries a licensing risk.

## Browser choreography

Use a deliberate clean take. Each state below must be genuine; a hard cut may
remove model waiting time but may not change the interaction order or the
outcome of a job.

| Moment | Exact action | Expected visible state |
| --- | --- | --- |
| Open | Load the production URL. | `LIVE ANALYSIS` is visible; Upload is the first screen. |
| Weak claims | Select `weak.mp4`, then enter the three fixed claims. | The claims form contains the same criterion that will be tested again. |
| Weak job | Click **Start analysis**. | The live waiting state appears. |
| Weak result | Let the actual job complete, then open the result. | Claims 1–2 are **Shown**; claim 3 is **Told only**. |
| Ground evidence | Click a Claim 1 or Claim 2 evidence timestamp. | The player seeks to the cited counter/filter change and the active card is highlighted. |
| Keep criteria | Click **Re-check with new video**. | Upload returns with all three claims retained. |
| Revised job | Select `revised.mp4`, then click **Start analysis**. | A new live waiting state appears. |
| Revised result | Let the actual job complete, then open the result. | Claim 3 is now **Shown** with evidence at the removal moment. |
| Ground revised evidence | Click Claim 3's evidence timestamp. | The player seeks to the click and removed completed task. |

If focus, file, job, claims, or the resulting status differs from this table,
do not try to repair it in-frame. Return to the prepared state and restart that
take. The final cut may join clean genuine takes, but must not imply that a
sample, saved report, or prior job is the current live job.

## Time-coded cut and narration intent

The **Narration intent** column is not a voice-over script. In your own words,
say only the point in that cell; do not read model explanations or UI labels
aloud. Leave result cards long enough to read.

| Final time | Show exactly | Narration intent | Required proof |
| --- | --- | --- | --- |
| **0:00–0:07** | Full-screen weak-result Evidence map. Hold the **Told only** badge and the claim text `Clear completed removes completed tasks.` | Frame the author-side problem: polished demos can claim a result the recording does not prove. | The first image establishes the concrete failure, not an abstract feature list. |
| **0:07–0:15** | Production home screen, with `LIVE ANALYSIS` and the public URL readable for two seconds. Then show the MP4 selected in Upload. | Name the product and identify its input: a demo video plus observable claims. | Public deployment and the real analysis entry point are visible. |
| **0:15–0:25** | The three claims form, then click **Start analysis** for `weak.mp4`. | Explain that claims are test criteria, not prompts asking the model to praise a demo. | The unchanged third claim is visible before both runs. |
| **0:25–0:30** | Genuine Waiting screen for the weak job. | State that the video is being analyzed live. Do not claim universal accuracy or expose internal logs. | The job is not a fixture or pre-filled sample. |
| **0:30–0:44** | Cut to the actual completed weak report. Hold claim 3's **Told only** card and its explanation. | Explain why narration/hover is insufficient: the action and result must appear on screen. | The product's key distinction is legible. |
| **0:44–0:53** | Click evidence on a **Shown** counter/filter card. Hold the player after it seeks and the card remains highlighted. | Explain that verdicts are tied to a specific moment rather than a generic summary. | Click-to-seek evidence works in the product. |
| **0:53–1:03** | Click **Re-check with new video**. Show that all three claims remain. Select `revised.mp4` and start its analysis. | State the improvement loop: fix the proof in the recording while holding the criterion constant. | The exact claim persists from weak to revised. |
| **1:03–1:08** | Genuine Waiting screen for the revised job. | No additional point is needed; allow the new job state to be visible. | The second run is independent and live. |
| **1:08–1:10** | Hard cut only after this job is complete. Optional neutral editor card: `after the live analysis completed`. | No narration. | The cut removes idle processing time without fabricating a state. |
| **1:10–1:25** | Open the revised Claim 3 card, now **Shown**. Click its evidence; hold the player where Clear completed has removed the task. | Close the core contrast: the verdict changed because the screen now proves the same claim. | Same claim, changed video, changed evidence-backed verdict. |
| **1:25–1:37** | Full-screen editorial Evidence Path card described below. | In one concise sentence, connect the product result to its guardrail: the model may suggest evidence, but the system validates references and computes timestamps. | Innovation is visible without turning the product screen into a developer console. |
| **1:37–1:47** | Return to the revised Evidence map, then a static end card with `DemoTrace`, public URL, and GitHub repository. | Give your own closing and invite a judge to try the live app. | The viewer leaves with the working product, not infrastructure labels. |

## Editorial Evidence Path — 1:25–1:37

This is the only architecture insert. It is an editorial card, not product UI:
opaque zinc-black background (`#09090b`), primary text `#f4f4f5`, muted text
`#a1a1aa`, green `#10b981` only for validated output. It must remain readable
and static after a short 250 ms dissolve.

```text
Owned MP4
    ↓
Frames + transcript ──→ Claude proposes verdict + evidence IDs
                                    ↓
                         DemoTrace validates IDs
                         computes timestamps itself
                                    ↓
                         SHOWN / TOLD ONLY / MISSING
                         click → exact video moment
```

- Keep the statement to one line: **“Evidence is validated before it becomes a verdict.”**
- Do not animate each service, show AWS account details, or list Lambda, S3,
  DynamoDB, Terraform, keys, or token counts. Those details belong in README
  and the repository.
- The card must not claim the model is deterministic or perfectly accurate. It
  explains the verification boundary, not a benchmark.

## Final-edit constraints

- Use hard cuts for real product state changes. Use one 250 ms dissolve only
  into and out of the Evidence Path card. Do not fade through a blank screen.
- Keep each badge and claim readable for at least two seconds. Never digital
  zoom so far that a status label, evidence timestamp, or the player state is
  cropped away.
- One idea per frame: do not overlay architecture labels, captions and a full
  result card simultaneously.
- The sample is a fallback only. If it appears, keep `Recorded analysis ·
  sample` visible and never transition from it into the revised live result as
  though they belong to one job.
- A time-lapse is not permitted for the live processing phase. A hard cut after
  a genuine completion is permitted and should be labeled neutrally if the cut
  could be misunderstood.
- Do not leave a silent static screen for more than four seconds, except the
  five-second final end card. Use no copyrighted music unless you can attribute
  and redistribute it.

## Recovery plan

| Failure before export | Correct response |
| --- | --- |
| Weak third claim returns **Shown** | Re-record `weak.mp4` so the action is never completed. Do not weaken the claim text after the fact. |
| Revised third claim is not **Shown** | Re-record it with a clearly visible click and a longer hold on the changed list state; re-run live analysis. |
| Live job is slow | Record Waiting for five seconds, then wait off-camera for its true completion and use the permitted hard cut. |
| Daily capacity / external API error | Stop the take, resolve the live environment, then start again. Do not substitute the sample for this proof. |
| Result card text is unreadable at final resolution | Increase browser zoom or crop the stable 16:9 capture; do not create a post-production replacement card. |
| HEVC upload warning | Re-export the source video as H.264 before recording. The warning is a product safeguard, not part of the hero narrative. |

## Export and upload checklist

- [ ] H.264 MP4, 1920×1080, clear narration or subtitles, no unlicensed music.
- [ ] Final duration is within the hackathon's current video limit, with 10+
      seconds spare for platform re-encoding or metadata.
- [ ] The production URL is readable in the first 15 seconds and the end card.
- [ ] Weak and revised results are distinct real jobs; neither is the sample.
- [ ] Claim 3 is **Told only** in the weak take and **Shown** in the revised
      take; two evidence clicks visibly seek the local player.
- [ ] No credentials, account data, private video, job token, terminal, or raw
      API response is visible.
- [ ] Playback was checked after upload while signed out or in a private window.
- [ ] Video description, attribution, repository URL and Devpost fields are
      written by the submission owner.
