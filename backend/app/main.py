"""FastAPI entrypoint for the claims adjuster backend."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.claims import router as claims_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Automated Claims Adjuster API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(claims_router, prefix="/api", tags=["claims"])


@app.get("/health")
def health() -> dict[str, str]:
    """Return service health status."""
    logging.info("Health check requested")
    return {"status": "ok"}
