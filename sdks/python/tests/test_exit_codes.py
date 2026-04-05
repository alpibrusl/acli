"""Tests for acli.exit_codes."""

import pytest

from acli.exit_codes import ExitCode


class TestExitCode:
    def test_standard_codes_values(self) -> None:
        assert ExitCode.SUCCESS == 0
        assert ExitCode.GENERAL_ERROR == 1
        assert ExitCode.INVALID_ARGS == 2
        assert ExitCode.NOT_FOUND == 3
        assert ExitCode.PERMISSION_DENIED == 4
        assert ExitCode.CONFLICT == 5
        assert ExitCode.TIMEOUT == 6
        assert ExitCode.UPSTREAM_ERROR == 7
        assert ExitCode.PRECONDITION_FAILED == 8
        assert ExitCode.DRY_RUN == 9

    def test_from_int_valid(self) -> None:
        assert ExitCode.from_int(0) is ExitCode.SUCCESS
        assert ExitCode.from_int(9) is ExitCode.DRY_RUN

    def test_from_int_tool_specific_range(self) -> None:
        with pytest.raises(ValueError, match="tool-specific range"):
            ExitCode.from_int(10)
        with pytest.raises(ValueError, match="tool-specific range"):
            ExitCode.from_int(63)

    def test_from_int_unknown(self) -> None:
        with pytest.raises(ValueError, match="Unknown exit code"):
            ExitCode.from_int(64)
        with pytest.raises(ValueError, match="Unknown exit code"):
            ExitCode.from_int(100)
