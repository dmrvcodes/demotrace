# Eval recorder

Scripted, reproducible recordings for the hand-labelled cases in `eval/cases/`.
Each script drives headless Chromium (Playwright) through a demo, records one continuous
1280×720 video, and `mux.js` adds narration synthesized with Amazon Polly (neural voice Arthur).

```bash
# Playwright with a Chromium build, e.g. from any project that has it installed
export PW_PATH=/path/to/node_modules/playwright
./polly.sh similar-ui-01               # narration clips (needs AWS credentials for Polly)
node similar-ui-01.js && node mux.js similar-ui-01
cp similar-ui-01.mp4 ../../.local/eval/videos/
```

| Case | What it tests |
|---|---|
| `todomvc-01.js` | Baseline: two shown results, a hovered-but-not-clicked button, a promise slide, a missing claim. Older one-off script; it writes `raw.webm` and its narration was muxed by hand. |
| `similar-ui-01.js` | A hover that reveals "View profile" without opening it; "as you can see" narration with nothing on screen. Uses https://the-internet.herokuapp.com. |
| `promise-slide-01.js` | A feature promised on a title slide; a screenshot of a button inside a slide; a two-part claim where only one part is shown. Local mock app in `pulse/`. |
| `silent-missing-01.js` | No audio. A 0.7 s toast between two 1-second samples, a caption-only promise, a claim with no evidence. Local mock app in `notely/`. |

Videos are not committed (`.local/` is ignored). Timings each script actually hit are written to
`<case>.timing.json`; the labels in `eval/cases/` were set from those marks and checked frame by frame.
