"""Tests for acli.errors."""

from acli.errors import (
    ACLIError,
    ConflictError,
    InvalidArgsError,
    NotFoundError,
    PreconditionError,
    suggest_flag,
)
from acli.exit_codes import ExitCode


class TestACLIError:
    def test_default_code(self) -> None:
        err = ACLIError("something broke")
        assert err.code == ExitCode.GENERAL_ERROR
        assert str(err) == "something broke"
        assert err.hint is None
        assert err.hints is None
        assert err.docs is None

    def test_with_hint_and_docs(self) -> None:
        err = ACLIError("bad", hint="try this", docs="readme.md")
        assert err.hint == "try this"
        assert err.docs == "readme.md"


class TestSpecificErrors:
    def test_invalid_args(self) -> None:
        err = InvalidArgsError("missing --pipeline")
        assert err.code == ExitCode.INVALID_ARGS

    def test_not_found(self) -> None:
        err = NotFoundError("resource gone", hint="check id")
        assert err.code == ExitCode.NOT_FOUND
        assert err.hint == "check id"

    def test_conflict(self) -> None:
        err = ConflictError("already exists")
        assert err.code == ExitCode.CONFLICT

    def test_precondition(self) -> None:
        err = PreconditionError("need setup first", docs=".cli/setup.md")
        assert err.code == ExitCode.PRECONDITION_FAILED
        assert err.docs == ".cli/setup.md"


class TestSuggestFlag:
    def test_close_match(self) -> None:
        assert suggest_flag("--pipline", ["--pipeline", "--env", "--dry-run"]) == "--pipeline"

    def test_no_match(self) -> None:
        assert suggest_flag("--zzzzz", ["--pipeline", "--env"]) is None

    def test_exact_match(self) -> None:
        assert suggest_flag("--env", ["--pipeline", "--env"]) == "--env"
