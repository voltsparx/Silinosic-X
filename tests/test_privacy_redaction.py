from unittest.mock import patch

from core.foundation.privacy import redact_if_needed, redact_text_if_needed, set_sensitive_information_mode


def test_sensitive_fields_are_redacted_by_default():
    set_sensitive_information_mode(False)
    result = redact_if_needed(
        {
            "contacts": {"emails": ["analyst@example.com"], "phones": ["+15551234567"]},
            "raw_text": "private OCR text",
        }
    )
    assert result["contacts"]["emails"] == ["[REDACTED]"]
    assert result["contacts"]["phones"] == ["[REDACTED]"]
    assert result["raw_text"] == "[REDACTED]"


def test_sensitive_fields_remain_available_after_explicit_opt_in():
    set_sensitive_information_mode(True)
    result = redact_if_needed({"emails": ["analyst@example.com"]})
    assert result["emails"] == ["analyst@example.com"]
    set_sensitive_information_mode(None)


def test_configured_custom_sensitive_fields_and_supported_generic_shapes_are_redacted():
    set_sensitive_information_mode(False)
    with patch(
        "core.foundation.privacy.load_operator_config",
        return_value={"privacy": {"redact_fields": ["emails", "api_keys"], "redaction_mask": "[REDACTED]"}},
    ):
        result = redact_if_needed(
            {
                "api_keys": ["secret"],
                "shared_emails": {"analyst@example.com": {"count": 2}},
                "contacts": [{"entity_type": "email", "value": "analyst@example.com", "evidence": "seen in analyst@example.com"}],
            }
        )
    assert result["api_keys"] == ["[REDACTED]"]
    assert "analyst@example.com" not in str(result)


def test_free_form_text_is_redacted_by_default():
    set_sensitive_information_mode(False)
    assert "analyst@example.com" not in redact_text_if_needed("Contact analyst@example.com or +1 555 123 4567")
