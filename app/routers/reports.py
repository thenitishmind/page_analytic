"""Reports router for weekly/monthly reports and recommendations page."""

from datetime import date
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import csv
import io
import json

from app.database import get_db
from app.auth.jwt_handler import get_current_user_from_cookie
from app.services.page_service import get_user_pages, get_all_metrics, get_content
from app.analytics.analytics_engine import (
    calculate_view_growth, calculate_engagement_rate,
    calculate_follower_growth, find_top_content, find_low_performing_content,
    find_best_posting_day, find_best_posting_time, calculate_performance_score,
    analyze_content_types, generate_weekly_summary, generate_monthly_summary,
)
from app.analytics.recommendation_engine import (
    generate_recommendations, generate_daily_action_plan,
    generate_today_performance_summary, generate_priorities,
)
from app.utils.helpers import get_date_range, format_number

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/recommendations", response_class=HTMLResponse)
async def recommendations_page(
    request: Request,
    period: str = Query("30days"),
    page_id: int = Query(None),
    db: Session = Depends(get_db),
):
    """Recommendations page."""
    try:
        user = get_current_user_from_cookie(request, db)
    except Exception:
        return RedirectResponse(url="/login", status_code=302)
    
    pages = get_user_pages(db, user.id)
    selected_page = None
    if pages:
        if page_id:
            selected_page = next((p for p in pages if p.id == page_id), pages[0])
        else:
            selected_page = pages[0]
    
    if not selected_page:
        return templates.TemplateResponse(
            request=request,
            name="recommendations.html",
            context={
                "user": user, "pages": pages,
                "selected_page": None, "has_data": False, "period": period,
            },
        )
    
    start, end = get_date_range(period)
    metrics = get_all_metrics(db, selected_page.id)
    content = get_content(db, selected_page.id)
    
    recs = generate_recommendations(metrics, content, start, end)
    action_plan = generate_daily_action_plan(metrics, content, date.today())
    perf_summary = generate_today_performance_summary(metrics, content, start, end)
    priorities = generate_priorities(metrics, content, start, end)
    
    return templates.TemplateResponse(
        request=request,
        name="recommendations.html",
        context={
            "user": user, "pages": pages,
            "selected_page": selected_page, "has_data": True, "period": period,
            "recommendations": recs,
            "action_plan": action_plan,
            "performance_summary": perf_summary,
            "priorities": priorities,
            "format_number": format_number,
            "is_demo": selected_page.is_demo,
        },
    )


@router.get("/reports", response_class=HTMLResponse)
async def reports_page(
    request: Request,
    report_type: str = Query("weekly"),
    period: str = Query("30days"),
    page_id: int = Query(None),
    db: Session = Depends(get_db),
):
    """Reports page (weekly/monthly)."""
    try:
        user = get_current_user_from_cookie(request, db)
    except Exception:
        return RedirectResponse(url="/login", status_code=302)
    
    pages = get_user_pages(db, user.id)
    selected_page = None
    if pages:
        if page_id:
            selected_page = next((p for p in pages if p.id == page_id), pages[0])
        else:
            selected_page = pages[0]
    
    if not selected_page:
        return templates.TemplateResponse(
            request=request,
            name="reports.html",
            context={
                "user": user, "pages": pages,
                "selected_page": None, "has_data": False,
                "report_type": report_type, "period": period,
            },
        )
    
    metrics = get_all_metrics(db, selected_page.id)
    content = get_content(db, selected_page.id)
    
    if report_type == "monthly":
        report = generate_monthly_summary(metrics, content, date.today())
    else:
        report = generate_weekly_summary(metrics, content, date.today())
    
    return templates.TemplateResponse(
        request=request,
        name="reports.html",
        context={
            "user": user, "pages": pages,
            "selected_page": selected_page, "has_data": True,
            "report_type": report_type, "period": period,
            "report": report,
            "format_number": format_number,
            "is_demo": selected_page.is_demo,
        },
    )


@router.get("/export/csv")
async def export_csv(
    page_id: int = Query(...),
    period: str = Query("30days"),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Export daily metrics as CSV."""
    start, end = get_date_range(period)
    from app.services.page_service import get_daily_metrics
    metrics = get_daily_metrics(db, page_id, start, end)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["date", "views", "followers", "new_followers", "lost_followers",
                     "likes", "comments", "shares", "posts", "engagement_rate"])
    
    for m in metrics:
        writer.writerow([
            m.metric_date.isoformat(), m.views, m.followers,
            m.new_followers, m.lost_followers, m.likes,
            m.comments, m.shares, m.posts, m.engagement_rate,
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=analytics_{period}.csv"},
    )


@router.get("/export/json")
async def export_json(
    page_id: int = Query(...),
    period: str = Query("30days"),
    db: Session = Depends(get_db),
):
    """Export analytics data as JSON."""
    start, end = get_date_range(period)
    metrics = get_all_metrics(db, page_id)
    content = get_content(db, page_id)
    
    report = generate_monthly_summary(metrics, content, date.today())
    
    return report
