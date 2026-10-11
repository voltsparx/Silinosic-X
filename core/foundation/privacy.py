"""Central, render-time sensitive-information controls."""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any, Mapping

from core.foundation.operator_config import load_operator_config


_SENSITIVE_MODE: ContextVar[bool | None] = ContextVar("silinosic_x_sensitive_mode", default=None)
_SENSITIVE_KEYS = frozenset(
    {
        "email",
        "emails",
        "phone",
        "phones",
        "address",
        "addresses",
        "exact_geolocation",
        "geolocation",
        "gps",
        "latitude",
        "longitude",
        "credential_token",
        "credential_tokens",
        "token",
        "tokens",
        "darkweb_identifier",
        "darkweb_identifiers",
        "raw_text",
        "merged_text",
    }
)


def sensitive_information_enabled(override: bool | None = None) -> bool:
    """Resolve the per-run opt-in, falling back to the safe config default."""

    if override is not None:
        return bool(override)
    runtime_value = _SENSITIVE_MODE.get()
    if runtime_value is not None:
        return runtime_value
    privacy = load_operator_config().get("privacy", {})
    return bool(privacy.get("sensitive_information", False)) if isinstance(privacy, dict) else False


def set_sensitive_information_mode(value: bool | None) -> None:
    """Set the current process/task rendering mode without changing config on disk."""

    _SENSITIVE_MODE.set(None if value is None else bool(value))


def redact_if_needed(
    data: Any,
    *,
    sensitive_information: bool | None = None,
    mask: str | None = None,
) -> Any:
    """Return a recursive copy with known sensitive values masked by default."""

    if sensitive_information_enabled(sensitive_information):
        return data
    if mask is None:
        privacy = load_operator_config().get("privacy", {})
        mask = str(privacy.get("redaction_mask", "[REDACTED]")) if isinstance(privacy, dict) else "[REDACTED]"

    def _redact(value: Any) -> Any:
        if isinstance(value, Mapping):
            output: dict[Any, Any] = {}
            for key, child in value.items():
                normalized_key = str(key).strip().lower()
                if normalized_key in _SENSITIVE_KEYS:
                    if isinstance(child, (list, tuple)):
                        output[key] = [mask for _ in child]
                    elif isinstance(child, Mapping):
                        output[key] = {nested_key: mask for nested_key in child}
                    elif child in (None, ""):
                        output[key] = child
                    else:
                        output[key] = mask
                else:
                    output[key] = _redact(child)
            return output
        if isinstance(value, (list, tuple)):
            return [_redact(item) for item in value]
        return value

    return _redact(data)
