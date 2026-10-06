import os
import sys
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SCORER"] = "fake"
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
Path("test.db").unlink(missing_ok=True)

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from seed import seed  # noqa: E402

seed()
client = TestClient(app)

RESUME = b"""Jane Doe
B.S. Computer Science, State University
Built REST APIs in Python (FastAPI) backed by Postgres; shipped to production for 50k users.
Led migration to Docker, reduced p95 latency by 40%.
"""


def login(email):
    r = client.post("/api/auth/login", data={"username": email, "password": "demo1234"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_full_flow_and_rbac():
    rec, iv1, iv2 = login("recruiter@demo.com"), login("interviewer@demo.com"), login("interviewer2@demo.com")
    assert client.post("/api/auth/login", data={"username": "recruiter@demo.com", "password": "x"}).status_code == 401
    assert client.get("/api/jobs").status_code == 401

    job = client.get("/api/jobs", headers=rec).json()[0]
    assert len(job["rubric"]) == 3
    assert client.post("/api/jobs", headers=iv1, json={"title": "x"}).status_code == 403

    cand = client.post("/api/candidates", headers=rec, data={"job_id": job["id"]},
                       files={"file": ("jane.txt", RESUME)}).json()
    assert cand["name"] == "Jane Doe"

    run = client.post(f"/api/candidates/{cand['id']}/score", headers=rec).json()
    assert run["scorer"] == "fake" and run["passed"] and run["total"] >= 60
    for r in run["results"]:
        assert all(q in RESUME.decode() for q in r["evidence"])  # evidence is verbatim resume lines

    # interviewer can't see the candidate until assigned
    assert client.get(f"/api/candidates/{cand['id']}", headers=iv1).status_code == 404
    assert client.get("/api/candidates", headers=iv1).json() == []
    me = client.get("/api/auth/me", headers=iv1).json()
    r = client.post(f"/api/candidates/{cand['id']}/interviews", headers=rec,
                    json={"interviewer_id": me["id"], "slot": "2026-10-20T15:00:00Z"})
    assert r.status_code == 201
    assert client.get(f"/api/candidates/{cand['id']}", headers=iv1).status_code == 200
    assert [c["id"] for c in client.get("/api/candidates", headers=iv1).json()] == [cand["id"]]
    assert client.get(f"/api/candidates/{cand['id']}", headers=iv2).status_code == 404
    assert client.post(f"/api/candidates/{cand['id']}/score", headers=iv1).status_code == 403


NOTES = ("Candidate explained how she built REST APIs in Python and shipped them to production. "
         "She said she led a Docker migration and reduced latency by 40 percent. "
         "On education she was unsure about distributed systems theory.")


def test_scorecard_quotes_are_verbatim_and_scoped():
    rec, iv1, iv2 = login("recruiter@demo.com"), login("interviewer@demo.com"), login("interviewer2@demo.com")
    job = client.get("/api/jobs", headers=rec).json()[0]
    cand = client.post("/api/candidates", headers=rec, data={"job_id": job["id"]},
                       files={"file": ("sc.txt", RESUME)}).json()
    me = client.get("/api/auth/me", headers=iv1).json()
    iv_id = client.post(f"/api/candidates/{cand['id']}/interviews", headers=rec,
                        json={"interviewer_id": me["id"], "slot": "2026-10-21T15:00:00Z"}).json()["id"]
    assert client.post(f"/api/interviews/{iv_id}/scorecards", headers=iv2, json={"transcript": NOTES}).status_code == 404
    r = client.post(f"/api/interviews/{iv_id}/scorecards", headers=iv1, json={"transcript": NOTES})
    assert r.status_code == 201, r.text
    sc = r.json()
    assert sc["results"] and any(x["quotes"] for x in sc["results"])
    assert all(q in NOTES for x in sc["results"] for q in x["quotes"])
    iv = client.get(f"/api/candidates/{cand['id']}", headers=iv1).json()["interviews"][0]
    assert iv["status"] == "completed" and len(iv["scorecards"]) == 1


def test_upload_size_cap_and_cors():
    rec = login("recruiter@demo.com")
    big = b"x" * (5 * 1024 * 1024 + 1)
    r = client.post("/api/candidates", headers=rec, data={"job_id": 1}, files={"file": ("big.txt", big)})
    assert r.status_code == 413
    pre = client.options("/api/jobs", headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" not in pre.headers
