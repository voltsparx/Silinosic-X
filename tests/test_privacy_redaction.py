from core.foundation.privacy import redact_if_needed, set_sensitive_information_mode


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
