"""Run the reproducible DemoTrace quality gate over recorded live results.

Videos and raw runs stay local. Commit only hand labels in ``eval/cases`` and run this command
after each live Lambda analysis:

    .venv/bin/python eval/run.py

The default is deliberately strict: it refuses to claim a gate from fewer than four recorded,
hand-labelled cases and fails on any false ``shown`` in a negative case.
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
    negatives = [row for row in rows if row["negative"]]
    return {
        "cases_recorded": len(scored),
        "cases_missing_results": missing,
        "status_accuracy": sum(row["status_ok"] for row in rows) / len(rows) if rows else 0,
        "evidence_hit_rate": sum(row["evidence_hit"] for row in evidence_rows) / len(evidence_rows) if evidence_rows else None,
        "false_shown_on_negatives": sum(row["false_shown"] for row in negatives),
        "negatives": len(negatives),
    }


def passed(summary: dict) -> bool:
    return (
        summary["cases_recorded"] >= MIN_CASES
        and not summary["cases_missing_results"]
        and summary["status_accuracy"] >= MIN_STATUS_ACCURACY
        and summary["false_shown_on_negatives"] == 0
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=Path("eval/cases"))
    parser.add_argument("--runs", type=Path, default=Path("eval/runs"))
    args = parser.parse_args()
    scored, missing = run(args.cases, args.runs)
    for item in scored:
        print(report(item))
    summary = aggregate(scored, missing)
    evidence = "-" if summary["evidence_hit_rate"] is None else f"{summary['evidence_hit_rate']:.0%}"
    print(f"\nGate: {summary['cases_recorded']}/{MIN_CASES} recorded cases; status {summary['status_accuracy']:.0%}; evidence {evidence}; false Shown {summary['false_shown_on_negatives']}/{summary['negatives']}")
    if missing:
        print(f"Missing live runs: {', '.join(missing)}")
    if passed(summary):
        print("PASS")
        return 0
    print("FAIL — do not quote this as a quality result yet.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
