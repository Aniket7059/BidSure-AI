from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

import app.models

from app.core.config import settings
from app.database.session import engine, get_db

from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    audit_logs,
    bid_documents,
    bid_submissions,
    bidders,
    compliance,
    dashboard,
    discrepancies,
    tenders,
    verification,
)
from app.api.routes.auth import router as auth_router
from app.services.evaluators.register import register_evaluators
from app.providers.register import register_providers


# # Create all tables
# Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifecycle.

    Requirement evaluators and verification providers are
    registered when the application starts.
    """

    # --------------------------------------------------
    # Startup
    # --------------------------------------------------

    from app.database.base import Base
    from app.database.session import engine

    Base.metadata.create_all(bind=engine)
    register_evaluators()
    register_providers()

    yield

    # --------------------------------------------------
    # Shutdown
    # --------------------------------------------------

    # Reserved for future cleanup logic.


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# API Routers
# --------------------------------------------------

app.include_router(bidders.router)
app.include_router(tenders.router)
app.include_router(bid_submissions.router)
app.include_router(bid_documents.router)
app.include_router(compliance.router)
app.include_router(verification.router)
app.include_router(discrepancies.router)
app.include_router(audit_logs.router)
app.include_router(dashboard.router)
app.include_router(auth_router)


# --------------------------------------------------
# Root
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "environment": settings.ENVIRONMENT,
    }


# --------------------------------------------------
# Health Checks
# --------------------------------------------------

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health/database")
def database_health_check(
    db: Session = Depends(get_db),
):
    db.execute(text("SELECT 1"))

    return {
        "status": "healthy",
        "database": "connected",
    }