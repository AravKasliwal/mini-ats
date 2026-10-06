from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))  # recruiter | interviewer


class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    pass_threshold: Mapped[float] = mapped_column(Float, default=60.0)
    rubric: Mapped[list["Rubric"]] = relationship(
        back_populates="job", cascade="all, delete-orphan", order_by="Rubric.id"
    )


class Rubric(Base):
    """One weighted criterion of a job's rubric."""

    __tablename__ = "rubrics"
    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(50), default="skills")  # skills|experience|education
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    description: Mapped[str] = mapped_column(Text, default="")
    keywords: Mapped[list] = mapped_column(JSON, default=list)  # used by the offline scorer
    job: Mapped[Job] = relationship(back_populates="rubric")


class Candidate(Base):
    __tablename__ = "candidates"
    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    name: Mapped[str] = mapped_column(String(255))
    resume_text: Mapped[str] = mapped_column(Text)
    filename: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    runs: Mapped[list["Run"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan", order_by="Run.id.desc()"
    )
    interviews: Mapped[list["Interview"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )


class Run(Base):
    """One scoring run of a candidate against the job rubric."""

    __tablename__ = "runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"))
    scorer: Mapped[str] = mapped_column(String(50))
    total: Mapped[float] = mapped_column(Float)
    passed: Mapped[int] = mapped_column(Integer)
    results: Mapped[list] = mapped_column(JSON)  # [{criterion_id, name, weight, score, rationale, evidence}]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    candidate: Mapped[Candidate] = relationship(back_populates="runs")


class Interview(Base):
    __tablename__ = "interviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"))
    interviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    slot: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    candidate: Mapped[Candidate] = relationship(back_populates="interviews")
    scorecards: Mapped[list["Scorecard"]] = relationship(
        back_populates="interview", cascade="all, delete-orphan", order_by="Scorecard.id.desc()"
    )


class Scorecard(Base):
    __tablename__ = "scorecards"
    id: Mapped[int] = mapped_column(primary_key=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id"))
    scorer: Mapped[str] = mapped_column(String(50))
    transcript: Mapped[str] = mapped_column(Text)
    overall: Mapped[float] = mapped_column(Float)
    recommendation: Mapped[str] = mapped_column(String(30))
    results: Mapped[list] = mapped_column(JSON)  # [{criterion, rating, summary, quotes}]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    interview: Mapped[Interview] = relationship(back_populates="scorecards")
