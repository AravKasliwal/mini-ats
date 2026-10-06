"""Interview transcript/notes -> structured scorecard with verbatim quoted evidence."""
import json
import re

from . import llm

POSITIVE = {"built", "led", "designed", "shipped", "reduced", "improved", "increased", "owned", "debugged",
            "optimized", "implemented", "scaled", "delivered", "mentored", "launched"}
NEGATIVE = {"unsure", "don't know", "dont know", "no experience", "never", "struggled", "couldn't", "could not",
            "not sure", "vague"}


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip() for p in parts if len(p.strip()) > 15]


def fake_scorecard(transcript: str, criteria: list[dict]) -> list[dict]:
    sents = _sentences(transcript)
    out = []
    for c in criteria:
        kws = [k.lower() for k in c.get("keywords", [])] or [c["name"].lower()]
        quotes = [s for s in sents if any(k in s.lower() for k in kws)][:3]
        pos = sum(any(w in q.lower() for w in POSITIVE) for q in quotes)
        neg = sum(any(w in q.lower() for w in NEGATIVE) for q in quotes)
        rating = 0 if not quotes else max(1, min(5, 2 + pos - 2 * neg + (1 if len(quotes) > 1 else 0)))
        summary = (f"{len(quotes)} relevant statement(s); {pos} indicate concrete impact, {neg} indicate gaps."
                   if quotes else "Not discussed in the interview.")
        out.append({"criterion": c["name"], "rating": rating, "summary": summary, "quotes": quotes})
    return out


LLM_SYSTEM = """You turn interview notes/transcripts into a structured scorecard. For each rubric criterion give an
integer rating 0-5 (0 = not discussed), a one-sentence summary, and 1-3 quotes copied VERBATIM from the transcript
that support the rating. Never paraphrase inside quotes; never invent evidence.
Output JSON: {"results": [{"criterion": str, "rating": int, "summary": str, "quotes": [str]}]}"""


def llm_scorecard(transcript: str, criteria: list[dict]) -> list[dict]:
    rubric = [{"name": c["name"], "description": c["description"]} for c in criteria]
    data = llm.call_json(LLM_SYSTEM, f"CRITERIA:\n{json.dumps(rubric)}\n\nTRANSCRIPT:\n{transcript}")
    by_name = {r.get("criterion"): r for r in data.get("results", [])}
    out = []
    for c in criteria:
        r = by_name.get(c["name"], {})
        quotes = [q.strip() for q in r.get("quotes", []) if q.strip() and q.strip() in transcript]
        rating = max(0, min(5, int(r.get("rating", 0))))
        if not quotes:
            rating = min(rating, 1)
        out.append({"criterion": c["name"], "rating": rating,
                    "summary": str(r.get("summary", ""))[:400], "quotes": quotes})
    return out


def recommend(results: list[dict], criteria: list[dict]) -> tuple[float, str]:
    weights = {c["name"]: c["weight"] for c in criteria}
    tw = sum(weights.values()) or 1
    overall = round(sum(r["rating"] * weights.get(r["criterion"], 1) for r in results) / tw / 5 * 100, 1)
    rec = "strong_yes" if overall >= 80 else "yes" if overall >= 60 else "no" if overall >= 40 else "strong_no"
    return overall, rec


def build_scorecard(transcript: str, criteria: list[dict], mode: str | None = None):
    mode = mode or llm.scorer_mode()
    results = llm_scorecard(transcript, criteria) if mode == "llm" else fake_scorecard(transcript, criteria)
    overall, rec = recommend(results, criteria)
    return mode, results, overall, rec
