"""Run the reproducible DemoTrace quality gate over recorded live results.

Videos and raw runs stay local. Commit only hand labels in ``eval/cases`` and run this command
after each live Lambda analysis:

    .venv/bin/python eval/run.py

The default is deliberately strict: it refuses to claim a gate from fewer than four recorded,
hand-labelled cases and fails on any false ``shown`` for a claim expected not to be shown.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from score import report, score

MIN_CASES = 4
MIN_STATUS_ACCURACY = 0.70


def run(cases_dir: Path, runs_dir: Path) -> tuple[list[dict], list[str]]:
    scored, missing = [], []
    for case_path in sorted(cases_dir.glob("*.json")):
        case = json.loads(case_path.read_text())
        result_path = runs_dir / f"{case['case_id']}.lambda.json"
        if not result_path.exists():
            missing.append(case["case_id"])
            continue
        scored.append(score(case, json.loads(result_path.read_text())))
    return scored, missing


def aggregate(scored: list[dict], missing: list[str]) -> dict:
    rows = [row for item in scored for row in item["rows"]]
    evidence_rows = [row for row in rows if row["evidence_hit"] is not None]
    non_shown = [row for row in rows if row["expected"] != "shown"]
    return {
        "cases_recorded": len(scored),
        "cases_missing_results": missing,
        "status_accuracy": sum(row["status_ok"] for row in rows) / len(rows) if rows else 0,
        "evidence_hit_rate": sum(row["evidence_hit"] for row in evidence_rows) / len(evidence_rows) if evidence_rows else None,
        "false_shown_on_non_shown": sum(row["false_shown"] for row in non_shown),
        "non_shown": len(non_shown),
    }


def passed(summary: dict, min_cases: int = MIN_CASES) -> bool:
    return (
        summary["cases_recorded"] >= min_cases
        and not summary["cases_missing_results"]
        and summary["status_accuracy"] >= MIN_STATUS_ACCURACY
        and summary["false_shown_on_non_shown"] == 0
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=Path("eval/cases"))
    parser.add_argument("--runs", type=Path, default=Path("eval/runs"))
    parser.add_argument("--min-cases", type=int, default=MIN_CASES,
                        help="minimum distinct recorded cases required for this gate")
    args = parser.parse_args()
    if args.min_cases < 1:
        raise SystemExit("--min-cases must be at least 1")
    scored, missing = run(args.cases, args.runs)
    for item in scored:
        print(report(item))
    summary = aggregate(scored, missing)
    evidence = "-" if summary["evidence_hit_rate"] is None else f"{summary['evidence_hit_rate']:.0%}"
    print(f"\nGate: {summary['cases_recorded']}/{args.min_cases} recorded cases; status {summary['status_accuracy']:.0%}; evidence {evidence}; false Shown {summary['false_shown_on_non_shown']}/{summary['non_shown']}")
    if missing:
        print(f"Missing live runs: {', '.join(missing)}")
    if passed(summary, args.min_cases):
        print("PASS")
        return 0
    print("FAIL — do not quote this as a quality result yet.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
