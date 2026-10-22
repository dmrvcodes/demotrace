---
doc: checklist
status: approved
---

# Build Checklist

Build mode: fast

## Slices

- [x] **1. You can turn a real demo video into labelled frames and a transcript on your own machine**
  Becomes usable: `python -m demotrace.cli prepare video.mp4 --out out/` writes up to 90 de-duplicated JPEG frames (each labelled `F001…` with its time in the video) and speech segments (`S01…` with start and end) as JSON, and refuses a video longer than 3 minutes.
  Why now: Every later step stands on correct timestamps and on a request that fits the size cap. It costs no cloud money and is the input the model call needs. Project scaffolding is part of this slice.
  PRD ref: `prd.md > The Core Journey` (steps 5–6 depend on correct times), `prd.md > States and Boundaries` (no audio, longer than 3 minutes, static video)
  Spec ref: `spec.md > Worker pipeline`, `spec.md > File Structure`, `spec.md > Shared models`
  Build: Scaffold `backend/shared` and `backend/worker` per the file structure (Python 3.12 virtual environment, `pyproject.toml`, pytest). Add the `ffprobe` check with the 3-minute limit; frames at 1 per second plus scene changes, perceptual-hash de-duplication, at most 90, 1024 px, JPEG, time = `pts_time` minus the stream's `start_time`; faster-whisper segments, with no segments when there is no audio; a helper that trims the request to 16 MB as sent (JPEG quality first, then frames); the `prepare` command.
  Verify (mechanical): pytest passes (timing offset, de-duplication, the 90 cap, size trimming, no audio, longer than 3 minutes). Run `prepare` on a short test clip generated with ffmpeg and macOS `say` (a test pattern with a spoken sentence) and check the frame count, the times and the transcript text.
  Learner check: Run `prepare` on one of your own short demo clips, open `out/frames`, and confirm the time written on a frame matches what you see in the video at that second.
  Commit: `Add local video preparation pipeline (frames and transcript)`

- [ ] **2. A real Bedrock call from your machine returns a valid structured answer**
  Becomes usable: `python -m demotrace.cli smoke` sends a small request and then one realistic request (real frames, speech and claims from slice 1, at most 16 MB) to Claude Opus 5.5 on Amazon Bedrock, prints the status, token usage and the structured answer, and saves both answers as fixtures.
  Why now: Bedrock access, the IAM action, the quota, structured output, effort `high` and the request size are the biggest unknowns, and everything after depends on them. If something fails, we learn it before building more. This is the one allowed technical-layer slice because it leaves runnable evidence of the riskiest assumption.
  PRD ref: `prd.md > Results and evidence`, `prd.md > Product Decisions` (a slide that promises a feature is Told only)
  Spec ref: `spec.md > External Services and Dependencies` (Claude Opus 5.5 on Amazon Bedrock), `spec.md > How We Verify` (Bedrock smoke test), `spec.md > Decisions and Open Issues`
  Build: The model's output schema in the shared models (`claim_id`, `status`, `confidence`, `evidence_ids`, `explanation`); the prompt builder (labelled frames, speech segments, claims; speech and on-screen text framed as data, not instructions); a Bedrock client wrapper (`AnthropicBedrockMantle`, us-east-1, effort `high`, non-streaming, timeout about 420 seconds, refusal and error handling); the `smoke` command; a fixture writer that saves only the model's answer and usage numbers, never the frames or the video. **No AWS call is made until you confirm your console checks are done: what the credits cover and when they expire, Opus 5.5 access, the Bedrock quotas, and the Lambda quotas.**
  Verify (mechanical): Offline tests for the prompt builder and the schema with a stub client. Then the live run: the small call returns a parsed answer; the realistic call returns a parsed answer; record `usage` token counts, the request size in bytes and `stop_reason`; both answers are saved under `eval/fixtures/`.
  Learner check: Confirm your console checks are done before the run. Then read the realistic answer and say whether each claim's status and explanation match what you know your video shows.
  Commit: `Add Bedrock model call with structured output and saved fixtures`

