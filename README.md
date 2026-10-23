# DemoTrace

**DemoTrace checks whether a product demo proves its claims, rather than merely saying them.**

Upload an MP4 demo, write three to five observable claims, and get an evidence map. Every claim
is marked **Shown**, **Told only**, or **Missing**, with a click that seeks directly to the cited
frame or speech segment.

Live app: [demotrace.vercel.app](https://demotrace.vercel.app)

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
.venv/bin/python eval/run.py
```

It requires four recorded, hand-labelled cases, status accuracy of at least 70%, and **zero false
Shown verdicts on negative cases**. The repository currently contains one real labelled run; the
gate intentionally fails until the remaining three cases are recorded. No aggregate quality claim
is made before that gate passes.

## Security and operations

- Per-job bearer tokens gate reports; only their SHA-256 hashes reach DynamoDB.
- Uploads use presigned POST with MP4 and 150 MB constraints.
- S3 versioning, immediate worker cleanup and a one-day lifecycle rule protect privacy.
- Terraform state is encrypted in a versioned S3 backend; the Worker image deploys by digest.
- GitHub Actions uses a scoped OIDC deploy role and immutable action references. That role cannot
  mutate IAM execution policies.

## Attribution

The current UI sample includes a DemoTrace-authored promise slide and an excerpt of **Big Buck
Bunny** by the Blender Foundation, licensed [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/).
It is an interactive example only; it is not presented as a live model result. It will be replaced
with an owned TodoMVC evidence-map sample before submission.

Built with the Devpost Learn Skill Pack for **Build With AI: Basics**.
