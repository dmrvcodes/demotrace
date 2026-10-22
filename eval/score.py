"""Score one analysis result against a hand-labelled case (`spec.md > Eval harness`).

Per claim: does the status match, and does a cited frame fall inside a labelled evidence range
(tolerance = the frame sampling step)? Separately: false Shown on negative cases, which is the
error that matters most for the kernel.

    python eval/score.py eval/cases/todomvc-01.json eval/runs/todomvc-01.result.json
"""

import json
import sys
from pathlib import Path

DEFAULT_TOLERANCE_S = 1.0  # the frame sampling step


def _hit(times: list[float], ranges: list[list[float]], tolerance: float) -> bool:
    return any(start - tolerance <= t <= end + tolerance for t in times for start, end in ranges)


def score(case: dict, result: dict, tolerance: float = DEFAULT_TOLERANCE_S) -> dict:
    got = {c["claim_id"]: c for c in result["claims"]}
    rows = []
    for label in case["claims"]:
        answer = got.get(label["id"], {})
        evidence = answer.get("evidence", [])
        frame_times = [e["t"] for e in evidence if e["kind"] == "frame"]
        any_times = [e["t"] for e in evidence]
        ranges = label["evidence_ranges_s"]
        rows.append({
            "id": label["id"],
            "expected": label["expected"],
            "got": answer.get("status"),
            "status_ok": answer.get("status") == label["expected"],
            "negative": label["negative"],
            "false_shown": bool(label["negative"]) and answer.get("status") == "shown",
            # Shown is judged on frames; Told only may rest on a slide frame or a speech segment.
            "evidence_hit": (None if not ranges else
                             _hit(frame_times if label["expected"] == "shown" else any_times, ranges, tolerance)),
            "cited": [f"{e['ref_id']}@{e['t']:.1f}" for e in evidence],
        })
    hits = [r["evidence_hit"] for r in rows if r["evidence_hit"] is not None]
    negatives = [r for r in rows if r["negative"]]
    return {
        "case_id": case["case_id"],
        "status_accuracy": sum(r["status_ok"] for r in rows) / len(rows),
        "evidence_hit_rate": (sum(hits) / len(hits)) if hits else None,
        "false_shown_on_negatives": sum(r["false_shown"] for r in negatives),
        "negatives": len(negatives),
        "rows": rows,
    }


def report(scored: dict) -> str:
    lines = [f"{scored['case_id']}: status {scored['status_accuracy']:.0%}, evidence hits "
             + (f"{scored['evidence_hit_rate']:.0%}" if scored["evidence_hit_rate"] is not None else "-")
             + f", false Shown on negatives {scored['false_shown_on_negatives']}/{scored['negatives']}"]
    for r in scored["rows"]:
        mark = "ok " if r["status_ok"] else "MISS"
        hit = {True: "in range", False: "OUT of range", None: "-"}[r["evidence_hit"]]
        neg = f" [{r['negative']}]" if r["negative"] else ""
        lines.append(f"  {mark} {r['id']} expected {r['expected']:9} got {str(r['got']):9} evidence {hit:12} "
                     f"{', '.join(r['cited']) or '-'}{neg}")
    return "\n".join(lines)


if __name__ == "__main__":
    case_path, result_path = map(Path, sys.argv[1:3])
    print(report(score(json.loads(case_path.read_text()), json.loads(result_path.read_text()))))
