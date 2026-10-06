"""Rubric scoring: per-criterion 0-5 score + rationale + verbatim resume evidence.

Two scorers share one output shape:
  fake - deterministic keyword matching (CI, offline eval)
  llm  - Claude; evidence quotes are verified to be verbatim resume lines
"""
import json
import re

from . import llm

MAX_SCORE = 5


def _lines(text: str) -> list[str]:
    return [l.strip() for l in text.splitlines() if l.strip()]


def fake_score(resume: str, criteria: list[dict]) -> list[dict]:
    lines = _lines(resume)
    out = []
    for c in criteria:
        kws = [k.lower() for k in c.get("keywords", []) if k.strip()]
        hit_kws, evidence, listed_only = set(), [], True
        for line in lines:
            low = line.lower()
            found = {k for k in kws if re.search(r"(?<![a-z0-9])" + re.escape(k) + r"(?![a-z0-9])", low)}
            if found:
                hit_kws |= found
                # A line that is mostly bare keywords ("Skills: python sql docker ...") lists, not demonstrates.
                if not (len(found) >= 4 and len(line.split()) <= 2 * len(found) + 3):
                    listed_only = False
                if len(evidence) < 3:
                    evidence.append(line)
        need = max(1, (len(kws) + 1) // 2)
        score = round(MAX_SCORE * min(1.0, len(hit_kws) / need)) if kws else 0
        if listed_only and score > 3:
            score = 3
        rationale = (
            f"Matched {len(hit_kws)}/{len(kws)} keywords ({', '.join(sorted(hit_kws))})."
            if hit_kws else "No rubric keywords found in resume."
        )
        out.append({"criterion_id": c["id"], "name": c["name"], "weight": c["weight"],
                    "score": score, "rationale": rationale, "evidence": evidence})
    return out


LLM_SYSTEM = """You are a structured resume screener. Score a resume against each rubric criterion on an integer 0-5 scale
(0 = no evidence, 3 = partial/adequate, 5 = strong, clearly demonstrated). Base scores ONLY on the resume text.
For every criterion give a one-sentence rationale and 1-3 evidence quotes copied VERBATIM, character for character,
from single resume lines. If there is no evidence use an empty list and score 0.
Output JSON: {"results": [{"criterion_id": int, "score": int, "rationale": str, "evidence": [str]}]}"""


def llm_score(resume: str, criteria: list[dict], job_title: str) -> list[dict]:
    payload = {"job_title": job_title,
               "criteria": [{k: c[k] for k in ("id", "name", "category", "description")} for c in criteria]}
    data = llm.call_json(LLM_SYSTEM, f"RUBRIC:\n{json.dumps(payload)}\n\nRESUME:\n{resume}")
    by_id = {r["criterion_id"]: r for r in data.get("results", [])}
    lines = _lines(resume)
    out = []
    for c in criteria:
        r = by_id.get(c["id"], {})
        # Keep only quotes that really appear in the resume; no invented evidence.
        evidence = [q.strip() for q in r.get("evidence", []) if any(q.strip() in l for l in lines)]
        score = max(0, min(MAX_SCORE, int(r.get("score", 0))))
        if not evidence and score > 0 and r.get("evidence"):
            score = min(score, 2)  # claimed evidence didn't verify
        out.append({"criterion_id": c["id"], "name": c["name"], "weight": c["weight"], "score": score,
                    "rationale": str(r.get("rationale", "No rationale returned."))[:500], "evidence": evidence})
    return out


def aggregate(results: list[dict]) -> float:
    """Weighted average of 0-5 scores, scaled to 0-100."""
    total_w = sum(r["weight"] for r in results) or 1
    return round(sum(r["score"] * r["weight"] for r in results) / total_w / MAX_SCORE * 100, 1)


def score_resume(resume: str, criteria: list[dict], job_title: str, mode: str | None = None):
    mode = mode or llm.scorer_mode()
    results = llm_score(resume, criteria, job_title) if mode == "llm" else fake_score(resume, criteria)
    return mode, results, aggregate(results)
