"""Call Claude Opus 5.5 on Amazon Bedrock with structured output, and turn every failure into a code."""

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

REGION = os.environ.get("AWS_REGION", "us-east-1")
# One call must never eat the whole 15-minute Lambda budget, so no automatic SDK retries.
TIMEOUT_S = 420
RETRY_DELAY_S = 5
RETRY_MIN_TIME_LEFT_S = 450


@dataclass
class ModelResult:
    answer: ModelAnswer
    usage: dict
    stop_reason: str
    request_id: str | None
    elapsed_s: float


def make_client(profile: str | None = None):
    """Credentials come from the normal AWS chain: your profile locally, the function's role in Lambda."""
    return anthropic.AnthropicBedrockMantle(
        aws_region=REGION, aws_profile=profile, timeout=TIMEOUT_S, max_retries=0,
    )


def _credentials_error() -> tuple[type[BaseException], ...]:
    try:
        from botocore.exceptions import BotoCoreError
        return (BotoCoreError,)
    except ImportError:
        return ()


def call_model(client, request: ModelRequest, *,
               time_left_s: Callable[[], float] = lambda: math.inf) -> ModelResult:
    """One call, plus one retry on throttling or a server/network error if enough time remains."""
    retried = False
    while True:
        started = time.monotonic()
        try:
            response = client.messages.parse(**request.params, output_format=ModelAnswer)
            break
        except (anthropic.RateLimitError, anthropic.InternalServerError, anthropic.APIConnectionError) as err:
            if not retried and time_left_s() > RETRY_MIN_TIME_LEFT_S:
                retried = True
                time.sleep(RETRY_DELAY_S)
                continue
            raise ModelError(ErrorCode.MODEL_UNAVAILABLE, type(err).__name__) from err
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError, anthropic.NotFoundError) as err:
            # Missing model access, a wrong IAM action or a wrong model ID: the message says which.
            raise ModelError(ErrorCode.MODEL_UNAVAILABLE, f"{type(err).__name__}: {err.message}") from err
        except anthropic.BadRequestError as err:
            raise ModelError(ErrorCode.MODEL_REJECTED_REQUEST, err.message) from err
        except pydantic.ValidationError as err:
            raise ModelError(ErrorCode.MODEL_INVALID_OUTPUT, str(err)[:300]) from err
        except _credentials_error() as err:
            raise ModelError(ErrorCode.MODEL_UNAVAILABLE, f"AWS credentials: {err}") from err
    elapsed = round(time.monotonic() - started, 1)
    request_id = getattr(response, "_request_id", None)

    if response.stop_reason == "refusal":
        category = getattr(getattr(response, "stop_details", None), "category", None)
        raise ModelError(ErrorCode.MODEL_REFUSED, str(category), request_id)
    if response.stop_reason == "max_tokens":
        raise ModelError(ErrorCode.MODEL_INVALID_OUTPUT, "answer cut off at max_tokens", request_id)
    if response.parsed_output is None:
        raise ModelError(ErrorCode.MODEL_INVALID_OUTPUT, "no parsed answer", request_id)

    return ModelResult(
        answer=response.parsed_output,
        usage=response.usage.to_dict(),
        stop_reason=response.stop_reason,
        request_id=request_id,
        elapsed_s=elapsed,
    )
