---
doc: scope
status: approved
---

# DemoTrace

DemoTrace maps every product claim to the exact moment the demo proves it.

## The Unique Kernel
It separates what a demo *says* from what it *shows*. A slide that promises a feature is not proof: that claim stays **Told only** until the video shows the result on screen. There is no score — only evidence the author can click and check.

## Who It's For
A developer entering a hackathon, usually alone, who needs a demo video convincing enough for judges. The first user is the learner themselves, preparing the final submission.
Today this person re-watches the video over and over, checks it against a checklist on paper, or just hopes the judges will take the slides at their word.

## The Core Loop
Upload a draft video (up to 3 minutes) and 3–5 claims about the product → see the weak spots (a claim marked **Told only** instead of **Shown**) → re-record the weak part → upload again → get **Shown** on every claim.
They come back because every re-record is a new check: the judges watch quickly, so each claim has to be proven without filler.

## Inspiration & Identity
No visual direction has been shared yet; `3-prd` will ask. The intended tone is evidence over verdicts: every claim is tied to a moment the author can click, not to a number.

## Why This Matters to the Learner
"Maximize the chances of winning." Judges skim videos, so every claim must be proven, and the learner will run their own final demo through DemoTrace before submitting.

## What "Working" Looks Like
Someone opens DemoTrace, uploads a video up to 3 minutes (or tries the built-in sample), types 3–5 claims, and sees a clear processing status. They then get the video next to a card per claim, each marked **Shown**, **Told only** or **Missing**.
The "aha" beat: clicking the evidence on a card jumps the player to the exact second where the claimed feature really works on screen, rather than sitting on a presentation slide.
The demo story: a weak first version with Told only claims → re-record → every claim Shown.

## The POC Boundary
**In:**
- Analysis of a video up to 3 minutes against 3–5 claims.
- Three statuses: Shown, Told only, Missing.
- Click-to-seek from a piece of evidence to its timestamp.
- A "Try with sample" button, so judges and the learner can test the system in one click without uploading a file.
- A clear processing status, and deletion of the video after analysis.

**Nice-to-have (first to go if time runs short):**
- Frame thumbnails (a text timestamp is enough).
- Export of the report to Markdown.

## Later
Script generation, video editing, accounts and history, collaboration, YouTube links, voice and gestures, comparing videos, sharing by link, suggesting claims automatically.

## Explicitly Cut
- **A numeric score** — the point is verifiable evidence the author can check, not a judgment number.
- **Non-English speech** — the proof of concept supports English only.
