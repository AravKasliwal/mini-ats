from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user, make_token, recruiter_only, verify_password
from ..db import get_db
from ..models import User
from ..schemas import TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == form.username))
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(401, "Bad credentials")
    return TokenOut(access_token=make_token(user), user=user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@router.get("/interviewers", response_model=list[UserOut])
def interviewers(db: Session = Depends(get_db), _: User = Depends(recruiter_only)):
    return db.scalars(select(User).where(User.role == "interviewer")).all()
