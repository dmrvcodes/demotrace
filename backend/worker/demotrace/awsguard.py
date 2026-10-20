"""Local settings and the AWS account guard for the CLI.

The learner's machine has several AWS profiles, and the default one belongs to another account. So
before any live call the CLI confirms, with STS, that the credentials in use belong to the account in
`DEMOTRACE_AWS_ACCOUNT_ID`, and refuses otherwise. Lambda does not need this: its role lives in the
right account by construction.
"""

import os
from pathlib import Path


class WrongAccount(Exception):
    pass


def load_env(path: Path = Path(".env")) -> None:
    """Read KEY=VALUE lines from a local, gitignored .env without overriding the real environment."""
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip("'\"")
        if key and value:
            os.environ.setdefault(key, value)


def profile(override: str | None = None) -> str | None:
    return override or os.environ.get("AWS_PROFILE") or None


def check_account(profile_name: str | None, *, session_factory=None) -> str:
    """Return the account ID if it matches DEMOTRACE_AWS_ACCOUNT_ID; raise WrongAccount otherwise."""
    expected = os.environ.get("DEMOTRACE_AWS_ACCOUNT_ID", "").replace("-", "").strip()
    if not expected:
        raise WrongAccount("DEMOTRACE_AWS_ACCOUNT_ID is not set (see .env.example); refusing to call AWS")
    # The default chain on this machine points at another account, so it is never used here:
    # without an explicit profile nothing is sent to AWS at all, not even this identity check.
    if not profile_name:
        raise WrongAccount("no AWS profile set (AWS_PROFILE in .env or --profile); refusing to call AWS")
    if session_factory is None:
        import boto3
        session_factory = boto3.Session
    session = session_factory(profile_name=profile_name)
    actual = session.client("sts").get_caller_identity()["Account"]
    if actual != expected:
        raise WrongAccount(
            f"credentials for profile {profile_name} belong to another account, not {expected}; "
            "refusing to call AWS"
        )
    return actual
