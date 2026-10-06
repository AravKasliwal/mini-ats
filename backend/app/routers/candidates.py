from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user, recruiter_only
from ..db import get_db
from ..models import Candidate, Interview, Job, Run, User
from ..schemas import CandidateDetail, CandidateOut, RunOut
from ..services.parse_resume import extract_text, guess_name
from ..services.rubric_score import score_resume

MAX_UPLOAD = 5 * 1024 * 1024
router = APIRouter(prefix="/candidates", tags=["candidates"])


def visible_candidate(db: Session, user: User, candidate_id: int) -> Candidate:
    """RBAC: recruiters see all candidates, interviewers only those they are assigned to."""
    cand = db.get(Candidate, candidate_id)
    if cand and user.role != "recruiter" and not any(i.interviewer_id == user.id for i in cand.interviews):
        cand = None
    if not cand:
        raise HTTPException(404, "Candidate not found")
    return cand


def _out(c: Candidate) -> dict:
    return {"id": c.id, "job_id": c.job_id, "name": c.name, "filename": c.filename,
            "created_at": c.created_at, "latest_total": c.runs[0].total if c.runs else None}


@router.get("", response_model=list[CandidateOut])
def list_candidates(job_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(current_user)):
    q = select(Candidate).order_by(Candidate.id.desc())
    if job_id:
        q = q.where(Candidate.job_id == job_id)
    if user.role != "recruiter":
        q = q.join(Interview).where(Interview.interviewer_id == user.id).distinct()
    return [_out(c) for c in db.scalars(q)]


@router.post("", response_model=CandidateOut, status_code=201, dependencies=[Depends(recruiter_only)])
async def upload(job_id: int = Form(...), name: str = Form(""), file: UploadFile = File(...),
                 db: Session = Depends(get_db)):
    if not db.get(Job, job_id):
        raise HTTPException(404, "Job not found")
    data = await file.read()
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, "Resume too large (max 5 MB)")
    text = extract_text(file.filename or "", data)
    if not text:
        raise HTTPException(422, "Could not extract any text from the file")
    fallback = (file.filename or "Candidate").rsplit(".", 1)[0]
    cand = Candidate(job_id=job_id, name=name or guess_name(text, fallback), resume_text=text,
                     filename=file.filename or "")
    db.add(cand)
    db.commit()
    return _out(cand)


@router.get("/{candidate_id}", response_model=CandidateDetail)
def detail(candidate_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    c = visible_candidate(db, user, candidate_id)
    interviews = c.interviews if user.role == "recruiter" else [i for i in c.interviews if i.interviewer_id == user.id]
    return {**_out(c), "resume_text": c.resume_text, "runs": c.runs, "interviews": interviews}


@router.post("/{candidate_id}/score", response_model=RunOut, status_code=201, dependencies=[Depends(recruiter_only)])
def score(candidate_id: int, mode: str | None = None, db: Session = Depends(get_db)):
    c = db.get(Candidate, candidate_id)
    if not c:
        raise HTTPException(404, "Candidate not found")
    job = db.get(Job, c.job_id)
    if not job.rubric:
        raise HTTPException(422, "Job has no rubric criteria")
    criteria = [{"id": r.id, "name": r.name, "category": r.category, "weight": r.weight,
                 "description": r.description, "keywords": r.keywords} for r in job.rubric]
    try:
        used, results, total = score_resume(c.resume_text, criteria, job.title, mode)
    except Exception as e:  # LLM failure shouldn't 500 opaquely
        raise HTTPException(502, f"Scoring failed: {e}") from e
    run = Run(candidate_id=c.id, scorer=used, total=total, passed=int(total >= job.pass_threshold), results=results)
    db.add(run)
    db.commit()
    return run