- [ ] **3. You get the finished evidence map for a video and its claims, and can replay it offline**
  Becomes usable: `python -m demotrace.cli analyze video.mp4 --claims claims.json --out out/` prints and saves the result (status, evidence with server-computed timestamps and an explanation per claim). `--replay <fixture>` runs the validation without calling the model. Invalid references are rejected.
  Why now: This is the unique kernel working end to end on your machine — separating what a demo says from what it shows — and it gives the eval something to run.
  PRD ref: `prd.md > Results and evidence`, `prd.md > States and Boundaries` (model refusal or failure, static video, no audio)
  Spec ref: `spec.md > Result validation`, `spec.md > Worker pipeline`, `spec.md > Data Model` (Result JSON)
  Build: Validation (every cited ID exists; status agrees with evidence type; one result per claim; allowed `confidence` values); server-side timestamps from the IDs; the result assembler with `schema_version` and duration; error codes (refusal, invalid output, video too long); the `analyze` command that wires prepare, model call and validation; the `--replay` option.
  Verify (mechanical): Tests: a valid fixture passes; an unknown ID fails; Shown with only speech evidence fails; a missing claim fails; a refusal produces the failure code. Run `analyze --replay` on the saved fixtures and check the output against the result schema. Run `analyze` live once on a test clip with a promise slide and read its statuses.
  Learner check: Run `analyze` on your video with 3–5 claims, one of which is only promised on a slide. Confirm that claim comes out Told only and that the timestamps point where you expect.
  Commit: `Add evidence map analysis with server-side validation and replay`

- [ ] **4. A quality gate you can run: labelled videos scored against the plan's thresholds**
  Becomes usable: `python eval/run.py` scores every labelled case and prints status accuracy, the share of false Shown on negative cases, and the evidence hit rate, with pass or fail against the early gate (3 videos, at least 70%, no false Shown on the promise slide).
  Why now: This is your evening gate. It decides whether the approach is good enough before any cloud or interface work is built on it.
  PRD ref: `prd.md > Product Decisions` (a slide that promises a feature is Told only), `prd.md > What We're Building`
  Spec ref: `spec.md > Eval harness`, `spec.md > How We Verify` (Eval)
  Build: The `eval/cases` format (expected status and evidence time range `[start, end]` per claim); the runner (live or replay); the metrics with the frame sampling step as tolerance; the gate report; hand-labelling 3 videos together with you, one of them the negative promise-slide case; recorded runs saved as fixtures; `eval/runs/` stays gitignored and no video is committed.
  Verify (mechanical): Runner tests on synthetic labels and outputs (metric math, tolerance). Run the gate on the 3 labelled videos and read the report.
  Learner check: Label the 3 videos with me (statuses and time ranges), run the gate, and tell me whether the failures it reports match your own judgement.
  Commit: `Add labelled eval cases and quality gate runner`

- [x] **5. The interface works end to end on the sample**
  Becomes usable: The four steps in the browser in the dark look from the PRD. **Try with sample** opens Results with the video, the timeline and one card per claim; clicking a timestamp or a marker moves the player and highlights the card; the "AI assessment" note is visible.
  Why now: After slices 1–4 you already have a real result from your own pipeline, so the Results screen, the timeline and click-to-seek can be built on it right away. Design is a quarter of the judging, so the look and the core interaction come early, while feedback can still shape the rest, and an early weak demo can be shown. Fixture mode needs no AWS.
  PRD ref: `prd.md > Results and evidence`, `prd.md > Try with sample`, `prd.md > Look and Feel`, `prd.md > Screens and Layout`
  Spec ref: `spec.md > Web app shell`, `spec.md > Results view`, `spec.md > Sample mode and fixtures`, `spec.md > Look and Feel`
  Build: Scaffold the Next.js app in `web/` (TypeScript, Tailwind, Inter and Geist Mono through `next/font`); theme tokens from the spec; `StatusBadge`, `ClaimCard`, `VideoPlayer`, `Timeline`; a schema-checked local sample fixture until Bedrock becomes available (then replace it with a real recorded pipeline result), and a short sample clip with an explicit redistribution licence and attribution, with a `.gitignore` exception for `web/public/samples/` only; the Upload, Claims and Waiting steps as shells.
  Verify (mechanical): `npm run build` and the linter pass; start the dev server, load the page in the browser pane, click **Try with sample**, check that a timestamp click sets the player time and highlights the card, and check the colors and fonts against the tokens.
  Learner check: Open `http://localhost:3000`, click **Try with sample**, click timestamps and markers, and say whether the look matches what you pictured.
  Commit: `Add interface with sample results, timeline and click-to-seek`

