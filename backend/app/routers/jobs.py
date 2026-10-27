import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user, recruiter_only
from ..db import get_db
from ..models import Candidate, Job, Rubric
from ..schemas import JobIn, JobOut

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _get(db: Session, job_id: int) -> Job:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.get("", response_model=list[JobOut], dependencies=[Depends(current_user)])
def list_jobs(db: Session = Depends(get_db)):
    return db.scalars(select(Job).order_by(Job.id)).all()


@router.post("", response_model=JobOut, status_code=201, dependencies=[Depends(recruiter_only)])
def create_job(body: JobIn, db: Session = Depends(get_db)):
    job = Job(title=body.title, description=body.description, pass_threshold=body.pass_threshold,
              rubric=[Rubric(**r.model_dump()) for r in body.rubric])
    db.add(job)
    db.commit()
    return job


@router.get("/{job_id}", response_model=JobOut, dependencies=[Depends(current_user)])
def get_job(job_id: int, db: Session = Depends(get_db)):
    return _get(db, job_id)


@router.put("/{job_id}", response_model=JobOut, dependencies=[Depends(recruiter_only)])
def update_job(job_id: int, body: JobIn, db: Session = Depends(get_db)):
    job = _get(db, job_id)
    job.title, job.description, job.pass_threshold = body.title, body.description, body.pass_threshold
    job.rubric = [Rubric(**r.model_dump()) for r in body.rubric]
    db.commit()
    return job


@router.delete("/{job_id}", status_code=204, dependencies=[Depends(recruiter_only)])
def delete_job(job_id: int, db: Session = Depends(get_db)):
    db.delete(_get(db, job_id))
    db.commit()


def _csv_safe(v) -> str:
    """Neutralise spreadsheet formula injection from user-supplied text (names come from resumes)."""
    v = "" if v is None else str(v)
    return "'" + v if v[:1] in ("=", "+", "-", "@", "\t", "\r") else v


@router.get("/{job_id}/export.csv", dependencies=[Depends(recruiter_only)])
def export_csv(job_id: int, db: Session = Depends(get_db)):
    """Candidates for a job ranked by latest score, with per-criterion scores."""
    job = _get(db, job_id)
    cands = db.scalars(select(Candidate).where(Candidate.job_id == job_id)).all()
    cands.sort(key=lambda c: c.runs[0].total if c.runs else -1, reverse=True)
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["rank", "name", "stage", "total", "passed", "scorer"] + [r.name for r in job.rubric])
    for i, c in enumerate(cands, 1):
        run = c.runs[0] if c.runs else None
        by_id = {r["criterion_id"]: r["score"] for r in run.results} if run else {}
        w.writerow([i, _csv_safe(c.name), c.stage, run.total if run else "", ("yes" if run.passed else "no") if run else "",
                    run.scorer if run else ""] + [by_id.get(r.id, "") for r in job.rubric])
    return Response(out.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="job-{job_id}-candidates.csv"'})
