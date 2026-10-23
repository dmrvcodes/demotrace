"""The model client through the real Anthropic SDK, with the HTTP transport mocked: no network, no cost."""

import json

import anthropic
import httpx2
import pytest

from demotrace.llm import ModelError
from demotrace.llm import client as llm
from demotrace.llm.prompt import build_request
from demotrace.smoke import small_case
from demotrace_shared.analysis import ModelAnswer
from demotrace_shared.errors import ErrorCode

ANSWER = ModelAnswer.model_validate({"claims": [
    {"claim_id": "C1", "evidence_ids": ["F001"], "explanation": "The export dialog says the CSV downloaded.",
     "status": "shown", "confidence": "high"},
    {"claim_id": "C2", "evidence_ids": [], "explanation": "Sharing never appears.",
     "status": "missing", "confidence": "medium"},
]})


def message(stop_reason="end_turn", text=None, extra=None):
    content = [] if text is None and stop_reason == "refusal" else [{"type": "text", "text": text or ANSWER.model_dump_json()}]
    body = {"id": "msg_1", "type": "message", "role": "assistant", "model": "test-model", "content": content,
            "stop_reason": stop_reason, "stop_sequence": None,
            "usage": {"input_tokens": 1200, "output_tokens": 300}, **(extra or {})}
    return httpx2.Response(200, json=body, headers={"request-id": "req_ok"})


def error(status, kind):
    return httpx2.Response(status, json={"type": "error", "error": {"type": kind, "message": kind}},
                           headers={"request-id": f"req_{status}"})


class Server:
    """Answers queued responses in order and records every request body."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.bodies = []

    def __call__(self, request):
        self.bodies.append(json.loads(request.content))
        return self.responses.pop(0)

    def client(self):
        return llm.make_client("sk-ant-test", http_client=anthropic.DefaultHttpxClient(transport=httpx2.MockTransport(self)))


def request():
    media, images, claims = small_case()
    return build_request(media, images, claims)


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)


def call(server, **kw):
    return llm.call_model(server.client(), request(), **kw)


def test_returns_the_validated_answer_with_usage_and_request_id():
    server = Server(message())
    result = call(server)
    assert result.answer == ANSWER and result.request_id == "req_ok"
    assert result.usage["input_tokens"] == 1200
    sent = server.bodies[0]
    assert sent["output_config"]["effort"] == "high"
    assert sent["output_config"]["format"] == {"type": "json_schema", "schema": llm.ANSWER_SCHEMA}


def test_schema_matches_the_answer_model():
    item = llm.ANSWER_SCHEMA["properties"]["claims"]["items"]
    assert set(item["properties"]) == set(item["required"]) == set(ModelAnswer.model_fields["claims"].annotation.__args__[0].model_fields)


def test_overloaded_529_is_retried_once():
    server = Server(error(529, "overloaded_error"), message())
    assert call(server).answer == ANSWER
    assert len(server.bodies) == 2


def test_other_5xx_is_retried_once_then_unavailable():
    server = Server(error(503, "api_error"), error(503, "api_error"))
    with pytest.raises(ModelError) as err:
        call(server)
    assert err.value.code == ErrorCode.MODEL_UNAVAILABLE and err.value.request_id == "req_503"
    assert len(server.bodies) == 2


def test_no_retry_when_the_lambda_is_running_out_of_time():
    server = Server(error(529, "overloaded_error"), message())
    with pytest.raises(ModelError) as err:
        call(server, time_left_s=lambda: 300)
    assert err.value.code == ErrorCode.MODEL_UNAVAILABLE and len(server.bodies) == 1


def test_refusal_is_reported_as_a_refusal_not_invalid_output():
    server = Server(message("refusal", extra={"stop_details": {"type": "refusal", "category": "cyber", "explanation": None}}))
    with pytest.raises(ModelError) as err:
        call(server)
    assert err.value.code == ErrorCode.MODEL_REFUSED and err.value.request_id == "req_ok"


def test_cut_off_answer_is_reported_as_cut_off():
    server = Server(message("max_tokens", text='{"claims": [{"claim_id": "C1", "evid'))
    with pytest.raises(ModelError) as err:
        call(server)
    assert err.value.code == ErrorCode.MODEL_INVALID_OUTPUT and "cut off" in err.value.detail


def test_request_too_large_413():
    with pytest.raises(ModelError) as err:
        call(Server(error(413, "request_too_large")))
    assert err.value.code == ErrorCode.REQUEST_TOO_LARGE


def test_bad_request_is_rejected_without_retry():
    server = Server(error(400, "invalid_request_error"))
    with pytest.raises(ModelError) as err:
        call(server)
    assert err.value.code == ErrorCode.MODEL_REJECTED_REQUEST and len(server.bodies) == 1


def test_auth_failure_is_unavailable():
    with pytest.raises(ModelError) as err:
        call(Server(error(401, "authentication_error")))
    assert err.value.code == ErrorCode.MODEL_UNAVAILABLE


def test_answer_that_breaks_the_schema_is_invalid():
    with pytest.raises(ModelError) as err:
        call(Server(message(text='{"claims": [{"claim_id": "C1"}]}')))
    assert err.value.code == ErrorCode.MODEL_INVALID_OUTPUT


def test_client_requires_an_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ModelError) as err:
        llm.make_client()
    assert err.value.code == ErrorCode.MODEL_UNAVAILABLE and "ANTHROPIC_API_KEY" in err.value.detail
