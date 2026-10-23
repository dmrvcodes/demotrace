"""Call Claude directly with structured output, and turn every failure into a code.

`messages.create` with a JSON schema, not `messages.parse`: parse validates the JSON before the
stop reason is visible, so a refusal or a cut-off answer would surface as invalid output. Here the
stop reason is checked first, then the text is validated against the Pydantic model.
"""

import math
import os
import time
from collections.abc import Callable
from dataclasses import dataclass

import anthropic
import pydantic

from demotrace_shared.analysis import ModelAnswer
from demotrace_shared.errors import ErrorCode

from . import ModelError
from .prompt import ModelRequest

# One call must never eat the whole 15-minute Lambda budget, so no automatic SDK retries.
TIMEOUT_S = 420
RETRY_DELAY_S = 5
RETRY_MIN_TIME_LEFT_S = 450

_STATUSES = ["shown", "told_only", "missing"]
_CONFIDENCES = ["low", "medium", "high"]

# The answer's JSON schema, written out so it is explicit and strict-mode compatible
# (every property required, no extra keys). A test keeps it in step with ModelAnswer.
ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim_id": {"type": "string"},
                    "evidence_ids": {"type": "array", "items": {"type": "string"}},
                    "explanation": {"type": "string"},
                    "status": {"type": "string", "enum": _STATUSES},
                    "confidence": {"type": "string", "enum": _CONFIDENCES},
                },
                "required": ["claim_id", "evidence_ids", "explanation", "status", "confidence"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["claims"],
    "additionalProperties": False,
}

# Retried once when enough Lambda time remains. OverloadedError (529) is not an
# InternalServerError subclass, so it is listed explicitly.
_RETRYABLE = (anthropic.RateLimitError, anthropic.InternalServerError, anthropic.OverloadedError,
              anthropic.APIConnectionError)


@dataclass
class ModelResult:
    answer: ModelAnswer
    usage: dict
    stop_reason: str
    request_id: str | None
    elapsed_s: float


def make_client(api_key: str | None = None, **client_options) -> anthropic.Anthropic:
    """Create the direct Claude client. The Worker passes the key from Secrets Manager; local runs
    fall back to ANTHROPIC_API_KEY from the gitignored .env. The key is never logged."""
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ModelError(ErrorCode.MODEL_UNAVAILABLE, "ANTHROPIC_API_KEY is not set")
    return anthropic.Anthropic(api_key=api_key, timeout=TIMEOUT_S, max_retries=0, **client_options)


def _request_id(err: BaseException) -> str | None:
    response = getattr(err, "response", None)
    return response.headers.get("request-id") if response is not None else None


def _params(request: ModelRequest) -> dict:
    params = dict(request.params)
    params["output_config"] = {**params.get("output_config", {}),
                               "format": {"type": "json_schema", "schema": ANSWER_SCHEMA}}
    return params


def call_model(client, request: ModelRequest, *,
               time_left_s: Callable[[], float] = lambda: math.inf) -> ModelResult:
    """One call, plus one retry on throttling, overload or a server/network error if time remains."""
    retried = False
    params = _params(request)
    while True:
        started = time.monotonic()
        try:
            response = client.messages.create(**params)
            break
        except anthropic.RequestTooLargeError as err:
            raise ModelError(ErrorCode.REQUEST_TOO_LARGE, "413 from the API", _request_id(err)) from err
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError, anthropic.NotFoundError) as err:
            # Invalid credentials or model access are reported as a safe application error.
            raise ModelError(ErrorCode.MODEL_UNAVAILABLE, type(err).__name__, _request_id(err)) from err
        except (*_RETRYABLE, anthropic.APIStatusError) as err:
            server_side = isinstance(err, _RETRYABLE) or getattr(err, "status_code", 0) >= 500
            if not server_side:
                raise ModelError(ErrorCode.MODEL_REJECTED_REQUEST, type(err).__name__, _request_id(err)) from err
            if not retried and time_left_s() > RETRY_MIN_TIME_LEFT_S:
                retried = True
                time.sleep(RETRY_DELAY_S)
                continue
            raise ModelError(ErrorCode.MODEL_UNAVAILABLE, type(err).__name__, _request_id(err)) from err
    elapsed = round(time.monotonic() - started, 1)
    request_id = getattr(response, "_request_id", None)

    if response.stop_reason == "refusal":
        category = getattr(getattr(response, "stop_details", None), "category", None)
        raise ModelError(ErrorCode.MODEL_REFUSED, str(category), request_id)
    if response.stop_reason == "max_tokens":
        raise ModelError(ErrorCode.MODEL_INVALID_OUTPUT, "answer cut off at max_tokens", request_id)
    text = next((block.text for block in response.content if block.type == "text"), None)
    if not text:
        raise ModelError(ErrorCode.MODEL_INVALID_OUTPUT, "no text in the answer", request_id)
    try:
        answer = ModelAnswer.model_validate_json(text)
    except pydantic.ValidationError as err:
        raise ModelError(ErrorCode.MODEL_INVALID_OUTPUT, "answer does not match the schema", request_id) from err

    return ModelResult(
        answer=answer,
        usage=response.usage.to_dict(),
        stop_reason=response.stop_reason,
        request_id=request_id,
        elapsed_s=elapsed,
    )
