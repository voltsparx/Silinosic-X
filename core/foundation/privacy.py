"""Central, render-time sensitive-information controls."""

from __future__ import annotations

from contextvars import ContextVar
import re
from typing import Any, Mapping

from core.foundation.operator_config import load_operator_config


_SENSITIVE_MODE: ContextVar[bool | None] = ContextVar("silinosic_x_sensitive_mode", default=None)
_FIELD_ALIASES: dict[str, frozenset[str]] = {
    "email": frozenset({"email", "emails"}),
    "emails": frozenset({"email", "emails"}),
    "phone": frozenset({"phone", "phones"}),
    "phones": frozenset({"phone", "phones"}),
    "address": frozenset({"address", "addresses"}),
    "addresses": frozenset({"address", "addresses"}),
    "exact_geolocation": frozenset({"exact_geolocation", "geolocation", "gps", "latitude", "longitude"}),
    "geolocation": frozenset({"exact_geolocation", "geolocation", "gps", "latitude", "longitude"}),
    "credential_token": frozenset({"credential_token", "credential_tokens", "token", "tokens"}),
    "credential_tokens": frozenset({"credential_token", "credential_tokens", "token", "tokens"}),
    "api_key": frozenset({"api_key", "api_keys"}),
    "api_keys": frozenset({"api_key", "api_keys"}),
    "darkweb_identifier": frozenset({"darkweb_identifier", "darkweb_identifiers"}),
    "darkweb_identifiers": frozenset({"darkweb_identifier", "darkweb_identifiers"}),
    "wallet_address": frozenset({"wallet_address", "wallet_addresses"}),
    "wallet_addresses": frozenset({"wallet_address", "wallet_addresses"}),
    "raw_text": frozenset({"raw_text", "merged_text"}),
    "merged_text": frozenset({"raw_text", "merged_text"}),
}
_DEFAULT_REDACT_FIELDS = (
    "emails", "phones", "addresses", "exact_geolocation", "credential_tokens", "darkweb_identifiers", "wallet_addresses"
)
_SHARED_VALUE_FIELDS = frozenset({"shared_emails", "shared_phones", "shared_addresses", "shared_wallet_addresses"})
_EMAIL_RE = re.compile(r"(?<![\w.+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![\w.-])")
_PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{6,}\d)(?!\w)")
_TOKEN_RE = re.compile(r"\b(?:api[_ -]?key|access[_ -]?token|credential[_ -]?token)\s*[:=]\s*[^\s,;]+", re.IGNORECASE)


def _configured_redaction_keys() -> frozenset[str]:
    privacy = load_operator_config().get("privacy", {})
    configured = privacy.get("redact_fields") if isinstance(privacy, dict) else None
    fields = configured if isinstance(configured, list) else _DEFAULT_REDACT_FIELDS
    keys: set[str] = set()
    for field in fields:
        normalized = str(field or "").strip().lower()
        if normalized:
            keys.update(_FIELD_ALIASES.get(normalized, {normalized}))
    return frozenset(keys)


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


def redact_text_if_needed(
    text: object,
    *,
    sensitive_information: bool | None = None,
    mask: str | None = None,
) -> str:
    """Mask recognizable sensitive values embedded in free-form text."""

    value = str(text or "")
    if sensitive_information_enabled(sensitive_information):
        return value
    if mask is None:
        privacy = load_operator_config().get("privacy", {})
        mask = str(privacy.get("redaction_mask", "[REDACTED]")) if isinstance(privacy, dict) else "[REDACTED]"
    return _TOKEN_RE.sub(mask, _PHONE_RE.sub(mask, _EMAIL_RE.sub(mask, value)))


def redact_if_needed(
    data: Any,
    *,
    sensitive_information: bool | None = None,
    mask: str | None = None,
) -> Any:
    """Return a recursive copy with configured and embedded sensitive values masked."""

    if sensitive_information_enabled(sensitive_information):
        return data
    if mask is None:
        privacy = load_operator_config().get("privacy", {})
        mask = str(privacy.get("redaction_mask", "[REDACTED]")) if isinstance(privacy, dict) else "[REDACTED]"
    sensitive_keys = _configured_redaction_keys()

    def _redact_mapping_keys(value: Mapping[Any, Any]) -> dict[Any, Any]:
        return {
            (mask if index == 1 else f"{mask}:{index}"): _redact(child)
            for index, child in enumerate(value.values(), start=1)
        }

    def _row_declares_sensitive_value(value: Mapping[Any, Any]) -> bool:
        for kind_key in ("entity_type", "type", "kind", "field", "label"):
            if str(value.get(kind_key) or "").strip().lower() in sensitive_keys:
                return True
        return False

    def _redact(value: Any) -> Any:
        if isinstance(value, Mapping):
            output: dict[Any, Any] = {}
            row_sensitive = _row_declares_sensitive_value(value)
            for key, child in value.items():
                normalized_key = str(key).strip().lower()
                if normalized_key in sensitive_keys:
                    if isinstance(child, (list, tuple)):
                        output[key] = [mask for _ in child]
                    elif isinstance(child, Mapping):
                        output[key] = {nested_key: mask for nested_key in child}
                    elif child in (None, ""):
                        output[key] = child
                    else:
                        output[key] = mask
                elif normalized_key in _SHARED_VALUE_FIELDS and isinstance(child, Mapping):
                    output[key] = _redact_mapping_keys(child)
                elif row_sensitive and normalized_key in {"value", "evidence"}:
                    output[key] = mask if child not in (None, "") else child
                else:
                    output[key] = _redact(child)
            return output
        if isinstance(value, (list, tuple)):
            return [_redact(item) for item in value]
        if isinstance(value, str):
            return redact_text_if_needed(value, sensitive_information=False, mask=mask)
        return value

    return _redact(data)
