from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import get_db
from ..models import Candidate, Interview, Job, Scorecard, User
from ..schemas import ScorecardIn, ScorecardOut
from ..services.scorecard import build_scorecard

router = APIRouter(tags=["scorecards"])


@router.post("/interviews/{interview_id}/scorecards", response_model=ScorecardOut, status_code=201)
def create_scorecard(interview_id: int, body: ScorecardIn, mode: str | None = None,
                     db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Notes/transcript -> structured scorecard. Recruiters: any interview. Interviewers: their own only."""
    iv = db.get(Interview, interview_id)
    if iv and user.role != "recruiter" and iv.interviewer_id != user.id:
        iv = None
    if not iv:
        raise HTTPException(404, "Interview not found")
    job = db.get(Job, db.get(Candidate, iv.candidate_id).job_id)
    criteria = [{"id": r.id, "name": r.name, "weight": r.weight, "description": r.description,
                 "keywords": r.keywords} for r in job.rubric]
    if not criteria:
        raise HTTPException(422, "Job has no rubric criteria")
    try:
        used, results, overall, rec = build_scorecard(body.transcript, criteria, mode)
    except Exception as e:
        raise HTTPException(502, f"Scorecard generation failed: {e}") from e
    sc = Scorecard(interview_id=iv.id, scorer=used, transcript=body.transcript, overall=overall,
                   recommendation=rec, results=results)
    iv.status = "completed"
    db.add(sc)
    db.commit()
    return sc
