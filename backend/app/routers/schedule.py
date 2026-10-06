from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import recruiter_only
from ..db import get_db
from ..models import Candidate, Interview, User
from ..schemas import InterviewOut, ScheduleIn

router = APIRouter(tags=["schedule"])


@router.post("/candidates/{candidate_id}/interviews", response_model=InterviewOut, status_code=201,
             dependencies=[Depends(recruiter_only)])
def schedule(candidate_id: int, body: ScheduleIn, db: Session = Depends(get_db)):
    """Schedule stub: stores a slot + assigned interviewer. No calendar or email integration."""
    if not db.get(Candidate, candidate_id):
        raise HTTPException(404, "Candidate not found")
    interviewer = db.get(User, body.interviewer_id)
    if not interviewer or interviewer.role != "interviewer":
        raise HTTPException(422, "interviewer_id must be an interviewer user")
    iv = Interview(candidate_id=candidate_id, interviewer_id=interviewer.id, slot=body.slot)
    db.add(iv)
    db.commit()
    return iv
