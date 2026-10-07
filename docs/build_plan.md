# Mini ATS / Interview Agent — Build Plan

## Goal
Public demo of a thin Talent Flow–style loop: resume → rubric score → candidate card → schedule stub → transcript scorecard, with recruiter vs interviewer roles.

## Repo outline
```
mini-ats/
  README.md                 # demo GIF, architecture, how to run
  docker-compose.yml        # postgres + api + web
  .env.example
  backend/
    app/
      main.py
      auth.py               # simple JWT or session; roles: recruiter | interviewer
      models.py             # Job, Rubric, Candidate, Run, Interview, Scorecard
      schemas.py
      routers/
        jobs.py
        candidates.py
        score.py
        schedule.py
        scorecards.py
      services/
        parse_resume.py     # PDF/text extract
        rubric_score.py     # LLM or rule+LLM hybrid
        scorecard.py        # transcript → scorecard w/ quotes
      eval/
        fixtures/           # 5–10 anonymized resumes + gold labels
        run_eval.py         # precision/recall or agreement vs gold
    alembic/
    requirements.txt
  frontend/
    src/
      pages/ Login, Jobs, CandidateDetail, Scorecard
      api.ts
  scripts/seed.py           # demo job + users
```

## MVP slices (ship in order)
1. **Scaffold** — Compose up, health check, seed recruiter/interviewer users.
2. **Jobs + rubrics** — CRUD one job with weighted criteria (skills, experience, education).
3. **Upload + parse** — PDF → plain text; store Candidate.
4. **Score run** — apply rubric; show per-criterion scores + short rationale (cite resume lines).
5. **Schedule stub** — pick a slot; no real calendar; store Interview row.
6. **Scorecard** — paste notes/transcript → structured scorecard with quoted evidence.
7. **RBAC** — interviewer only sees assigned candidates; recruiter sees all.
8. **Eval** — fixed fixture set; `run_eval.py` prints agreement metrics; mention in README.
9. **Polish** — README architecture diagram, one-command demo, screenshots.

## Stack
- FastAPI + SQLAlchemy + Postgres
- React + Vite (minimal UI)
- Docker Compose
- One LLM provider via env key (optional offline fake scorer for CI)

## What NOT to build (v1)
- Real iCIMS / Outlook / Teams
- Real email send
- Full CI/CD to cloud (local Compose is enough; optional GitHub Actions: pytest + frontend build)
- Fancy agent frameworks — keep calls explicit and logged

## Resume / interview talking points
- End-to-end product ownership of a recruiting workflow
- Structured scoring with evidence, not vibes
- Role-based access
- Eval harness so changes don't regress quality
- Honest scope: public slice inspired by internship work, not proprietary code

## Definition of done
- `docker compose up` → login → score a resume → create interview → generate scorecard
- Eval script runs without API keys (fake scorer) and with keys (LLM)
- Clean README a recruiter can skim in 2 minutes
