from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, inputs, projects, run
from app.config import FRONTEND_ORIGINS

app = FastAPI(title="AI Business Discovery to POC")

# The browser blocks :3000 -> :8000 without this.
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(projects.router)
app.include_router(inputs.router)
app.include_router(run.router)
