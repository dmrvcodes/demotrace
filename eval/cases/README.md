# Recording queue

The quality gate needs four distinct videos and their genuine Lambda outputs in `eval/runs/`
(which is intentionally ignored). Do not add fabricated results to make the gate pass.

Record and hand-label these next:

1. `promise-slide-01`: a feature promised on a title slide, never demonstrated — expected `told_only`.
2. `similar-ui-01`: an interface that resembles the claim but does not show its result — expected `told_only` or `missing`.
3. `silent-missing-01`: no narration and no on-screen evidence for one claim — expected `missing`.

For each case, commit only a JSON label matching `todomvc-01.json`; save the Lambda result as
`eval/runs/<case_id>.lambda.json`, then run `.venv/bin/python eval/run.py`.
