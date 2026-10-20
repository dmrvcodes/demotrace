import json

from demotrace.llm.client import ModelResult
from demotrace.llm.fixtures import FIXTURE_KIND, write_fixture
from demotrace.llm.prompt import build_request
from demotrace.smoke import load_claims, small_case

from .test_client import ANSWER


def test_fixture_keeps_ids_times_and_answer_but_no_media(tmp_path):
    media, images, claims = small_case()
    req = build_request(media, images, claims)
    result = ModelResult(answer=ANSWER, usage={"input_tokens": 1, "output_tokens": 2},
                         stop_reason="end_turn", request_id="req_1", elapsed_s=1.5)
    path = write_fixture(tmp_path, "case", media, claims, req, result)
    raw = path.read_text()
    data = json.loads(raw)

    assert data["kind"] == FIXTURE_KIND
    assert data["frames"] == [{"id": "F001", "t": 0.0}]
    assert data["segments"] == [{"id": "S01", "start": 0.0, "end": 2.5}]
    assert data["claims"][0] == {"id": "C1", "text": claims[0]}
    assert data["answer"]["claims"][0]["status"] == "shown"
    assert data["request_bytes"] == req.size_bytes
    # No frame data and no transcript text in a fixture.
    assert "base64" not in raw and "/9j/" not in raw
    assert media.segments[0].text not in raw


def test_claims_file_accepts_a_list_or_an_object(tmp_path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps(["One", "Two", " Three "]))
    b.write_text(json.dumps({"claims": ["One", "Two", "Three", "Four"]}))
    assert load_claims(a) == ["One", "Two", "Three"]
    assert len(load_claims(b)) == 4
