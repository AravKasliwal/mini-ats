"""Seed demo users + a demo job (rubric loaded from the eval fixtures). Idempotent."""
import json
import sys
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "backend"), "/app"]

from sqlalchemy import select  # noqa: E402

from app.auth import hash_password  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.models import Job, Rubric, User  # noqa: E402

FIXTURES = next(p for p in (Path(__file__).resolve().parents[1] / "backend/app/eval/fixtures",
                            Path("/app/app/eval/fixtures")) if p.exists())


def seed():
    if engine.url.get_backend_name() == "sqlite":  # dev/tests; Postgres uses `alembic upgrade head`
        Base.metadata.create_all(engine)
    with SessionLocal() as db:
        for email, name, role in [("recruiter@demo.com", "Riley Recruiter", "recruiter"),
                                  ("interviewer@demo.com", "Ivy Interviewer", "interviewer"),
                                  ("interviewer2@demo.com", "Sam Second", "interviewer")]:
            if not db.scalar(select(User).where(User.email == email)):
                db.add(User(email=email, name=name, role=role, password_hash=hash_password("demo1234")))
        if not db.scalar(select(Job)):
            spec = json.loads((FIXTURES / "job.json").read_text())
            db.add(Job(title=spec["title"], description=spec["description"], pass_threshold=spec["pass_threshold"],
                       rubric=[Rubric(**r) for r in spec["rubric"]]))
        db.commit()
    print("seeded: recruiter@demo.com / interviewer@demo.com / interviewer2@demo.com (password demo1234)")


if __name__ == "__main__":
    seed()
