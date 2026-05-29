from aupoll.config import parse_config


def test_parse_config_requires_unique_question_ids():
    raw = {
        "questions": [
            {"id": "q1", "prompt": "One?", "scale": {"min": 1, "max": 5}},
            {"id": "q1", "prompt": "Two?", "scale": {"min": 1, "max": 5}},
        ]
    }

    try:
        parse_config(raw)
    except ValueError as exc:
        assert "unique" in str(exc)
    else:
        raise AssertionError("expected duplicate ids to fail")


def test_parse_config_defaults_poll_labels():
    config = parse_config({"questions": [{"id": "q1", "prompt": "One?", "scale": {"min": 1, "max": 5}}]})

    assert config.title == "AUpoll"
    assert config.submit_label == "Submit"
    assert config.questions[0].step == 1

