"""Subprocess environment policy, asserted rather than remembered.

Two operational constraints from the project brief are enforced here so no
variant invocation can violate them by omission:

1. OpenWiki telemetry is disabled in every subprocess.
2. Non-reproducible / private OpenWiki personal-mode connectors are never
   enabled. Only the git-repo connector is permitted.
"""

from __future__ import annotations

import os

#: Env vars that must be set in every variant subprocess.
TELEMETRY_OFF = {
    "OPENWIKI_TELEMETRY_DISABLED": "1",
    "DO_NOT_TRACK": "1",
}

#: Personal-mode connectors that are banned in benchmark runs: they pull
#: private data and are not reproducible.
BANNED_CONNECTORS = frozenset({"gmail", "notion", "x", "twitter", "web-search", "hackernews"})

#: The only connector permitted for variant 04.
ALLOWED_CONNECTORS = frozenset({"git-repo"})


class EnvPolicyError(RuntimeError):
    """Raised when a subprocess environment would violate the brief."""


def variant_env(base: dict[str, str] | None = None) -> dict[str, str]:
    """Return the environment for a variant subprocess, telemetry disabled.

    The caller must use this; `assert_telemetry_disabled` is then a
    tripwire, not the primary mechanism.
    """
    env = dict(os.environ if base is None else base)
    env.update(TELEMETRY_OFF)
    return env


def assert_telemetry_disabled(env: dict[str, str]) -> None:
    for key, want in TELEMETRY_OFF.items():
        got = env.get(key)
        if got != want:
            raise EnvPolicyError(
                f"{key}={got!r} in variant subprocess env; must be {want!r}. "
                "Build the env with harness.env.variant_env()."
            )


def assert_connectors_allowed(connectors: list[str]) -> None:
    banned = sorted({c for c in connectors if c.lower() in BANNED_CONNECTORS})
    if banned:
        raise EnvPolicyError(
            f"connectors {banned} are banned in benchmark runs "
            "(non-reproducible and/or private data). "
            f"Permitted: {sorted(ALLOWED_CONNECTORS)}."
        )
    unknown = sorted({c for c in connectors if c.lower() not in ALLOWED_CONNECTORS})
    if unknown:
        raise EnvPolicyError(
            f"connectors {unknown} are not on the allow-list {sorted(ALLOWED_CONNECTORS)}."
        )
