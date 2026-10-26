# DemoTrace

**DemoTrace checks whether a product demo proves its claims, rather than merely saying them.**

Upload an MP4 demo, write three to five observable claims, and get an evidence map. Every claim
is marked **Shown**, **Told only**, or **Missing**, with a click that seeks directly to the cited
frame or speech segment.

Live app: [demotrace.vercel.app](https://demotrace.vercel.app) ·
Demo video (2:28): [YouTube](https://www.youtube.com/watch?v=R_W9WrFR5QY)

## Why it is useful

A polished demo can make a promised feature look finished. DemoTrace separates the promise from
the visible result before a hackathon participant records their final submission.

```text
Browser ──presigned POST──> S3 (versioned, short-lived)
   │                              │
   └── Control Lambda ──event──> Worker Lambda (ffmpeg + Whisper + Claude)
                                      │
                                  DynamoDB result
```

The worker pins the uploaded S3 object version, extracts labelled frames and English speech,
asks Claude for structured assessments, validates every cited ID itself, writes server-computed
timestamps, then removes every version of the uploaded video. Job state transitions are
conditional, so duplicate deliveries and late writers cannot overwrite a report.

## Run locally

The UI needs only Node.js 22:

```bash
cd web
cp .env.example .env.local
npm ci
npm run dev
```

For a live backend, set `NEXT_PUBLIC_API_BASE_URL` to the Control Lambda Function URL. The
worker additionally requires `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL`; do not commit either.

```bash
PYTHONPATH=backend/worker:backend/shared:backend/control \
  .venv/bin/pytest -q backend/worker/tests backend/control/tests eval/tests
npm run lint --prefix web
npm run build --prefix web
```

## Evaluation

Hand-labelled cases live in [`eval/cases`](eval/cases). Raw videos and Lambda outputs remain
local by design. Run the honest quality gate with:

```bash
.venv/bin/python eval/run.py --min-cases 6
```

It requires six recorded, hand-labelled cases, status accuracy of at least 70%, and **zero false
Shown verdicts on negative cases**. The current 25 October live Lambda → Claude pass has six
recordings (27 claims): **100% status accuracy, 100% evidence hits and 0/16 false Shown**. This is
a small, hand-labelled smoke eval—not a general accuracy claim—and raw videos and responses remain
out of Git.

## Security and operations

- Per-job bearer tokens gate reports; only their SHA-256 hashes reach DynamoDB.
- Uploads use presigned POST with MP4 and 150 MB constraints.
- S3 versioning, immediate worker cleanup and a one-day lifecycle rule protect privacy.
- Terraform state is encrypted in a versioned S3 backend; the Worker image deploys by digest.
- GitHub Actions uses a scoped OIDC deploy role and immutable action references. That role cannot
  mutate IAM execution policies.

The production-only safety check uses two owned local MP4s and one real model call. It verifies
unauthenticated report access, pinned S3 versions despite an overwrite, S3 cleanup, log privacy,
and the temporary capacity off switch. It restores the Lambda configuration even on failure; do
not run it during a public demo because it sets capacity to zero briefly.

```bash
AWS_PROFILE=demotrace-key .venv/bin/python scripts/live_system_check.py \
  --video .local/eval/videos/todomvc-01.mp4 \
  --replacement .local/eval/videos/silent-missing-01.mp4
```

## Attribution

The **Try with sample** video is a scripted recording of the
[TodoMVC demo](https://demo.playwright.dev/todomvc) hosted by Playwright. TodoMVC is MIT-licensed.
The narration is generated with Amazon Polly (neural voice Arthur). The evidence map shown with it is
a real, recorded result from the deployed Worker (`claude-sonnet-4-6`), labelled in the interface as
a recorded analysis rather than a live one.

Built with the Devpost Learn Skill Pack for **Build With AI: Basics**.

## Demo capture

The owner-facing, shot-by-shot capture plan for the submission video is
[`devpost/demo-run-sheet.md`](devpost/demo-run-sheet.md). It uses two genuine
production runs to show the core improvement loop: **Told only** in a weak
recording, then **Shown** after the demonstrable action is added.
