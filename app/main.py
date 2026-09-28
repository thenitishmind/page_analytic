"""FastAPI application entry point.

Initializes the app, registers all routers, mounts static files,
and optionally seeds demo data on startup.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.database import engine, SessionLocal, Base
from app.models.models import User, Page, DailyMetric, Content, Recommendation, AlertConfig, ScoreWeight
from app.routers import (
    auth_router,
    dashboard_router,
    pages_router,
    analytics_router,
    api_router,
    reports_router,
    settings_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler: create tables and seed demo data."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Seed demo data if DEMO_MODE is enabled
    if settings.DEMO_MODE:
        db = SessionLocal()
        try:
            from app.utils.demo_data import initialize_demo_data
            initialize_demo_data(db)
        finally:
            db.close()
    
    yield


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="A comprehensive analytics dashboard for social media pages.",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Register routers
app.include_router(auth_router, tags=["Authentication"])
app.include_router(dashboard_router, tags=["Dashboard"])
app.include_router(pages_router, tags=["Pages"])
app.include_router(analytics_router, tags=["Analytics"])
app.include_router(api_router, tags=["API"])
app.include_router(reports_router, tags=["Reports"])
app.include_router(settings_router, tags=["Settings"])
