import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from run import aggregate, passed
from score import score


def test_false_shown_is_counted_for_negative_missing_claim():
    case = {"case_id": "negative", "claims": [{"id": "C1", "expected": "missing", "negative": "absent", "evidence_ranges_s": []}]}
    result = {"claims": [{"claim_id": "C1", "status": "shown", "evidence": [{"ref_id": "F001", "kind": "frame", "t": 1}]}]}
    scored = score(case, result)
    assert scored["false_shown_on_negatives"] == 1


def test_gate_requires_four_recorded_cases_and_no_false_shown():
    base = {"rows": [{"status_ok": True, "evidence_hit": True, "negative": True, "false_shown": False}]}
    assert not passed(aggregate([base] * 3, []))
    assert passed(aggregate([base] * 4, []))
    failed = {"rows": [{"status_ok": True, "evidence_hit": True, "negative": True, "false_shown": True}]}
    assert not passed(aggregate([base, base, base, failed], []))