- [ ] **6. The same analysis runs inside a real Lambda and writes its result to DynamoDB**
  Becomes usable: A spike script builds the arm64 Worker image, pushes it to ECR, creates the function, a DynamoDB table and an S3 bucket, and a test event with a `job_id` makes the Lambda fetch a video, run the pipeline, call Bedrock from its own role, and store the result.
  Why now: This is the second big risk: the container with ffmpeg and faster-whisper on arm64, the IAM action from the Lambda role, and the real time and memory. It must be proven before the control API and the live interface depend on it. Time-box: finish no later than the evening of Thursday 22 October; the scope is only S3, the pinned object version, the Worker Lambda, Bedrock, the DynamoDB result and the clean-up, with no Terraform, Function URL, budgets, CORS or public site (those are later slices). No AWS call is made before your console checks are confirmed.
  PRD ref: `prd.md > States and Boundaries` (privacy, failures)
  Spec ref: `spec.md > Worker pipeline`, `spec.md > Job state machine and limits`, `spec.md > AWS Lambda`, `spec.md > Amazon S3`, `spec.md > Amazon DynamoDB`, `spec.md > How We Verify` (Lambda run, State races), `spec.md > Fallbacks and Cut Order`
  Build: The Worker Dockerfile (Lambda Python 3.12 base, static arm64 ffmpeg, whisper model in `/opt/models`, offline environment, `HOME` untouched); the handler with the conditional claim, the pinned `VersionId` download, the conditional finish and the `finally` cleanup of every version; `scripts/spike-deploy.sh` with the AWS CLI; written measurements for time, memory, `cpu_threads` and whisper size.
  Verify (mechanical): The read-only file system works; the test event completes; the DynamoDB row is `COMPLETED` with a result; a duplicate delivery exits without changes; no object versions remain in S3; CloudWatch holds no transcript; measurements are written down.
  Learner check: Upload a short video yourself with the AWS CLI, send the test event, and confirm the result row appears and the video is gone from the bucket.
  Commit: `Run the worker on Lambda with DynamoDB state and measurements`

- [ ] **7. A full backend flow works: create a job, upload straight to S3, analyze, poll**
  Becomes usable: With a script, `POST /jobs` returns a token and an upload slot, the file goes to S3, `POST /jobs/{id}/analyze` queues it, and `GET /jobs/{id}` moves from queued to analyzing to done. Limits and token rules apply.
  Why now: This is the backend the interface will talk to. The state rules and the privacy rules must be proven before the live interface depends on them.
  PRD ref: `prd.md > Waiting for the analysis`, `prd.md > States and Boundaries` (daily limits, privacy)
  Spec ref: `spec.md > Control API (FastAPI)`, `spec.md > Job state machine and limits`, `spec.md > Data Model`, `spec.md > How We Verify` (State races, Security and privacy)
  Build: The FastAPI app with the Mangum handler; the presigned upload slot; conditional state transitions; the time rules applied on read; atomic counters (global and per hashed IP); error codes including the capacity one; deployed as a zip Lambda with a Function URL and CORS configured there; tests with moto.
  Verify (mechanical): moto tests pass. Live: a request without a token gets 401 or 404; overwriting the S3 object after `analyze` does not change the result; a failed Worker start gives `FAILED`; the timeout rules fire; the caps trigger; CORS headers appear once.
  Learner check: Run the provided script with your own video and watch the status move to done; confirm that a request without the token is refused.
  Commit: `Add control API with job state machine and limits`

