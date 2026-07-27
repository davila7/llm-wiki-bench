"""Operational constraints must be enforced by code, not by memory."""

from __future__ import annotations

import pytest

from harness.env import (
    EnvPolicyError,
    assert_connectors_allowed,
    assert_telemetry_disabled,
    variant_env,
)


def test_variant_env_disables_telemetry() -> None:
    env = variant_env({"PATH": "/usr/bin"})
    assert env["OPENWIKI_TELEMETRY_DISABLED"] == "1"
    assert env["DO_NOT_TRACK"] == "1"
    assert_telemetry_disabled(env)


def test_variant_env_overrides_a_hostile_base() -> None:
    env = variant_env({"OPENWIKI_TELEMETRY_DISABLED": "0", "DO_NOT_TRACK": "0"})
    assert_telemetry_disabled(env)


def test_bare_env_is_rejected() -> None:
    with pytest.raises(EnvPolicyError, match="OPENWIKI_TELEMETRY_DISABLED"):
        assert_telemetry_disabled({"PATH": "/usr/bin"})


def test_git_repo_connector_is_allowed() -> None:
    assert_connectors_allowed(["git-repo"])


@pytest.mark.parametrize("connector", ["gmail", "notion", "x", "web-search", "hackernews"])
def test_private_connectors_are_banned(connector: str) -> None:
    with pytest.raises(EnvPolicyError, match="banned"):
        assert_connectors_allowed([connector])


def test_unknown_connector_is_rejected_not_ignored() -> None:
    with pytest.raises(EnvPolicyError, match="allow-list"):
        assert_connectors_allowed(["slack"])
