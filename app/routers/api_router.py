"""REST API endpoints for programmatic access."""

from datetime import date
from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import json

from app.database import get_db
from app.auth.jwt_handler import get_current_user_from_cookie
from app.services.page_service import (
    get_user_pages, get_page, create_page, delete_page,
    get_all_metrics, get_content, import_csv, import_excel, add_manual_metric,
)
from app.analytics.analytics_engine import (
    calculate_view_growth, calculate_engagement_rate,
    calculate_follower_growth, calculate_content_performance,
    find_top_content, find_low_performing_content,
    calculate_performance_score, generate_alerts, detect_anomalies,
    generate_health_summary, generate_weekly_summary, generate_monthly_summary,
)
from app.analytics.recommendation_engine import (
    generate_recommendations, generate_daily_action_plan,
)
from app.utils.helpers import get_date_range, format_number
from app.schemas.schemas import PageCreate, ManualMetricEntry

router = APIRouter(prefix="/api")


@router.get("/dashboard/{page_id}")
async def api_dashboard(
    page_id: int,
    period: str = Query("30days"),
    request=None,
    db: Session = Depends(get_db),
):
    """Full dashboard data for a page."""
    # For API, we'll accept unauthenticated for now (add auth middleware in production)
    start, end = get_date_range(period)
    metrics = get_all_metrics(db, page_id)
    content = get_content(db, page_id)
    
    if not metrics:
        return {"has_data": False}
    
    return {
        "views": calculate_view_growth(metrics, start, end),
        "engagement": calculate_engagement_rate(metrics, start, end),
        "followers": calculate_follower_growth(metrics, start, end),
        "top_content": find_top_content(content, "views", 10),
        "alerts": generate_alerts(metrics, start, end),
        "health": generate_health_summary(metrics, content, start, end),
    }


@router.get("/analytics/daily/{page_id}")
async def api_daily_analytics(
    page_id: int,
    period: str = Query("30days"),
    db: Session = Depends(get_db),
):
    """Daily analytics API."""
    start, end = get_date_range(period)
    metrics = get_all_metrics(db, page_id)
    return calculate_view_growth(metrics, start, end)


@router.get("/analytics/content/{page_id}")
async def api_content_analytics(
    page_id: int,
    db: Session = Depends(get_db),
):
    """Content analytics API."""
    content = get_content(db, page_id)
    return {
        "performance": calculate_content_performance(content),
        "top_viewed": find_top_content(content, "views", 10),
        "top_shared": find_top_content(content, "shares", 10),
        "low_performing": find_low_performing_content(content, 10),
    }


@router.get("/analytics/engagement/{page_id}")
async def api_engagement_analytics(
    page_id: int,
    period: str = Query("30days"),
    db: Session = Depends(get_db),
):
    """Engagement analytics API."""
    start, end = get_date_range(period)
    metrics = get_all_metrics(db, page_id)
    return calculate_engagement_rate(metrics, start, end)


@router.get("/analytics/growth/{page_id}")
async def api_growth_analytics(
    page_id: int,
    period: str = Query("30days"),
    db: Session = Depends(get_db),
):
    """Growth analytics API."""
    start, end = get_date_range(period)
    metrics = get_all_metrics(db, page_id)
    return calculate_follower_growth(metrics, start, end)


@router.get("/recommendations/{page_id}")
async def api_recommendations(
    page_id: int,
    period: str = Query("30days"),
    db: Session = Depends(get_db),
):
    """Recommendations API."""
    start, end = get_date_range(period)
    metrics = get_all_metrics(db, page_id)
    content = get_content(db, page_id)
    return generate_recommendations(metrics, content, start, end)


@router.get("/reports/weekly/{page_id}")
async def api_weekly_report(
    page_id: int,
    db: Session = Depends(get_db),
):
    """Weekly report API."""
    metrics = get_all_metrics(db, page_id)
    content = get_content(db, page_id)
    return generate_weekly_summary(metrics, content, date.today())


@router.get("/reports/monthly/{page_id}")
async def api_monthly_report(
    page_id: int,
    db: Session = Depends(get_db),
):
    """Monthly report API."""
    metrics = get_all_metrics(db, page_id)
    content = get_content(db, page_id)
    return generate_monthly_summary(metrics, content, date.today())


@router.post("/pages")
async def api_create_page(
    page_data: PageCreate,
    request=None,
    db: Session = Depends(get_db),
):
    """Create a new page via API."""
    # In production, get user from JWT
    page = create_page(
        db=db, user_id=1,
        platform=page_data.platform,
        page_name=page_data.page_name,
        page_external_id=page_data.page_external_id,
        page_url=page_data.page_url,
        api_token=page_data.api_token,
    )
    return {"id": page.id, "page_name": page.page_name}


@router.delete("/pages/{page_id}")
async def api_delete_page(
    page_id: int,
    db: Session = Depends(get_db),
):
    """Delete a page via API."""
    success = delete_page(db, page_id, 1)  # user_id=1 for demo
    if not success:
        raise HTTPException(status_code=404, detail="Page not found")
    return {"deleted": True}


@router.post("/import/csv")
async def api_import_csv(
    page_id: int = Query(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Import CSV data."""
    content = await file.read()
    result = import_csv(db, page_id, content)
    return result


@router.post("/import/excel")
async def api_import_excel(
    page_id: int = Query(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Import Excel data."""
    content = await file.read()
    result = import_excel(db, page_id, content)
    return result


@router.post("/import/manual")
async def api_manual_entry(
    entry: ManualMetricEntry,
    db: Session = Depends(get_db),
):
    """Manual metric entry."""
    metric = add_manual_metric(
        db=db,
        page_id=entry.page_id,
        metric_date=entry.metric_date,
        views=entry.views,
        followers=entry.followers,
        new_followers=entry.new_followers,
        lost_followers=entry.lost_followers,
        likes=entry.likes,
        comments=entry.comments,
        shares=entry.shares,
        posts=entry.posts,
    )
    return {"id": metric.id, "date": metric.metric_date.isoformat()}
