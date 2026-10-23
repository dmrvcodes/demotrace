---
doc: spec
status: approved
---

# DemoTrace — Technical Spec

## As Built — 23 October

The executable architecture supersedes stale planning references below: the Control service is a
dependency-free Python 3.12 Lambda Function URL handler, not FastAPI/Mangum; inference uses the
direct Anthropic API via a secret in AWS Secrets Manager, not Bedrock; Terraform has an encrypted
S3 remote backend; and GitHub Actions deploys a digest-pinned arm64 Worker via a restricted OIDC
role. `eval/run.py` is the actual quality gate and requires four genuine recorded cases before it
can pass. The planning sections remain as historical decisions until the final documentation pass.

## How This Works, In Plain Language

DemoTrace has two halves: a website the author sees, and a small cloud backend that does the heavy work.

- **The website** (Next.js, hosted on Vercel) shows the four steps from the PRD: Upload, Claims, Waiting, Results. It plays the author's video from the author's own computer, so the video never has to come back from the cloud.
- **The front door** (a small Python service on AWS Lambda, "Control") does three things: it hands the browser a one-time upload slot, it starts an analysis when the author has typed their claims, and it reports progress and the final result. Every analysis gets a secret ticket (the job token) that only the author's browser holds, so nobody else can open the result.
- **The video storage** (S3) receives the video straight from the browser through that one-time slot and keeps it only until the analysis is done.
- **The notebook** (DynamoDB) holds one row per analysis: its claims, its status (created → waiting → analyzing → done or failed) and, at the end, the result. Moving between statuses is guarded so that two workers can never take the same job, and a finished job can never be overwritten by a late timeout.
- **The analyst** (a second Lambda, "Worker", packaged as a container) does the real work in order: it checks the video length, cuts out frames (about one per second, plus scene changes, at most 90), writes down what is said (speech to text), and then asks Claude through the Anthropic API (the model is chosen in one place; today Claude Sonnet 4.6) one structured question: for each claim, is it Shown, Told only or Missing, which frames or speech segments prove it, and why. Then the Worker **checks that every piece of evidence Claude cites really exists** and computes all timestamps itself. It saves the result and deletes the video.
- **The browser's memory** (localStorage) keeps the claims, the ticket and the finished report on that device, so closing the tab does not lose anything. The video is not kept anywhere, so after a reload the author drops the file again to turn the player back on.

Why this shape rather than something simpler: judges need to analyze a real video at any time during judging, so there has to be a real backend. Why not something more elaborate: no accounts, no queue service, no live sockets — the browser just asks for the status every few seconds, and the Worker's concurrency limit acts as a queue.

## The Core Journey Through the System

PRD ref: `prd.md > The Core Journey`.

1. **Open the site** → Vercel serves the Next.js page; the browser looks in localStorage for an earlier analysis (`prd.md > Returning to a result`) and offers it if there is one.
2. **Drop a video** → the browser checks length and playability locally (`prd.md > Upload`). If accepted, it calls `POST /jobs` on Control. Control checks the daily limits, creates the job (status `CREATED`), and returns a job id, a job token, and a one-time upload slot. The browser sends the file straight to S3 in the background. **Try with sample** skips all of this and goes to step 7 with prepared data (`prd.md > Try with sample`).
3. **Type 3–5 claims** → the browser keeps them in the form (and in localStorage).
4. **Start the analysis** → `POST /jobs/{id}/analyze` with the claims and the token. Control confirms the upload landed, pins the exact version of the uploaded object, checks the analysis limit, moves the job `CREATED → QUEUED`, and starts the Worker asynchronously.
5. **Waiting** → the browser polls `GET /jobs/{id}` every few seconds. `QUEUED` shows "waiting to be processed", `PROCESSING` shows "analyzing" (`prd.md > Waiting for the analysis`). Meanwhile the Worker takes the job (`QUEUED → PROCESSING`), downloads that exact video version, runs the pipeline, asks Claude, validates the answer, writes the result (`PROCESSING → COMPLETED`), and deletes every stored version of the video.
6. **Results** → the poll returns the result. The browser renders the video (from the local file), the timeline and one card per claim, and saves the report in localStorage (`prd.md > Results and evidence`).
7. **Click evidence** → the player seeks to that second and the related card is highlighted; no network involved.
8. **Re-check with new video** → back to the upload step with the claims kept; a fresh job is created when the new file is accepted (`prd.md > Re-checking after a re-record`).

## Stack

