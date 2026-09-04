"""
Digest writer
=============
Turns the Monday at-risk list into a short, plain-English briefing a
coordinator can read in 20 seconds on their phone.

Design rules (this is an ops tool, not a chatbot):
- The model only REPHRASES facts the ML pipeline already produced
  (kid name, levels, risk reason). It is told not to add advice or diagnoses.
- Deterministic fallback: if there's no API key, the call fails, or the
  output looks wrong, we send the plain bullet list. The email always goes out.
- Cost-capped: Haiku, ~300 output tokens, one call per chapter per week.

`format_fallback()` and `_build_prompt()` are pure, so they're unit-tested.
"""

from app.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

MAX_KIDS_IN_PROMPT = 25


def format_fallback(at_risk_kids: list) -> str:
    """Plain bullet list. Always available."""
    return "\n".join(
        f"  - {k['name']} | English: {k['english_level']} | Math: {k['math_level']} | Reason: {k['risk_reason']}"
        for k in at_risk_kids
    )


def _build_prompt(chapter_name: str, at_risk_kids: list) -> str:
    rows = "\n".join(
        f"- {k['name']}: English {k['english_level']}, Math {k['math_level']}. Flagged because: {k['risk_reason']}"
        for k in at_risk_kids[:MAX_KIDS_IN_PROMPT]
    )
    extra = len(at_risk_kids) - MAX_KIDS_IN_PROMPT
    if extra > 0:
        rows += f"\n- (+{extra} more kids, listed in the dashboard)"

    return f"""You are writing a short Monday-morning briefing for a volunteer coordinator at an education NGO chapter called {chapter_name}.

Below is the list of kids an ML model flagged as at-risk this week, with the reason it gave.

{rows}

Write the briefing in plain English, 4 to 7 sentences, no bullet points, no headings.
Rules:
- Group kids who share the same reason together so the coordinator sees patterns (e.g. "three kids missed two sessions in a row").
- Mention every kid by name at least once.
- Only use the facts above. Do not invent causes, do not give teaching or medical advice, do not speculate about home life.
- End with one sentence saying which kids to check on first, based only on the reasons given.
- Warm but efficient tone. No emojis.
"""


def write_digest(chapter_name: str, at_risk_kids: list) -> tuple[str, str]:
    """
    Returns (text, source) where source is "llm" or "fallback".
    Never raises.
    """
    fallback = format_fallback(at_risk_kids)
    if not at_risk_kids or not ANTHROPIC_API_KEY:
        return fallback, "fallback"

    try:
        import anthropic  # imported lazily so the app runs without the package/key
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=350,
            temperature=0.2,
            messages=[{"role": "user", "content": _build_prompt(chapter_name, at_risk_kids)}],
        )
        text = "".join(getattr(block, "text", "") for block in msg.content).strip()

        # Sanity checks: non-trivial, and every kid actually mentioned.
        if len(text) < 60:
            return fallback, "fallback"
        missing = [k["name"] for k in at_risk_kids[:MAX_KIDS_IN_PROMPT] if k["name"].split()[0] not in text]
        if missing:
            return fallback, "fallback"
        return text, "llm"
    except Exception as e:  # network, auth, rate limit, anything
        print(f"[digest_writer] LLM summary unavailable, using fallback: {e}")
        return fallback, "fallback"
