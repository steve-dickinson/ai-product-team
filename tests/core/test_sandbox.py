"""Tests for the sandbox (unit tests — Docker optional)."""

from __future__ import annotations

from src.core.sandbox import Sandbox, SandboxResult


def test_sandbox_initialises_with_defaults() -> None:
    sandbox = Sandbox()
    assert sandbox.timeout_seconds == 300
    assert sandbox.memory_limit == "2g"


def test_sandbox_result_fields() -> None:
    result = SandboxResult(exit_code=0, stdout="hello", stderr="")
    assert result.exit_code == 0
    assert not result.timed_out
