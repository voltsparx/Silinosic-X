from filters.noise_suppression_filter import run


def test_noise_filter_uses_first_nonempty_ocr_text_field():
    result = run(
        {
            "results": [],
            "domain_result": {},
            "previous_plugin_data": {
                "ocr": {"text": None, "merged_text": "noise", "avg_confidence": 0.1}
            },
        }
    )
    assert result["data"]["suppressed_ocr_artifacts"] == ["previous_plugin_data.ocr"]
