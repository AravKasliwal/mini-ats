import subprocess
import sys


def test_fake_scorer_eval_does_not_regress():
    # Baseline is 87.5% on the 8 fixtures; fail CI if the offline scorer gets worse.
    r = subprocess.run([sys.executable, "-m", "app.eval.run_eval", "--mode", "fake", "--min-accuracy", "0.87"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout
