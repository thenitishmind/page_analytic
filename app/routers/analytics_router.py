"""Analytics sub-page routers for daily, content, engagement, and growth views."""

from datetime import date, timedelta
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.jwt_handler import get_current_user_from_cookie
from app.services.page_service import get_user_pages, get_all_metrics, get_content
from app.analytics.analytics_engine import (
    calculate_view_growth,
    calculate_engagement_rate,
    calculate_follower_growth,
    calculate_content_performance,
    find_top_content,
    find_low_performing_content,
    find_best_posting_day,
    find_best_posting_time,
    analyze_content_types,
    detect_anomalies,
)
from app.utils.helpers import get_date_range, format_number

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def _get_page_context(request, db, page_id, period):
    """Common helper to build page context for analytics views."""
    try:
        user = get_current_user_from_cookie(request, db)
    except Exception:
        return None, None, None, None, None, None, None
    
    pages = get_user_pages(db, user.id)
    if not pages:
        return user, pages, None, None, None, None, None
    
    selected_page = None
    if page_id:
        selected_page = next((p for p in pages if p.id == page_id), None)
    if not selected_page:
        selected_page = pages[0]
    
    start_date, end_date = get_date_range(period)
    all_metrics = get_all_metrics(db, selected_page.id)
    content_list = get_content(db, selected_page.id)
    
    return user, pages, selected_page, start_date, end_date, all_metrics, content_list


@router.get("/analytics/daily", response_class=HTMLResponse)
async def daily_analytics(
    request: Request,
    period: str = Query("30days"),
    page_id: int = Query(None),
    db: Session = Depends(get_db),
):
    """Detailed daily analytics view."""
    user, pages, page, start, end, metrics, content = _get_page_context(request, db, page_id, period)
    if user is None:
        return RedirectResponse(url="/login", status_code=302)
    if not page or not metrics:
        return templates.TemplateResponse(
            request=request,
            name="analytics_daily.html",
            context={
                "user": user, "pages": pages,
                "selected_page": page, "has_data": False, "period": period,
            },
        )
    
    view_data = calculate_view_growth(metrics, start, end)
    period_metrics = sorted(
        [m for m in metrics if start <= m.metric_date <= end],
        key=lambda m: m.metric_date, reverse=True,
    )
    anomalies = detect_anomalies(period_metrics)
    
    return templates.TemplateResponse(
        request=request,
        name="analytics_daily.html",
        context={
            "user": user, "pages": pages,
            "selected_page": page, "has_data": True, "period": period,
            "view_data": view_data,
            "daily_metrics": period_metrics,
            "anomalies": anomalies,
            "chart_dates": [m.metric_date.isoformat() for m in sorted(period_metrics, key=lambda m: m.metric_date)],
            "chart_views": [m.views for m in sorted(period_metrics, key=lambda m: m.metric_date)],
            "format_number": format_number,
            "is_demo": page.is_demo,
        },
    )


@router.get("/analytics/content", response_class=HTMLResponse)
async def content_analytics(
    request: Request,
    period: str = Query("30days"),
    page_id: int = Query(None),
    db: Session = Depends(get_db),
):
    """Detailed content performance view."""
    user, pages, page, start, end, metrics, content = _get_page_context(request, db, page_id, period)
    if user is None:
        return RedirectResponse(url="/login", status_code=302)
    if not page:
        return templates.TemplateResponse(
            request=request,
            name="analytics_content.html",
            context={
                "user": user, "pages": pages,
                "selected_page": page, "has_data": False, "period": period,
            },
        )
    
    content_perf = calculate_content_performance(content)
    top_viewed = find_top_content(content, "views", 10)
    top_shared = find_top_content(content, "shares", 10)
    top_commented = find_top_content(content, "comments", 10)
    top_engagement = find_top_content(content, "engagement", 10)
    low_content = find_low_performing_content(content, 10)
    type_analysis = analyze_content_types(content)
    best_day = find_best_posting_day(content)
    best_time = find_best_posting_time(content)
    
    return templates.TemplateResponse(
        request=request,
        name="analytics_content.html",
        context={
            "user": user, "pages": pages,
            "selected_page": page, "has_data": True, "period": period,
            "content_perf": content_perf,
            "top_viewed": top_viewed,
            "top_shared": top_shared,
            "top_commented": top_commented,
            "top_engagement": top_engagement,
            "low_content": low_content,
            "type_analysis": type_analysis,
            "best_day": best_day,
            "best_time": best_time,
            "format_number": format_number,
            "is_demo": page.is_demo,
        },
    )


@router.get("/analytics/engagement", response_class=HTMLResponse)
async def engagement_analytics(
    request: Request,
    period: str = Query("30days"),
    page_id: int = Query(None),
    db: Session = Depends(get_db),
):
    """Detailed engagement analytics view."""
    user, pages, page, start, end, metrics, content = _get_page_context(request, db, page_id, period)
    if user is None:
        return RedirectResponse(url="/login", status_code=302)
    if not page or not metrics:
        return templates.TemplateResponse(
            request=request,
            name="analytics_engagement.html",
            context={
                "user": user, "pages": pages,
                "selected_page": page, "has_data": False, "period": period,
            },
        )
    
    engagement_data = calculate_engagement_rate(metrics, start, end)
    period_metrics = sorted(
        [m for m in metrics if start <= m.metric_date <= end],
        key=lambda m: m.metric_date,
    )
    
    return templates.TemplateResponse(
        request=request,
        name="analytics_engagement.html",
        context={
            "user": user, "pages": pages,
            "selected_page": page, "has_data": True, "period": period,
            "engagement_data": engagement_data,
            "chart_dates": [m.metric_date.isoformat() for m in period_metrics],
            "chart_engagement": [m.engagement_rate for m in period_metrics],
            "chart_likes": [m.likes for m in period_metrics],
            "chart_comments": [m.comments for m in period_metrics],
            "chart_shares": [m.shares for m in period_metrics],
            "format_number": format_number,
            "is_demo": page.is_demo,
        },
    )


@router.get("/analytics/growth", response_class=HTMLResponse)
async def growth_analytics(
    request: Request,
    period: str = Query("30days"),
    page_id: int = Query(None),
    db: Session = Depends(get_db),
):
    """Detailed follower/growth analytics view."""
    user, pages, page, start, end, metrics, content = _get_page_context(request, db, page_id, period)
    if user is None:
        return RedirectResponse(url="/login", status_code=302)
    if not page or not metrics:
        return templates.TemplateResponse(
            request=request,
            name="analytics_growth.html",
            context={
                "user": user, "pages": pages,
                "selected_page": page, "has_data": False, "period": period,
            },
        )
    
    follower_data = calculate_follower_growth(metrics, start, end)
    view_data = calculate_view_growth(metrics, start, end)
    period_metrics = sorted(
        [m for m in metrics if start <= m.metric_date <= end],
        key=lambda m: m.metric_date,
    )
    
    return templates.TemplateResponse(
        request=request,
        name="analytics_growth.html",
        context={
            "user": user, "pages": pages,
            "selected_page": page, "has_data": True, "period": period,
            "follower_data": follower_data,
            "view_data": view_data,
            "chart_dates": [m.metric_date.isoformat() for m in period_metrics],
            "chart_followers": [m.followers for m in period_metrics],
            "chart_new_followers": [m.new_followers for m in period_metrics],
            "chart_views": [m.views for m in period_metrics],
            "format_number": format_number,
            "is_demo": page.is_demo,
        },
    )
