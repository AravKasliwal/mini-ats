"""Score fixture resumes and compare to hand-labelled gold.

  python -m app.eval.run_eval            # fake scorer if no ANTHROPIC_API_KEY, else LLM
  python -m app.eval.run_eval --mode fake|llm

Reports pass/fail accuracy, precision/recall (positive = pass), per-criterion MAE, and exact-score agreement.
Exits non-zero if accuracy falls below --min-accuracy (default 0), so it can gate CI.
"""
import argparse
import json
import sys
from pathlib import Path

from app.services import llm
from app.services.rubric_score import MAX_SCORE, aggregate, score_resume

FIX = Path(__file__).parent / "fixtures"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["fake", "llm"])
    ap.add_argument("--min-accuracy", type=float, default=0.0)
    args = ap.parse_args()
    mode = args.mode or llm.scorer_mode()

    job = json.loads((FIX / "job.json").read_text())
    gold = json.loads((FIX / "expected.json").read_text())["resumes"]
    criteria = [{"id": i + 1, "name": r["name"], "category": r["category"], "weight": r["weight"],
                 "description": r["description"], "keywords": r["keywords"]} for i, r in enumerate(job["rubric"])]
    thr = job["pass_threshold"]

    tp = fp = fn = tn = exact = n_crit = 0
    abs_err = [0.0] * len(criteria)
    print(f"scorer={mode}  threshold={thr}\n{'resume':26} {'gold':>14} {'pred':>14}  total(g/p)  verdict")
    for name, g in gold.items():
        _, res, total = score_resume((FIX / "resumes" / name).read_text(), criteria, job["title"], mode)
        pred = [r["score"] for r in res]
        g_total = aggregate([{"score": s, "weight": c["weight"]} for s, c in zip(g["scores"], criteria)])
        g_pass, p_pass = g_total >= thr, total >= thr
        tp += g_pass and p_pass; fp += (not g_pass) and p_pass
        fn += g_pass and not p_pass; tn += (not g_pass) and not p_pass
        for i, (a, b) in enumerate(zip(g["scores"], pred)):
            abs_err[i] += abs(a - b); exact += a == b; n_crit += 1
        print(f"{name:26} {str(g['scores']):>14} {str(pred):>14}  {g_total:5.1f}/{total:5.1f}  "
              f"{'ok' if g_pass == p_pass else 'MISS (' + ('false pass' if p_pass else 'false fail') + ')'}")

    n = len(gold)
    acc = (tp + tn) / n
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn) if tp + fn else float("nan")
    print(f"\npass/fail accuracy {acc:.0%} ({tp + tn}/{n})  precision {prec:.2f}  recall {rec:.2f}  "
          f"(tp={tp} fp={fp} fn={fn} tn={tn})")
    print(f"exact-score agreement {exact / n_crit:.0%}")
    for c, e in zip(criteria, abs_err):
        print(f"MAE {c['name']:22} {e / n:.2f} / {MAX_SCORE}")
    return 0 if acc >= args.min_accuracy else 1


if __name__ == "__main__":
    sys.exit(main())
