"""Single explicit LLM call site. Every call is logged (model, tokens, latency)."""
import json
import logging
import os
import re
import time

log = logging.getLogger("mini_ats.llm")

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-5-5")


def scorer_mode() -> str:
    """'llm' when a key is configured (unless SCORER=fake), else the offline 'fake' scorer."""
    forced = os.getenv("SCORER", "").lower()
    if forced in ("fake", "llm"):
        return forced
    return "llm" if os.getenv("ANTHROPIC_API_KEY") else "fake"


def call_json(system: str, user: str, max_tokens: int = 8000) -> dict:
    import anthropic

    client = anthropic.Anthropic()
    start = time.time()
    resp = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system + "\nRespond with a single JSON object and nothing else.",
        messages=[{"role": "user", "content": user}],
    )
    log.info(
        "llm_call model=%s in=%s out=%s latency=%.1fs stop=%s",
        MODEL, resp.usage.input_tokens, resp.usage.output_tokens, time.time() - start, resp.stop_reason,
    )
    if resp.stop_reason == "refusal":
        raise RuntimeError("Model declined the request")
    text = "".join(b.text for b in resp.content if b.type == "text")
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    return json.loads(text)
