"""
Tests for the safety gate — the most important module in this project.
Run with: pytest tests/test_safety_gate.py -v
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from safety import gate


def test_dry_run_returns_token_without_executing():
    result = gate.request_confirmation(
        "restart_container", "test-nginx", {}, "Restart test-nginx"
    )
    assert result["status"] == "confirmation_required"
    assert "confirmation_token" in result
    assert len(result["confirmation_token"]) > 0


def test_valid_confirmation_passes():
    result = gate.request_confirmation(
        "restart_container", "test-nginx", {}, "Restart test-nginx"
    )
    token = result["confirmation_token"]
    # Should not raise
    gate.validate_confirmation("restart_container", "test-nginx", {}, token)


def test_token_is_single_use():
    result = gate.request_confirmation(
        "restart_container", "test-nginx", {}, "Restart test-nginx"
    )
    token = result["confirmation_token"]
    gate.validate_confirmation("restart_container", "test-nginx", {}, token)

    # Second use of the same token must fail
    with pytest.raises(ValueError, match="Invalid or already-used"):
        gate.validate_confirmation("restart_container", "test-nginx", {}, token)


def test_token_rejected_for_different_target():
    result = gate.request_confirmation(
        "restart_container", "test-nginx", {}, "Restart test-nginx"
    )
    token = result["confirmation_token"]

    # Trying to use a nginx-confirmed token to restart redis must fail
    with pytest.raises(ValueError, match="does not match"):
        gate.validate_confirmation("restart_container", "test-redis", {}, token)


def test_token_rejected_for_different_tool():
    result = gate.request_confirmation(
        "restart_container", "test-nginx", {}, "Restart test-nginx"
    )
    token = result["confirmation_token"]

    with pytest.raises(ValueError, match="does not match"):
        gate.validate_confirmation("delete_container", "test-nginx", {}, token)


def test_expired_token_is_rejected(monkeypatch):
    # Force a very short TTL for this test
    monkeypatch.setattr(gate, "TOKEN_TTL_SECONDS", 0)

    result = gate.request_confirmation(
        "restart_container", "test-nginx", {}, "Restart test-nginx"
    )
    token = result["confirmation_token"]

    time.sleep(0.1)  # ensure we're past expiry

    with pytest.raises(ValueError, match="expired"):
        gate.validate_confirmation("restart_container", "test-nginx", {}, token)


def test_check_scope_allows_whitelisted_target():
    # Should not raise
    gate.check_scope("test-nginx", ["test-nginx", "test-redis"])


def test_check_scope_blocks_non_whitelisted_target():
    with pytest.raises(gate.ScopeError, match="not in the allowed scope"):
        gate.check_scope("some-other-container", ["test-nginx", "test-redis"])


def test_invalid_confirmation_token_is_rejected():
    with pytest.raises(ValueError, match="Invalid or already-used"):
        gate.validate_confirmation(
            "restart_container", "test-nginx", {}, "not-a-real-token"
        )