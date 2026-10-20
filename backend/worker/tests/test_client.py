"""The client wrapper against a stub: no network, no AWS, no cost."""

from types import SimpleNamespace

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


def response(stop_reason="end_turn", parsed=ANSWER, category=None):
    return SimpleNamespace(
        stop_reason=stop_reason,
        stop_details=SimpleNamespace(category=category) if category else None,
        parsed_output=parsed,
        usage=SimpleNamespace(to_dict=lambda: {"input_tokens": 1200, "output_tokens": 300}),
        _request_id="req_test",
    )


class StubClient:
    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.calls = []
        self.messages = self

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


def request():
    media, images, claims = small_case()
    return build_request(media, images, claims)


def connection_error():
    return anthropic.APIConnectionError(request=httpx2.Request("POST", "https://bedrock-mantle.invalid"))


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)


def test_returns_the_parsed_answer_with_usage():
    stub = StubClient(response())
    result = llm.call_model(stub, request())
    assert result.answer == ANSWER
    assert result.usage["input_tokens"] == 1200 and result.request_id == "req_test"
    sent = stub.calls[0]
    assert sent["output_format"] is ModelAnswer
    assert sent["output_config"] == {"effort": "high"}


def test_refusal_fails_with_its_category():
    with pytest.raises(ModelError) as err:
        llm.call_model(StubClient(response("refusal", parsed=None, category="cyber")), request())
    assert err.value.code == ErrorCode.MODEL_REFUSED and err.value.detail == "cyber"


def test_cut_off_answer_is_invalid():
    with pytest.raises(ModelError) as err:
        llm.call_model(StubClient(response("max_tokens")), request())
    assert err.value.code == ErrorCode.MODEL_INVALID_OUTPUT


def test_missing_parsed_answer_is_invalid():
    with pytest.raises(ModelError) as err:
        llm.call_model(StubClient(response(parsed=None)), request())
    assert err.value.code == ErrorCode.MODEL_INVALID_OUTPUT


def test_one_retry_on_a_network_error_when_time_allows():
    stub = StubClient(connection_error(), response())
    assert llm.call_model(stub, request()).answer == ANSWER
    assert len(stub.calls) == 2


def test_no_retry_when_the_lambda_is_running_out_of_time():
    stub = StubClient(connection_error(), response())
    with pytest.raises(ModelError) as err:
        llm.call_model(stub, request(), time_left_s=lambda: 300)
    assert err.value.code == ErrorCode.MODEL_UNAVAILABLE and len(stub.calls) == 1


def test_only_one_retry():
    stub = StubClient(connection_error(), connection_error(), response())
    with pytest.raises(ModelError):
        llm.call_model(stub, request())
    assert len(stub.calls) == 2
