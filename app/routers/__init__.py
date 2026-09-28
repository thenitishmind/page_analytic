"""Routers package."""

from app.routers.auth import router as auth_router
from app.routers.dashboard import router as dashboard_router
from app.routers.pages_router import router as pages_router
from app.routers.analytics_router import router as analytics_router
from app.routers.api_router import router as api_router
from app.routers.reports import router as reports_router
from app.routers.settings_router import router as settings_router

__all__ = [
    "auth_router",
    "dashboard_router",
    "pages_router",
    "analytics_router",
    "api_router",
    "reports_router",
    "settings_router",
]
