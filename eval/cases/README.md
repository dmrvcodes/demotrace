# Recording queue

The quality gate needs four distinct videos and their genuine Lambda outputs in `eval/runs/`
(which is intentionally ignored). Do not add fabricated results to make the gate pass.

The current six-case smoke gate is recorded, including `board-02` (a local Kanban board with two
visible state transitions and a coming-soon digest promise) and `inbox-02` (a local inbox with
archive/search state transitions and a coming-soon scheduled-delivery promise). To reproduce the
quoted six-case result, run `python eval/run.py --min-cases 6` after the six local Lambda result
files have been produced.

For each case, commit only a JSON label matching `todomvc-01.json`; save the Lambda result as
`eval/runs/<case_id>.lambda.json`, then run `.venv/bin/python eval/run.py`.
