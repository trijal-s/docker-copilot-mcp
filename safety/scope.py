"""
Scope whitelist — which containers this server is allowed to perform
destructive actions on.
"""

ALLOWED_RESTART_TARGETS = [
    "test-nginx",
    "test-redis",
]


def check_scope(target: str, allowed_targets: list) -> None:
    if target not in allowed_targets:
        from safety.gate import ScopeError
        raise ScopeError(
            f"'{target}' is not in the allowed scope. "
            f"This server is only permitted to act on: {', '.join(allowed_targets)}"
        )