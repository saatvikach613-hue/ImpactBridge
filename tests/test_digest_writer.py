"""The Monday digest must always go out, LLM or not, and must never invent facts."""

import app.automation.digest_writer as dw
from app.automation.digest_writer import format_fallback, _build_prompt, write_digest

KIDS = [
    {"name": "Arjun K",  "english_level": "word",   "math_level": "basic_operations", "risk_reason": "2 consecutive struggling sessions"},
    {"name": "Meera S",  "english_level": "letter", "math_level": "pre_number",        "risk_reason": "attendance below 60%"},
    {"name": "Ravi T",   "english_level": "word",   "math_level": "basic_operations", "risk_reason": "2 consecutive struggling sessions"},
]


def test_fallback_lists_every_kid_with_reason():
    text = format_fallback(KIDS)
    for k in KIDS:
        assert k["name"] in text
        assert k["risk_reason"] in text
    assert text.count("\n") == len(KIDS) - 1


def test_prompt_contains_facts_and_guardrails():
    p = _build_prompt("Madhavadhara", KIDS)
    assert "Madhavadhara" in p
    for k in KIDS:
        assert k["name"] in p
    # guardrails the reviewer will care about
    assert "Do not invent" in p
    assert "medical advice" in p
    assert "Only use the facts above" in p


def test_prompt_caps_kid_count():
    many = [dict(KIDS[0], name=f"Kid {i}") for i in range(40)]
    p = _build_prompt("X", many)
    assert "Kid 24" in p and "Kid 25" not in p
    assert "+15 more kids" in p


def test_write_digest_without_api_key_uses_fallback(monkeypatch):
    monkeypatch.setattr(dw, "ANTHROPIC_API_KEY", "")
    text, source = write_digest("X", KIDS)
    assert source == "fallback"
    assert text == format_fallback(KIDS)


def test_write_digest_with_empty_list_is_safe(monkeypatch):
    monkeypatch.setattr(dw, "ANTHROPIC_API_KEY", "fake-key")
    text, source = write_digest("X", [])
    assert source == "fallback"
    assert text == ""


def test_write_digest_llm_failure_falls_back(monkeypatch):
    """If the API errors for any reason, the email still goes out with the plain list."""
    monkeypatch.setattr(dw, "ANTHROPIC_API_KEY", "fake-key")

    class Boom:
        def __init__(self, *a, **k): pass
        class messages:
            @staticmethod
            def create(**kwargs): raise RuntimeError("network down")

    import sys, types
    fake = types.ModuleType("anthropic"); fake.Anthropic = Boom
    monkeypatch.setitem(sys.modules, "anthropic", fake)

    text, source = write_digest("X", KIDS)
    assert source == "fallback"
    assert "Arjun K" in text


def test_write_digest_rejects_output_missing_a_kid(monkeypatch):
    """Guardrail: if the model drops a kid, we don't trust the summary."""
    monkeypatch.setattr(dw, "ANTHROPIC_API_KEY", "fake-key")

    class Block:  text = "Arjun and Ravi both struggled two sessions running; please check on them first. " * 2
    class Msg:    content = [Block()]
    class Fake:
        def __init__(self, *a, **k): pass
        class messages:
            @staticmethod
            def create(**kwargs): return Msg()

    import sys, types
    fake = types.ModuleType("anthropic"); fake.Anthropic = Fake
    monkeypatch.setitem(sys.modules, "anthropic", fake)

    text, source = write_digest("X", KIDS)   # Meera is missing from the model output
    assert source == "fallback"


def test_write_digest_accepts_good_output(monkeypatch):
    monkeypatch.setattr(dw, "ANTHROPIC_API_KEY", "fake-key")

    class Block:  text = ("Arjun and Ravi both had two struggling sessions in a row, while Meera's attendance "
                          "has dropped below 60%. Start with Arjun and Ravi this week, then check in with Meera.")
    class Msg:    content = [Block()]
    class Fake:
        def __init__(self, *a, **k): pass
        class messages:
            @staticmethod
            def create(**kwargs): return Msg()

    import sys, types
    fake = types.ModuleType("anthropic"); fake.Anthropic = Fake
    monkeypatch.setitem(sys.modules, "anthropic", fake)

    text, source = write_digest("X", KIDS)
    assert source == "llm"
    assert "Meera" in text
