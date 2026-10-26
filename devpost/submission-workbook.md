# DemoTrace — Devpost submission workbook

This is the final owner checklist for the **Build With AI: Basics** Devpost
form. The project owner writes the public story, elevator pitch, survey answers
and final submission in their own words. This workbook provides verified facts,
field-by-field constraints, and an ordering that makes the submission stronger
without inventing personal experience.

## Verified links and facts to use

| Item | Verified value |
| --- | --- |
| Live application | [https://demotrace.vercel.app](https://demotrace.vercel.app) |
| Public repository | [https://github.com/dmrvcodes/demotrace](https://github.com/dmrvcodes/demotrace) |
| Open-source licence | [LICENSE](https://github.com/dmrvcodes/demotrace/blob/main/LICENSE) |
| Public video | [YouTube — DemoTrace](https://www.youtube.com/watch?v=R_W9WrFR5QY) |
| Video duration | 2:28 |
| Quality evidence | Six real Lambda → Claude recordings; 27 claims; 100% status accuracy, 100% evidence hits, 0/16 false Shown. This is a small hand-labelled smoke eval, **not** a general accuracy claim. |
| Privacy behaviour | Per-job bearer tokens; video is uploaded with presigned POST, Worker uses the pinned S3 version, and deletes every version after download. |
| Evidence boundary | Claude proposes structured verdicts/evidence IDs; DemoTrace validates IDs and computes timestamps server-side before rendering a verdict. |

Before entering any field, replay the published video through the end. Its final
spoken URL must be clearly `demotrace.vercel.app`, with one `l` in `vercel`.
Auto-generated captions currently render this ambiguously, so correct the video
or its captions if a judge could hear or read a different domain.

## 1. Project overview

### Project name

`DemoTrace` is already entered. Keep the single product name consistently in
the thumbnail, video title, Devpost heading, README and application.

### Elevator pitch — 200 characters

Write one sentence from these parts, in this order:

```text
Who has the problem → what they provide → the concrete outcome → why it differs
```

Use the product's exact vocabulary: **demo video**, **observable claims**,
**Shown / Told only / Missing**, and **timestamped evidence**. Avoid words such
as “revolutionary”, “AI-powered” without the outcome, “judge”, “score”, or
unqualified accuracy claims. Verify the final character count in Devpost.

### Thumbnail

Use a 3:2 PNG/JPG, less than 5 MB. It should show, in one readable frame:

```text
DEMO TRACE
Does your demo show it — or only say it?
SHOWN   TOLD ONLY   MISSING
```

Use the actual product dark zinc background, `#10b981` green and `#f59e0b`
amber. Do not use a generic robot, stock photo, AWS logo collage, or a tiny
browser screenshot that cannot be read in a gallery card.

## 2. Project details — public project page

### About the project

Write a short Markdown story with six compact sections. It should read as a
coherent product story, not as a list of services.

| Section | Owner-written content to cover | Evidence to link or show |
| --- | --- | --- |
| `## Why` | The moment a product gets judged from a demo before anyone can try it; distinguish a promised feature from an observable result. | First 7 seconds of the video. |
| `## What DemoTrace does` | MP4 + 3–5 observable claims → Shown / Told only / Missing evidence map; clicking evidence seeks the local player. | Live app and video. |
| `## The improvement loop` | A weak recording gets a Told only verdict; the author re-records the same criterion; a revised recording gets Shown. | Video’s `Clear completed` story. |
| `## How it works` | Browser uploads directly to S3; Worker extracts frames/transcript; Claude returns structured candidates; server validation controls timestamps/evidence; report stays available without retaining the video. | README architecture diagram. |
| `## What we measured` | State the six-case smoke-eval numbers with their limitation; include the cost/time measurement only if you can stand behind it from `spec.md`. | [`README.md`](../README.md) Evaluation section. |
| `## Challenges and learning` | The actual Bedrock block, direct Anthropic adaptation, need to test false Shown outcomes, and what planning/eval discipline changed. | `scope.md`, `prd.md`, `spec.md`, `checklist.md`. |

Required links to include in the story or `Try it out` section:

- live app: `https://demotrace.vercel.app`
- source: `https://github.com/dmrvcodes/demotrace`
- demo: `https://www.youtube.com/watch?v=R_W9WrFR5QY`

Do not claim that video is permanently stored, that the model is perfectly
accurate, that the evaluation is a benchmark, or that the app decides winners.

### Built with

Use only technologies actually in the repository. Recommended tags, in priority
order, are:

```text
TypeScript, Next.js, Python, Tailwind CSS,
AWS Lambda, Amazon S3, Amazon DynamoDB, Amazon ECR,
Terraform, Anthropic Claude, faster-whisper, ffmpeg,
Vercel, GitHub Actions, GitHub Actions OIDC
```

Remove any tag Devpost does not recognise rather than substituting an inaccurate
one. Do not tag Bedrock: production inference uses the direct Anthropic API.

### Try it out, media and video

1. Add the live application first, then the GitHub repository as two `Try it
   out` links.
2. Put the public YouTube URL in **Video demo link**:
   `https://www.youtube.com/watch?v=R_W9WrFR5QY`.
3. Add 3–5 gallery images only if each communicates a distinct proof:
   upload/claims; weak `Told only` result; evidence click-to-seek; revised
   `Shown` result; optional simple Evidence Path diagram. Use 3:2 images below
   5 MB, never sensitive video or terminal/console screenshots.
4. Preview the public project page in an incognito window before final submit.

## 3. Additional info — judges and organisers

Answer every personal/survey field truthfully. Do not select an option because
it sounds better. The substantive fields should draw from the verified facts
above, but the owner must supply personal experience.

| Devpost field | What to do |
| --- | --- |
| Submission type | Select the factual status: Individual or Team. |
| Country of residence / organisation | Enter your actual current details. Organisation remains empty if it does not apply. |
| Learn activities used | Select only sessions/resources you actually used; do not infer from project work. |
| AI cost impact | Select the option matching your experience. The project adapted after Bedrock access was blocked and used an authorised direct Anthropic credential; choose a cost option only if that fact genuinely affected your decisions. |
| Confidence with coding agents | Select your real post-project confidence, not the maximum for optics. |
| “Fix one thing” feedback | Describe one concrete friction you genuinely experienced, its impact, and a proposed improvement. |
| Value created | Select only actual value. If “Let me do something I couldn't do before” is true, anchor it in finding unproven demo claims with timestamped evidence. |
| More about project value | State the personal outcome in your own words; connect it to the before/after recording loop, not generic productivity. |
| Main technology requirement | Explain the real path: Learn Skill Pack planning (`scope.md` → `prd.md` → `spec.md`), ordered build checklist, live verification/eval, revisions after evidence, final review. Mention flipped interaction only to the extent it actually describes your process. |
| Licence URL | Paste `https://github.com/dmrvcodes/demotrace/blob/main/LICENSE`. |
| Eligibility confirmations | Read the official rules and check them only if true for you/all teammates. |

## 4. Finish the skill pack truthfully

### Early hands-on checkpoints

They remain unticked. `checklist.md > Revisions` records why: scheduled learner
exploration did not happen at slices 5 and 8, so it is not retroactively claimed
as learner feedback. Mechanical and production evidence remains recorded
separately.

### Kick-the-tires — owner action

Do the following on the production site with a video you are allowed to upload:

1. Open **Try with sample** and click an evidence timestamp.
2. Select an HEVC MP4 and observe the re-export warning.
3. Start a live analysis, reload while it is Processing, then after completion
   reload again, reattach the same local file, and click evidence.
4. Use **Re-check with new video** and confirm the claims remain.

Then record your own factual feedback in one short paragraph: what worked, what
was unclear, and what you would change. A real “no blockers; ready to ship” is
valid feedback only if it is your actual conclusion.

### Learning wrap-up — owner action

Trace the actual deployment incident using `infra/main.tf` and the deployment
revision in `checklist.md`. In your own words, answer one question:

> What exact GitHub OIDC subject did the role need to trust, why did the
> previous trust policy fail, and what would you check first if the same error
> returned in another repository?

Optional transfer reflection: identify one product rule that must never break
in another project, then say how you would turn it into a negative eval case.

After the owner supplies the observed feedback and learning response, update
the three final human checkboxes in `checklist.md`; do not mark them earlier.

## 5. Final order — do not submit prematurely

1. Correct/review the final spoken and visible domain in the YouTube video.
2. Complete the production kick-the-tires path and learning response above.
3. Fill every Devpost field from this workbook, then save each step.
4. Open **Preview** while signed out; verify title, pitch, video embed, live
   link, repo link, licence, tags, gallery, and Markdown render correctly.
5. Read the rules and final declarations one more time.
6. Only the project owner presses **Submit project** and completes the exit
   survey.
