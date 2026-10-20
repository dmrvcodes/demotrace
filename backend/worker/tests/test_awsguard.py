import os

import pytest

from demotrace import awsguard


class FakeSession:
    account = "111122223333"

    def __init__(self, profile_name=None):
        self.profile_name = profile_name

    def client(self, name):
        assert name == "sts"
        return self

    def get_caller_identity(self):
        return {"Account": self.account}


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in ("DEMOTRACE_AWS_ACCOUNT_ID", "AWS_PROFILE", "GUARD_TEST_KEY"):
        monkeypatch.delenv(key, raising=False)


def test_refuses_without_an_expected_account():
    with pytest.raises(awsguard.WrongAccount, match="not set"):
        awsguard.check_account("hackathon", session_factory=FakeSession)


def test_refuses_without_a_profile_and_never_calls_sts(monkeypatch):
    monkeypatch.setenv("DEMOTRACE_AWS_ACCOUNT_ID", "1111-2222-3333")

    def must_not_be_called(**kwargs):
        raise AssertionError("STS was called without an explicit profile")

    with pytest.raises(awsguard.WrongAccount, match="no AWS profile"):
        awsguard.check_account(None, session_factory=must_not_be_called)


def test_refuses_another_account(monkeypatch):
    monkeypatch.setenv("DEMOTRACE_AWS_ACCOUNT_ID", "4444-5555-6666")
    with pytest.raises(awsguard.WrongAccount, match="another account"):
        awsguard.check_account("work", session_factory=FakeSession)


def test_accepts_the_expected_account_with_or_without_dashes(monkeypatch):
    monkeypatch.setenv("DEMOTRACE_AWS_ACCOUNT_ID", "1111-2222-3333")
    assert awsguard.check_account("hackathon", session_factory=FakeSession) == "111122223333"


def test_env_file_fills_gaps_but_never_overrides(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("# comment\nAWS_PROFILE=hackathon\nGUARD_TEST_KEY='from file'\nEMPTY=\n")
    monkeypatch.setenv("AWS_PROFILE", "already-set")
    awsguard.load_env(env)
    assert os.environ["AWS_PROFILE"] == "already-set"
    assert os.environ["GUARD_TEST_KEY"] == "from file"
    assert "EMPTY" not in os.environ
