import hashlib
import time

_pending_confirmations: dict[str, tuple[str, float]] = {}
TOKEN_TTL_SECONDS = 120


class ScopeError(Exception):
    pass


class ConfirmationRequired(Exception):
    pass


def _action_signature(tool_name: str, target: str, params: dict) -> str:
    param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    return f"{tool_name}:{target}:{param_str}"


def _generate_token(signature: str) -> str:
    raw = f"{signature}:{time.time()}"
    token = hashlib.sha256(raw.encode()).hexdigest()[:16]
    _pending_confirmations[token] = (signature, time.time() + TOKEN_TTL_SECONDS)
    return token


def check_scope(target: str, allowed_targets: list) -> None:
    if target not in allowed_targets:
        raise ScopeError(
            f"'{target}' is not in the allowed scope. "
            f"This server is only permitted to act on: {', '.join(allowed_targets)}"
        )


def request_confirmation(tool_name: str, target: str, params: dict, plan_description: str) -> dict:
    signature = _action_signature(tool_name, target, params)
    token = _generate_token(signature)
    return {
        "status": "confirmation_required",
        "plan": plan_description,
        "confirmation_token": token,
        "expires_in_seconds": TOKEN_TTL_SECONDS,
        "instructions": (
            "This is a destructive action. Show this plan to the user. "
            "If they approve, call this tool again with the same arguments "
            "plus confirmation_token set to the value above."
        ),
    }


def validate_confirmation(tool_name: str, target: str, params: dict, confirmation_token: str) -> None:
    entry = _pending_confirmations.get(confirmation_token)
    if entry is None:
        raise ValueError("Invalid or already-used confirmation token.")

    signature, expires_at = entry
    expected_signature = _action_signature(tool_name, target, params)

    if time.time() > expires_at:
        del _pending_confirmations[confirmation_token]
        raise ValueError("Confirmation token expired. Please request confirmation again.")

    if signature != expected_signature:
        raise ValueError(
            "Confirmation token does not match this action "
            "(target or parameters changed since confirmation was requested)."
        )

    del _pending_confirmations[confirmation_token]