- [ ] **8. Public end to end: your own video, your claims, a real result**
  Becomes usable: On the deployed site, drop a video (the 3-minute and HEVC checks run first), it uploads in the background, you type claims, start, watch the waiting statuses, and get results from the live backend, with failure and capacity messages.
  Why now: This is the first moment a judge could use the real product. Everything before it exists to make this step safe. Once it works on a real clip, preparing the demo recording can start; slices 10–12 do not hold it back.
  PRD ref: `prd.md > Upload`, `prd.md > Claims`, `prd.md > Waiting for the analysis`, `prd.md > States and Boundaries`
  Spec ref: `spec.md > Upload and video preflight`, `spec.md > Claims form`, `spec.md > Waiting view and status poller`, `spec.md > The Core Journey Through the System`
  Build: The real mode of the API client; the preflight; `DropZone` and `ClaimsForm`; the status poller; the failure and capacity banner; the Vercel deploy with `NEXT_PUBLIC_API_BASE_URL`.
  Verify (mechanical): Preflight unit tests; `npm run build` passes; a script that does what the browser does (create job, upload, analyze, poll) against the production URL returns a valid result; the deployed page loads and the sample still works.
  Learner check: On the deployed address, upload a video of yours, enter claims, wait, and click the evidence; then try with someone else's video.
  Commit: `Wire the interface to the live backend`

- [ ] **9. You can come back to a result and re-check a new version**
  Becomes usable: Closing or reloading the tab keeps your claims and your analysis: a running analysis resumes, a finished one shows the saved report with "Drop the video file again to enable the interactive player". **Re-check with new video** returns to the upload step with the claims kept.
  Why now: This closes the loop from the scope — fix the weak part and check again — which the demo video is built on.
  PRD ref: `prd.md > Returning to a result`, `prd.md > Re-checking after a re-record`
  Spec ref: `spec.md > Saved report in the browser`, `spec.md > Data Model` (browser record)
  Build: The localStorage record, resume of polling, the saved-report view, the re-drop prompt that turns the player back on, and the re-check button.
  Verify (mechanical): Unit tests for the store; in the browser pane, finish an analysis, reload and confirm the saved report shows; re-drop the file and confirm click-to-seek works; use re-check and confirm the claims are kept.
  Learner check: Finish an analysis, close the tab, reopen the site, drop your video again, and click an evidence timestamp; then re-check with a new version.
  Commit: `Add saved report, resume and re-check`

- [ ] **10. The risky paths are proven on the live system**
  Becomes usable: The plan's verification list passes against the live system: races, security, caps, the model refusal message, the HEVC warning, S3 clean-up, and logs with no transcripts.
  Why now: Judging runs for days. The weak points must be closed before anyone else uses the system.
  PRD ref: `prd.md > States and Boundaries`
  Spec ref: `spec.md > How We Verify`, `spec.md > Important Failure Modes`, `spec.md > Job state machine and limits`
  Build: Fix whatever the checks expose; set the emergency off switch (cap 0) and the Budget alerts at $10, $25 and $50; make sure the failure messages match the PRD.
  Verify (mechanical): Run each check from `spec.md > How We Verify` (State races, Security and privacy) and record the result; confirm a cap of 0 turns analysis away with the capacity message and the sample still works.
  Learner check: Try to break it: a video over 3 minutes, an HEVC file, a refused request, a reload mid-analysis; tell me which message was unclear.
  Commit: `Harden limits, timeouts and clean-up on the live system`