| Layer | Choice | Why / tradeoff | Docs |
|---|---|---|---|
| Frontend | Next.js (App Router) + TypeScript + Tailwind CSS; fonts Inter and Geist Mono through `next/font`; no UI component library | **Learner's choice.** Tailwind makes the PRD's color and type tokens quick to apply. Tradeoff: verbose markup, acceptable for one small app. | [Next.js](https://nextjs.org/docs), [Tailwind](https://tailwindcss.com/docs), [next/font](https://nextjs.org/docs/app/api-reference/components/font) |
| Control API | Python 3.12, **FastAPI** + Mangum (ASGI-to-Lambda adapter), Pydantic v2, boto3; Lambda zip, arm64, Function URL | **Learner's choice** (Python 3.12 for both Lambdas, FastAPI named for the API). One language across the backend, shared Pydantic models, and the same app runs locally under `uvicorn`. Tradeoff: slightly slower cold start and a few more dependencies than a hand-written handler. | [FastAPI](https://fastapi.tiangolo.com), [Mangum](https://mangum.fastapiexpert.com), [Pydantic](https://docs.pydantic.dev), [Lambda Function URLs](https://docs.aws.amazon.com/lambda/latest/dg/urls-configuration.html) |
| Worker | Python 3.12, plain Lambda handler (it is invoked with an event, not HTTP), container image on arm64 | **Learner's choice** (container with ffmpeg and faster-whisper; arm64). | [Lambda container images](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html) |
| Video | ffmpeg / ffprobe (static arm64 build baked into the image), Pillow, `imagehash` and NumPy for de-duplication (perceptual hash plus a changed-pixel check) | Frames and duration come from the tools that define timestamps. | [ffmpeg](https://ffmpeg.org/documentation.html), [imagehash](https://github.com/JohannesBuchner/imagehash) |
| Speech to text | faster-whisper, model baked into the image at `/opt/models` | **Learner's choice.** Size and `cpu_threads` are chosen by measurement in Lambda, not in advance. | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) |
| Model | Claude through the Anthropic API (`anthropic` Python SDK). The model ID is set only by the Terraform variable `anthropic_model` (today `claude-sonnet-4-6`, the model the learner validated) and reaches the Worker as `ANTHROPIC_MODEL` | **Learner's choice, changed on 22 October:** Bedrock inference was blocked for this account, so the learner switched to the direct API. The key lives only in AWS Secrets Manager. | [Messages API](https://platform.claude.com/docs/en/api/messages/create) |
| Storage and state | S3 (versioning on), DynamoDB (on-demand, TTL), CloudWatch Logs | Part of the learner's approved design. | see External Services |
| Infrastructure | A deploy script with the AWS CLI first, then Terraform (local state kept outside the repository, image pinned by digest) | **Learner's choice and order:** the first working deploy is never delayed by automation. | [Terraform AWS provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs) |
| Hosting of the site | Vercel | $0; connects to the GitHub repository. | [Vercel](https://vercel.com/docs) |

**What was verified in this session and what was not.** Fetched and read today: the Anthropic documentation for Claude in Amazon Bedrock (client class, model ID, IAM action, regions, quotas, feature support), the Anthropic Python SDK reference for structured output, the Mangum site, and the faster-whisper README. Every other link above is from memory and has not been opened; the versions of Next.js, Tailwind and the Python packages are not pinned yet and must be checked when the project is scaffolded (`npm view next version`, `pip index versions ...`).

## Where It Runs and How Someone Tries It

**Runtime.** The site runs in the browser, served by Vercel. The backend runs in AWS **us-east-1**. Development happens on the learner's Mac (Apple silicon).

**Local, no AWS needed (fixture mode).**
```
cd web
npm install
echo "NEXT_PUBLIC_API_MODE=fixture" > .env.local
npm run dev        # open http://localhost:3000 and click "Try with sample"
```
Fixture mode replays a recorded model response (`web/public/samples/sample.json`) and plays `web/public/samples/sample.mp4`. This is the mode for building the interface and for the sample button in production.

**Local pipeline, real model.**
```
cd backend/worker
python -m demotrace.cli analyze path/to/video.mp4 --claims claims.json --out out/        # real Bedrock call
python -m demotrace.cli analyze path/to/video.mp4 --claims claims.json --replay eval/fixtures/<case>.json   # no model call
```
It needs `ffmpeg` and `ffprobe` on the path and AWS credentials in the learner's own AWS profile or environment — never in the repository.

**Production.** The site is deployed from the GitHub repository to Vercel. Its environment variable `NEXT_PUBLIC_API_BASE_URL` points at the Control Lambda's Function URL. The backend is deployed by `scripts/spike-deploy.sh` and later by Terraform in `infra/`.

**Required environment (names only, values never committed):** `AWS_REGION=us-east-1`, `BUCKET_NAME`, `TABLE_NAME`, `WORKER_FUNCTION_NAME`, `ANTHROPIC_MODEL` (set by Terraform for the Worker; locally in `.env`), `ANTHROPIC_API_KEY` (local `.env` only; in AWS it is in Secrets Manager), `DAILY_JOB_CAP`, `DAILY_ANALYSIS_CAP`, `IP_JOB_CAP`, `IP_ANALYSIS_CAP`, `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_API_MODE`. A secret-free `.env.example` lists them.

**The required demo recording** is made against the deployed site with the real analysis (weak first version → Told only → re-record → Shown). The sample button is the fallback for anyone trying it without a video.

**Submission and optional deployment.** A short demo video and a public GitHub repository are required. The learner chose a live deployment so judges can test it during judging; it supplements the video and repository, it does not replace them. All cloud cost is covered by AWS credits (see Decisions and Open Issues for the budget gate).

**Before any AWS call** the learner confirms in the AWS console: what the credits cover and when they expire; the Anthropic API key and its spending limit; Lambda quotas (concurrency and memory). Credentials are never stored in the repository or in these documents; they come from the learner's own AWS profile or environment.

## Look and Feel

Carried forward from `prd.md > Look and Feel`; the interview is not repeated.

- **Character:** strict, utilitarian engineering tool — Linear, GitHub Actions, Raycast. Dense but calm. Short, factual interface copy; no marketing tone.
- **Tailwind theme tokens:**
  - `--bg` `#09090b`, `--surface` `#18181b` (the learner's dark zinc base)
  - Derived to complete the neutral scale: border `#27272a`, primary text `#f4f4f5`, secondary text `#a1a1aa` (standard zinc steps)
  - `--shown` `#10b981`, `--told-only` `#f59e0b`, `--missing` `#71717a`
- **Color is semantic only.** The three evidence colors appear on status badges, timeline markers and card accents, and nowhere else.
- **Contrast note (derived):** `#71717a` on `#09090b` is about 4.1:1, below the 4.5:1 normally wanted for small text. So the Missing color is used for the badge border, dot and marker, while the badge label text is `#d4d4d8`.
- **Typography:** Inter for the interface; Geist Mono (JetBrains Mono as the alternative) for timestamps and status labels, e.g. `[0:42]`, `SHOWN`.
- **Avoid:** purple gradients, neon glow, sparkle or star icons.
- **Stack fit:** Tailwind with CSS variables honors all of this. Nothing in the direction is out of its reach.

## Components

### Web app shell
One route (`/`) holding a four-step flow (Upload → Claims → Waiting → Results) as a client-side state machine; no router needed between steps.
Talks to: the API client and the browser store.
PRD ref: `prd.md > Screens and Layout`.

### Upload and video preflight
`DropZone` accepts one file. `preflight.ts` loads it into an off-screen `<video>` to read its duration and to see whether the browser can decode it: more than 3 minutes → blocked with a clear error; decoding fails (HEVC or MOV) → warning that suggests H.264 MP4. The drop-zone text states the limits (3 minutes, English narration only) and the deletion line. Once accepted, the file is kept in memory (for the player) and uploaded in the background.
Talks to: API client (`POST /jobs`, then S3 with the upload slot).
PRD ref: `prd.md > Upload`, `prd.md > States and Boundaries`.

### Claims form
3–5 claim fields with the hint about observable results. **Start analysis** is enabled only when the upload has finished and 3–5 claims are filled.
PRD ref: `prd.md > Claims`.

### Waiting view and status poller
Polls `GET /jobs/{id}` every 3 seconds with the job token. Maps `QUEUED` → "waiting to be processed", `PROCESSING` → "analyzing", `FAILED` → a message chosen from the error code (including the "demo is at capacity" banner that switches to the sample), `COMPLETED` → Results. Polling resumes after a page reload from the saved job id.
PRD ref: `prd.md > Waiting for the analysis`, `prd.md > States and Boundaries`.

### Results view
`VideoPlayer` (HTML5 `<video>` on a blob URL for the author's file, or `/samples/sample.mp4`), `Timeline` (a custom bar under the player with colored markers at evidence times), `ClaimCard` list (claim text, status badge, timestamps, one-to-two sentence explanation), the "AI assessment — click the evidence to verify" note, and the **Re-check with new video** button. A timestamp or marker click sets `currentTime` and highlights the related card, both directions. No confidence value is rendered anywhere.
PRD ref: `prd.md > Results and evidence`, `prd.md > Re-checking after a re-record`.

### Saved report in the browser
`store.ts` writes one record to localStorage (`demotrace:v1:last`): job id, job token, claims, status, result (when done), saved time. A new analysis replaces it. On load, a record with a result shows the saved report and the message "Drop the video file again to enable the interactive player"; a record without one resumes polling. The video itself is never stored. The sample is never stored.
PRD ref: `prd.md > Returning to a result`.

### Sample mode and fixtures
The local fixture mode loads `src/lib/sample.ts` and `/public/samples/demotrace-sample.mp4`, so the same Results view renders without an API call. Until Bedrock inference is enabled for this account, the sample result is a schema-checked local fixture with deliberately traceable frame evidence; it is labelled as a sample analysis. It is replaced with a recorded model response for the same sample video before the quality gate and public submission.
PRD ref: `prd.md > Try with sample`.

### Control API (FastAPI)
Three endpoints, JSON, Bearer job token on the last two:

| Endpoint | What it does |
|---|---|
| `POST /jobs` | Checks the daily and per-IP job limits; creates the job (`CREATED`); returns `job_id`, `job_token` and a presigned upload slot. |
| `POST /jobs/{id}/analyze` | Body: the claims (3–5). Confirms the upload exists, reads its exact `VersionId` and size, checks the analysis limits, moves `CREATED → QUEUED`, starts the Worker asynchronously. |
| `GET /jobs/{id}` | Returns the status and, when done, the result. It also applies the time rules below. |

The client IP for the per-IP limits comes from the Function URL event. CORS is configured on the Function URL only; the FastAPI CORS middleware is switched on only for local development, so browsers never get duplicate headers.
PRD ref: `prd.md > Waiting for the analysis`, `prd.md > States and Boundaries` (daily limits, privacy).

### Job state machine and limits
States: `CREATED → QUEUED → PROCESSING → COMPLETED | FAILED`. Every move is a conditional write ("only if the status is still X"), so a duplicate or late actor simply loses.
- `QUEUED` for more than 30 minutes becomes `FAILED` (checked when the status is read).
- `PROCESSING` for more than 16 minutes becomes `FAILED`.
- The Worker finishes a job only if `status = PROCESSING` and `run_id` is its own, so it never overwrites a `FAILED` set by a timeout.
- If starting the Worker is confirmed to have failed, the job goes `QUEUED → FAILED`; if the start times out without an answer, the job stays `QUEUED` and the 30-minute rule settles it.
- Limits are atomic counters in DynamoDB with a TTL: `DAILY_JOB_CAP=40`, `DAILY_ANALYSIS_CAP=20`, and per IP 3 analyses and 6 jobs per day. Setting a cap to 0 is the emergency off switch. The IP is stored only as a hash.
PRD ref: `prd.md > States and Boundaries`.

### Worker pipeline
A Python package `demotrace` used by the Lambda handler, the local CLI and the eval harness alike, so there is one code path.

1. **Claim the job** — conditional `QUEUED → PROCESSING` with a new `run_id`. If it fails, this is a duplicate delivery: exit quietly.
2. **Fetch** — download the pinned `VersionId` of `incoming/{job_id}` into a temporary directory.
3. **Probe** — `ffprobe` re-checks the duration (more than 3 minutes → `FAILED`, error `video_too_long`) and finds the video and audio streams. *Learner-approved: the browser check can be bypassed, so the Worker is the real guard.*
4. **Frames** — 1 frame per second plus scene-change frames, de-duplicated by perceptual hash together with a changed-pixel check on a small colour thumbnail (a frame is a duplicate only when both agree), at most 90, longest side 1024 px, JPEG. A frame's time is its `pts_time` minus the stream's `start_time`.
5. **Speech** — faster-whisper segments with start and end. No audio stream → no segments (a claim shown only on a slide can still be Told only).
6. **Ask the model** — see External Services. Input: frames labelled `Frame F012 · 00:41.0`, speech segments `S05 [00:40.2–00:44.8] "..."`, claims `C1..C5`. The request body is kept at 16 MB or less *as sent* (base64 included); if it is larger, JPEG quality is reduced first, then frames are dropped. On-screen text and speech are data, not instructions, and the model gets no tools. The instructions tell the model to say so when nothing changes on screen (a static video), so such claims come out as Told only or Missing (`prd.md > States and Boundaries`).
7. **Validate** — see below.
8. **Finish** — conditional `PROCESSING → COMPLETED` (or `FAILED` with an error code and a plain message), then, in a `finally` block, delete every version of `incoming/{job_id}` and the temporary directory. Every failure is attributed to its stage (`download`, `prepare`, `transcribe`, `secret`, `model`, `validate`, `save`) and stored on the job as `failed_stage` with its code (`storage_error` and `internal_error` cover failures that carry no code of their own); per-stage durations are stored as `timings`. One JSON log line per job carries only ids, stage, error type, code, durations and token counts — no transcripts, prompts, keys or URLs.

PRD ref: `prd.md > The Core Journey`, `prd.md > Results and evidence`.

### Result validation
The server checks references and format only; it does not prove the model is right, which is why the interface says "AI assessment".
- Every cited ID (`F…` frame or `S…` segment) exists in this job's input.
- Status and evidence agree: **Shown** cites at least one frame; **Told only** cites at least one frame (a slide) or speech segment; **Missing** cites nothing. *(Derived from the PRD's definitions.)*
- Exactly one result per submitted claim; the explanation is non-empty; `confidence` is one of the three allowed values.
- Timestamps in the result are computed by the server from the IDs; the model's own numbers are never trusted.
- A refusal (`stop_reason == "refusal"`) or an invalid answer → job `FAILED` with a clear message.
PRD ref: `prd.md > Results and evidence`, `prd.md > States and Boundaries`.

### Shared models
`backend/shared/demotrace_shared` holds the Pydantic models used by both Lambdas and the CLI: the claim input, job status, error codes, the model's output schema, and the result returned to the browser. The browser's TypeScript types mirror them by hand, and one fixture file is validated by the Python tests and loaded by the interface, so the two cannot drift silently.

### Infrastructure (`infra/`)
Terraform for the S3 bucket, DynamoDB table, ECR repository, two Lambdas with roles and log groups, the Function URL, the asynchronous-invoke settings and an AWS Budget. Written only after the end-to-end flow works on resources created by the spike script.
PRD ref: `prd.md > States and Boundaries` (privacy, daily limits).

### Eval harness
`eval/` holds hand-labelled cases (status and an evidence time range per claim), recorded model responses as fixtures, and a runner that reports status accuracy, the share of false `Shown` on negative cases, and whether the cited frame falls inside the labelled range (tolerance: the frame sampling step). Test videos and run outputs stay out of git.
PRD ref: `prd.md > Product Decisions` (a slide that promises a feature is Told only).

## Data Model

**Job item** (DynamoDB, key `JOB#{job_id}`): `job_id` (random UUID4), `token_hash` (SHA-256 of the 32-byte job token — the token itself is never stored), `status`, `claims` (list of text), `version_id`, `size_bytes`, `created_at`, `queued_at`, `started_at`, `run_id`, `finished_at`, `error_code`, `result` (JSON), `model_confidence` (claim id → low/medium/high, for the eval only), `ttl`.
- Lives: until its TTL, set to **7 days** after creation (*derived default — see Open Issues*).
- Updated by: Control (create, queue, expire on read) and Worker (claim, finish) through conditional writes.
- Leaving and coming back: the browser asks `GET /jobs/{id}` with its saved token and gets the same status or result.

**Counter items** (key `CAP#{date}#global` and `CAP#{date}#ip#{ip_hash}`): job and analysis counts incremented with a conditional add; TTL of 2 days.

**Result JSON** (returned to the browser, stored in the job item):
```
{ schema_version, duration_s,
  claims: [ { claim_id: "C1", text, status: "shown"|"told_only"|"missing",
              explanation, evidence: [ { ref_id: "F012"|"S05", kind: "frame"|"speech", t: 41.0 } ] } ] }
```
The result sent to the browser has no confidence field. For speech evidence `t` is the segment start.

**Video object** (S3, `incoming/{job_id}`): written by the browser, read by the Worker at its pinned version, deleted (all versions) at the end of processing; lifecycle rules remove anything left after 1 day.

**Browser record** (localStorage `demotrace:v1:last`): described under Saved report in the browser.

## File Structure

```
demotrace/
├── devpost/                     # Devpost learning workspace (scope, PRD, spec, checklist)
├── web/                         # Next.js app, deployed to Vercel
│   ├── app/                     # layout.tsx (fonts, theme), page.tsx (the four-step flow)
│   ├── components/              # DropZone, ClaimsForm, WaitingView, ResultsView, VideoPlayer,
│   │                            # Timeline, ClaimCard, StatusBadge, AssessmentNote
│   ├── lib/                     # api.ts (real + fixture), store.ts (localStorage), preflight.ts,
│   │                            # types.ts, format.ts (mm:ss)
│   └── public/samples/          # sample.mp4 and sample.json (recorded result)
├── backend/
│   ├── shared/demotrace_shared/ # Pydantic models shared by both Lambdas and the CLI
│   ├── control/                 # FastAPI app + Mangum handler (zip Lambda)
│   │   ├── app/                 # main.py, routes, store.py (DynamoDB), limits.py, uploads.py (S3)
│   │   └── tests/
│   └── worker/                  # container Lambda
│       ├── Dockerfile
│       ├── demotrace/           # media/ (probe, frames, dedupe), stt/, llm/ (client, prompt),
│       │                        # validate/, jobs/ (claim, finish), cli.py, handler.py
│       └── tests/
├── infra/                       # Terraform (written after the first end-to-end run)
├── eval/
│   ├── cases/                   # hand labels per video (YAML)
│   ├── fixtures/                # recorded model responses (JSON)
│   └── runs/                    # run outputs (gitignored)
├── scripts/                     # spike-deploy.sh, build and push helpers
├── .env.example                 # variable names only
├── .gitignore
├── LICENSE                      # MIT
└── README.md
```

## External Services and Dependencies

### Claude on the Anthropic API
Docs: [Messages API](https://platform.claude.com/docs/en/api/messages/create), [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) (not fetched).
- **Client:** `anthropic.Anthropic(api_key=..., timeout=420, max_retries=0)`. The Worker reads the key from the Secrets Manager secret `demotrace/anthropic-api-key` (its role may read only that secret); locally it comes from the gitignored `.env`. The key is never logged.
- **Model ID:** read from `ANTHROPIC_MODEL` at call time, with no default in code, so a stale model can never be used silently. Terraform's `anthropic_model` is the single source of truth (today `claude-sonnet-4-6`).
- **Request:** one user message containing, in order, labelled frame images (base64 JPEG), the speech segments, then the claims; `max_tokens` 16000; `output_config={"effort": "high"}`, which Sonnet 4.6 supports; no `temperature`/`top_p`, no assistant prefill, no forced `tool_choice`, no tools.
- **Structured output:** `client.messages.parse(..., output_format=Model)` and read `response.parsed_output`.
- **Output model (what Claude returns), as in the approved plan:** per claim: `claim_id`, `status`, `confidence`, `evidence_ids` (a list of `F…`/`S…`), `explanation`. `confidence` is `low`/`medium`/`high`, stored with the job for the eval and never sent to the browser (`prd.md > Results and evidence`).
- **Refusal:** if `stop_reason == "refusal"`, the job fails with a clear message; no automatic model fallback.
- **Call settings:** non-streaming (the answer is a small JSON), timeout about 420 seconds, no automatic retry; one manual retry only on a 429 or 5xx if enough Lambda time remains.
- **Costs:** paid through the learner's Anthropic account, not AWS credits. Sonnet 4.6 list price is $3 / $15 per million input / output tokens; at roughly 75,000 input and a few thousand output tokens an analysis costs on the order of $0.3. Measured numbers come from the token counts the Worker logs.
- **The original plan (kept for reference):** Claude Opus 5.5 on Amazon Bedrock through `AnthropicBedrockMantle`. On 22 October inference was blocked for this account (403 for Claude), so it is not used.

### Amazon S3
Docs: [Presigned POST](https://docs.aws.amazon.com/boto3/latest/reference/services/s3/client/generate_presigned_post.html), [Versioning](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html), [Lifecycle](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html) (not fetched).
Bucket: versioning on, Block Public Access, server-side encryption, CORS for the production domain, `http://localhost:3000` and `*.vercel.app`. Upload slot: key `incoming/{job_id}`, size 1 byte to 150 MB, `Content-Type` starting with `video/`, valid 10 minutes. Lifecycle: current versions after 1 day, non-current versions after 1 day, expired delete markers, abort incomplete multipart uploads after 1 day.

### Amazon DynamoDB
Docs: [Conditional writes](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/WorkingWithItems.html#WorkingWithItems.ConditionalUpdate), [TTL](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html) (not fetched). One on-demand table, partition key `pk`; conditional `UpdateItem` for every state change and counter.

### AWS Lambda
Docs: [Function URLs](https://docs.aws.amazon.com/lambda/latest/dg/urls-configuration.html), [asynchronous invocation](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async.html) (not fetched).
- **Control:** zip, arm64, Function URL with CORS configured there.
- **Worker:** container image, arm64, reserved concurrency 1, 900-second timeout, asynchronous invoke with 0 retries and a maximum event age of 1800 seconds. Memory and ephemeral storage are chosen by measurement.
- **Roles:** Control — logs; DynamoDB `GetItem`/`PutItem`/`UpdateItem`; S3 `PutObject`, `GetObject`, `GetObjectVersion` on `incoming/*`; `lambda:InvokeFunction` on the Worker. Worker — logs; S3 `GetObjectVersion`, `DeleteObjectVersion` on `incoming/*`; S3 `ListBucketVersions` limited to the `incoming/` prefix; DynamoDB `GetItem`/`UpdateItem`; `bedrock-mantle:CreateInference`.
- **Mangum:** its site says it handles Function URL events, but does not mention payload format 2.0; confirmed by the first deploy.

### Amazon ECR, CloudWatch Logs, AWS Budgets
ECR holds the Worker image. Log groups have a retention period. Budgets at $10 / $25 / $50 only notify; the hard stop is the in-app caps.

### Python and JavaScript dependencies
Worker: `anthropic[bedrock]`, `faster-whisper` (its README does not state ARM support, so the arm64 image build is the check), `Pillow`, `imagehash`, `pydantic`, `boto3`. Control: `fastapi`, `mangum`, `pydantic`, `boto3`. Web: `next`, `react`, `tailwindcss`. Dev: `pytest`, `moto` for AWS-free tests of Control.

## Important Failure Modes

- **The model call fails, times out, refuses, or returns something invalid** → the job becomes `FAILED` with a plain message ("The analysis could not be completed — please try again"), the video is removed, the author can start again.
- **The Worker dies or never starts** → the time rules settle it on the next status read (`QUEUED` over 30 minutes, `PROCESSING` over 16 minutes become `FAILED`); the browser shows the failure instead of waiting forever.
- **The same job is delivered twice** → the second Worker fails the conditional claim and exits without touching anything.
- **A daily cap is reached** → Control answers with a dedicated error code, and the browser shows the capacity banner that switches the author to the sample.
- **The uploaded file is missing when analysis starts** → Control refuses with a clear message and the browser returns to the upload step.

## How We Verify

All of this comes from the approved plan; the points below are checked, not assumed.

**Bedrock smoke test (first, before any interface work).** One test checks five things at once: the model answers, `messages.parse` with structured output works, effort `high` is accepted, the request-size limit, and the token quota. A small request goes first, then one realistic request (about 90 frames at 1024 px, at most 16 MB). Three separate paid tests by size are not needed. It runs locally first (Tuesday) and then **from the Worker's Lambda role** (Wednesday), because the IAM action is only confirmed by a real call.

**Lambda run.** A 3-minute, 150 MB video is processed in a safe time. Time, memory, `cpu_threads` and the whisper model size are measured in Lambda and written down; the container's read-only file system is checked explicitly (the model lives in `/opt/models`, `HF_HUB_OFFLINE=1`, `HOME` is not overridden, library cache variables point at `/tmp` only if needed).

**State races.**
- A repeated delivery of the same event → the second Worker fails its conditional claim and exits.
- A timeout applied on read → the job is `FAILED`, and the Worker does not overwrite it.
- A failed Worker start → the job becomes `FAILED`.

**Security and privacy.**
- A request without a job token gets 401 or 404.
- Overwriting the S3 object after `analyze` does not affect the result: the Worker reads its pinned `VersionId`.
- After processing, no version of the video is left in S3.
- The job and analysis limits trigger.
- CloudWatch contains no transcripts and no presigned URLs.

**Eval (a smoke eval, not statistical proof).** 6 videos with 15–30 claims, including negative cases: a slide that promises a feature, a similar interface with no result, weak evidence, and a silent video with the claim on a slide (expected Told only). Labels are made by hand: status plus the evidence time range `[start, end]`. Metrics: status accuracy; the share of false `Shown` on negative cases, reported separately; and whether the cited frame falls inside the labelled range, with the frame sampling step as tolerance. Thresholds: Tuesday evening, 3 videos including a negative one, at least 70% and no false `Shown` on the promise slide (an early filter only); Friday–Saturday, all 6 videos, goal at least 80%. Any change of model or speech-to-text goes through the same eval. The README says honestly "smoke eval on N claims".

**Submission checks (for `6-ship`).** The analysis of the learner's own videos works in production; the demo video, README, license and Skill Pack documents are in place; no `learner-profile.md`, `.env`, Terraform state, test videos or secrets exist in files or history.

## Fallbacks and Cut Order

From the approved plan. **AWS resources stay inside AWS credits. Since 22 October the model is paid through the learner's Anthropic API account (their decision, after Bedrock was blocked for this account).**

- **No access to the model, or the quota is too small** → ask for a quota increase on day one; in parallel use another Bedrock model covered by the credits, and only if it passes the same eval. For development, replay the recorded fixtures.
- **A native library or speech-to-text fails in Lambda** → a smaller whisper model, then Amazon Transcribe; both go through the eval.
- **The Worker runs longer than about 10 minutes** → fewer frames; then the same image as a one-off ECS Fargate task (scale to zero, credits).
- **Lambda is not ready by Saturday** → a *working* mode on Fargate or a temporary instance within the credits. A static page does not count.
- **What is cut first:** Markdown export, then the per-IP limit (the global limits stay), then thumbnails (the timestamps stay).
- **Never cut:** analysis of the learner's own videos, click-to-seek, deletion of the media, the job token, the LICENSE, the Skill Pack documents.

## After Submission

There is no daily ping. Instead: a control run on the evening of Monday 26 October before judging starts, and a state check on Wednesday 28 October. After the winners are announced: `terraform destroy` and removal of any remaining versions in S3.

## What Was Simplified and Why

- **No accounts or login** — the job token and the browser's memory give private results without sign-in. The fuller version (history, sharing) is deferred in the PRD.
- **Polling instead of live updates** — the browser asks every 3 seconds. Real-time sockets would add a service and a failure mode for no visible gain.
- **No queue service** — the Worker's concurrency limit of 1 and the 30-minute queue rule act as the queue. A real queue is added only if there is time and evidence it is needed.
- **The sample is a recorded result** — labelled as such in the interface, so it is never mistaken for a live analysis. The live analysis of the author's own video is the real kernel and is not faked.
- **Frame thumbnails and Markdown export are not built** — text timestamps are enough (`prd.md > Deferred From the POC`).
- **Terraform comes after the first working end-to-end run** — the first deploy is a script, so the infrastructure tool never delays proving the pipeline.
- **No automatic retry and no automatic model fallback at runtime** — failing clearly is cheaper and more honest than hiding a different model's answer. The plan's manual fallback (another Bedrock model, only if it passes the same eval) is under Fallbacks and Cut Order.

## Decisions and Open Issues

**Decisions made by the learner**
- Frontend: Next.js (App Router) + TypeScript + Tailwind CSS, Inter and Geist Mono, no extra UI libraries, colors and styles strictly from the PRD.
- Backend: Python 3.12 for both Lambdas, FastAPI for the Control API, shared Pydantic models.
- The player always plays a local blob URL (after F5 the author picks the file again); the sample is a ready MP4 with a static JSON report in `public/` on Vercel.
- The Worker re-checks video length with `ffprobe`.
- The Bedrock spike (IAM policies, quotas, and the request size for 90 frames) is the main risk and is checked first.
- **The approved plan prevails.** Architecture, limits, timeouts, the model call, eval thresholds, fallbacks and the money rule (AWS credits only) are taken from it unchanged. Where the plan was silent, the spec adds the details marked below as derived; none of them changes a value or a decision of the plan.

**Derived implementation details (not learner choices; please correct anything wrong)**
- FastAPI runs only in the Control Lambda, wrapped by Mangum; the Worker is a plain handler because it is invoked with an event.
- The upload starts in the background as soon as the file is accepted; **Start analysis** waits for it.
- The model's `confidence` is kept as the plan says, in the format `low`/`medium`/`high`, stored for the eval only and never sent to the browser.
- Status-versus-evidence rules in Result validation; the 16 MB cap measured on the request as sent.
- Job records live 7 days, counters 2 days, the IP is stored hashed, and the sample carries a "sample analysis" label.
- Model call: non-streaming, about 420 seconds, no automatic retry.
- Text colors on the dark base and the lighter Missing label for contrast.

**The learner's uncertainty and how it is resolved.** The learner named the Bedrock side as the biggest unknown. It breaks down as the IAM action and its resource ARN, the quotas, and whether a request with 90 frames goes through. What clarified it so far: the documentation confirms the client, the model ID, the region, the IAM action name and the default quotas, and shows the exact ARN and the Opus 5.5 access criteria are not stated. The remaining check is a real call: first one small and one realistic call from the learner's machine on Tuesday, then a call from the Worker's role on Lambda on Wednesday. Evidence: the response with `usage` token counts and the status of each call recorded alongside the fixture.

**Open issues**
- Opus 5.5 access in the Bedrock console is unconfirmed. The Anthropic page lists Opus 4.8, Sonnet 5 and Haiku 4.5 as open to all customers; Sonnet 5.5, which the plan names as the fallback model, is also "see Access". Any replacement model must pass the same eval and be covered by the credits.
- Lambda concurrency: reserving 1 unit may be refused on a new account whose total quota is low. Part of the Lambda quota check.
- Whether `messages.parse` works on the Mantle client together with `output_config` (fallback written above); whether faster-whisper's native library builds on arm64; whether Mangum accepts the Function URL event shape; the request-size limit and regional-versus-global pricing for the Mantle endpoint. All are cheap to confirm in the first build slices.
- What the Worker does on an invalid model answer: fail immediately (current plan) or ask once more. Decide after the first eval runs show how often it happens.
- The `.gitignore` currently excludes `*.mp4`. The sample video must be committed so Vercel can serve it, so it needs an explicit exception, and it must be a clip the learner owns and that is small. Eval and test videos stay out of git.
- `prd.md > Open Questions`: none carried over.
