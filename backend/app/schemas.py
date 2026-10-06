from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserOut(ORM):
    id: int
    email: str
    name: str
    role: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class RubricIn(BaseModel):
    name: str
    category: str = Field("skills", pattern="^(skills|experience|education)$")
    weight: float = Field(1.0, gt=0)
    description: str = ""
    keywords: list[str] = []


class RubricOut(RubricIn, ORM):
    id: int


class JobIn(BaseModel):
    title: str
    description: str = ""
    pass_threshold: float = 60.0
    rubric: list[RubricIn] = []


class JobOut(ORM):
    id: int
    title: str
    description: str
    pass_threshold: float
    rubric: list[RubricOut]


class RunOut(ORM):
    id: int
    candidate_id: int
    scorer: str
    total: float
    passed: bool
    results: list[dict]
    created_at: datetime


class ScorecardOut(ORM):
    id: int
    interview_id: int
    scorer: str
    overall: float
    recommendation: str
    results: list[dict]
    created_at: datetime


class InterviewOut(ORM):
    id: int
    candidate_id: int
    interviewer_id: int
    slot: datetime
    status: str
    scorecards: list[ScorecardOut] = []


class CandidateOut(ORM):
    id: int
    job_id: int
    name: str
    filename: str
    created_at: datetime
    latest_total: float | None = None


class CandidateDetail(CandidateOut):
    resume_text: str
    runs: list[RunOut]
    interviews: list[InterviewOut]


class ScheduleIn(BaseModel):
    interviewer_id: int
    slot: datetime


class ScorecardIn(BaseModel):
    transcript: str = Field(min_length=20)
