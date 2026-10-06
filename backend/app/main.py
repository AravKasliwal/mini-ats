import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models  # noqa: F401  (register tables)
from .routers import auth_router, candidates, jobs, schedule, scorecards
from .services.llm import scorer_mode

logging.basicConfig(level=logging.INFO)

if "JWT_SECRET" not in os.environ:
    logging.warning("JWT_SECRET not set; using an insecure development default")

app = FastAPI(title="Mini ATS")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","), allow_methods=["*"], allow_headers=["*"])

for r in (auth_router.router, jobs.router, candidates.router, schedule.router, scorecards.router):
    app.include_router(r, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok", "scorer": scorer_mode()}