- [ ] **11. A six-video quality pass you can quote honestly in the README**
  Becomes usable: Six labelled videos (negatives included) run through the same gate, with the numbers and the prompt tuned until the goal of at least 80% holds.
  Why now: The quality of "shown versus told" is the product. Your plan reserves Friday and Saturday for it, after the system is stable.
  PRD ref: `prd.md > Product Decisions`
  Spec ref: `spec.md > Eval harness`, `spec.md > How We Verify` (Eval)
  Build: Three more labelled cases (a similar interface with no result, weak evidence, a silent video with the claim on a slide); prompt tuning against the whole set; a short results note with "smoke eval on N claims".
  Verify (mechanical): Run `python eval/run.py` on all six cases and read status accuracy, false Shown on the negatives, and evidence hits against the thresholds.
  Learner check: Look at every miss with me and say whether the model or the label was wrong.
  Commit: `Extend eval to six videos and tune the analysis`

- [ ] **12. The infrastructure is rebuilt from Terraform**
  Becomes usable: `terraform plan` shows no unexpected changes and `terraform apply` recreates the S3 bucket, DynamoDB table, ECR repository, both Lambdas with roles and log groups, the Function URL, the asynchronous-invoke settings and the Budget, with the Worker image pinned by digest.
  Why now: Your plan puts it after a working end to end, so it can never delay the proof. It also makes the cleanup after judging a single command.
  PRD ref: `prd.md > States and Boundaries` (privacy, daily limits)
  Spec ref: `spec.md > Infrastructure (infra/)`, `spec.md > Amazon ECR, CloudWatch Logs, AWS Budgets`, `spec.md > After Submission`
  Build: Terraform in `infra/` with local state kept outside the repository and `-var image_digest=...`; replace or import the spike resources without breaking the live site.
  Verify (mechanical): `terraform validate` and `terraform plan` run clean; after apply, the end-to-end script from slice 8 still returns a valid result; no state file is tracked by git.
  Learner check: Run the plan yourself and tell me whether the resources it lists are the ones you expect.
  Commit: `Add Terraform for the backend infrastructure`

## Hands-on Checkpoints

- [ ] Early usable behavior explored — after slice 5 (the interface with the sample: look and click-to-seek)
- [ ] Public end-to-end explored — after slice 8 (your own video and someone else's through the live site)
- [ ] Final kick-the-tires exploration and feedback completed

## Final Review

- [ ] Final review complete — feedback resolved and learner confirms ready to ship

## Code Tour and App Map

- [ ] Learning activity complete — guided route, focused alternative, prior practice connected, or brief recap
- [ ] Optional edit and transfer reflection addressed — offered/declined/already covered/not applicable as appropriate
- [ ] `devpost/app-map.html` generated from finished code, checked, and shown, including a project-grounded practice to reuse

Activity and evidence: [what actually happened; real document/test/code references; unfinished work if interrupted]
Route and stops: [actual paths and symbols; guided stops completed, or reference-only route]
Edit outcome: [tried/kept/reverted/declined/not applicable; verification if changed]
Reflection: [offered/answered/declined/already covered — personal answer belongs only in the ignored profile]
Activity mode: [live app and editor, explicit static fallback, focused alternative, prior practice, or recap]

## Revisions

- De-duplication now needs both the perceptual hash and a changed-pixel check on a colour thumbnail to call two frames duplicates (`spec.md > Worker pipeline`, `backend/worker/demotrace/media/dedupe.py`) — the build found that the perceptual hash gives a red and a blue screen the same hash, so a colour-only change such as a status turning green would have been thrown away as a duplicate.
- Bedrock inference is account-blocked (`Operation not allowed` for Amazon Nova and 403 for Claude), so the temporary execution order is slice 5 before slices 2–4. This preserves the product boundary and gives a local, reviewable interface while AWS Support resolves access. The sample starts as a schema-checked local fixture and must be replaced with a recorded model result before the eval/public-submission gate.
