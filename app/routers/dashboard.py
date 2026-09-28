"""Dashboard router — the main page users see after login.

Aggregates all analytics into a single comprehensive view.
"""

from datetime import date, timedelta
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.jwt_handler import get_current_user_from_cookie
from app.models.models import User, Page, AlertConfig, ScoreWeight
from app.services.page_service import get_user_pages, get_daily_metrics, get_all_metrics, get_content
from app.analytics.analytics_engine import (
    calculate_daily_growth,
    calculate_view_growth,
    calculate_engagement_rate,
    calculate_follower_growth,
    calculate_content_performance,
    find_top_content,
    find_low_performing_content,
    calculate_performance_score,
    generate_alerts,
    generate_health_summary,
    detect_anomalies,
)
from app.analytics.recommendation_engine import (
    generate_recommendations,
    generate_daily_action_plan,
    generate_today_performance_summary,
    generate_priorities,
)
from app.utils.helpers import get_date_range, format_number

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def root(request: Request, db: Session = Depends(get_db)):
    """Redirect root to dashboard or login."""
    try:
        user = get_current_user_from_cookie(request, db)
        return RedirectResponse(url="/dashboard", status_code=302)
    except Exception:
        return RedirectResponse(url="/login", status_code=302)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    period: str = Query("30days", description="Date range period"),
    page_id: int = Query(None, description="Page ID to view"),
    db: Session = Depends(get_db),
):
    """Main dashboard with all KPIs, charts, and recommendations."""
    try:
        user = get_current_user_from_cookie(request, db)
    except Exception:
        return RedirectResponse(url="/login", status_code=302)
    
    # Get user's pages
    pages = get_user_pages(db, user.id)
    
    if not pages:
        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "user": user,
                "pages": [],
                "selected_page": None,
                "has_data": False,
                "period": period,
            },
        )
    
    # Select page
    selected_page = None
    if page_id:
        selected_page = next((p for p in pages if p.id == page_id), None)
    if not selected_page:
        selected_page = pages[0]
    
    # Get date range
    start_date, end_date = get_date_range(period)
    
    # Fetch data
    all_metrics = get_all_metrics(db, selected_page.id)
    period_metrics = [m for m in all_metrics if start_date <= m.metric_date <= end_date]
    content_list = get_content(db, selected_page.id)
    period_content = [
        c for c in content_list
        if c.published_at and start_date <= c.published_at.date() <= end_date
    ]
    
    if not all_metrics:
        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "user": user,
                "pages": pages,
                "selected_page": selected_page,
                "has_data": False,
                "period": period,
            },
        )
    
    # Calculate all analytics
    daily_growth = calculate_daily_growth(all_metrics)
    view_data = calculate_view_growth(all_metrics, start_date, end_date)
    engagement_data = calculate_engagement_rate(all_metrics, start_date, end_date)
    follower_data = calculate_follower_growth(all_metrics, start_date, end_date)
    
    # Content analysis
    content_perf = calculate_content_performance(period_content if period_content else content_list)
    top_content = find_top_content(content_list, "views", 5)
    low_content = find_low_performing_content(content_list, 5)
    
    # Performance score
    score_weights_obj = db.query(ScoreWeight).filter(ScoreWeight.user_id == user.id).first()
    weights = None
    if score_weights_obj:
        weights = {
            "view_growth": score_weights_obj.weight_view_growth,
            "engagement": score_weights_obj.weight_engagement,
            "follower_growth": score_weights_obj.weight_follower_growth,
            "consistency": score_weights_obj.weight_consistency,
            "share_rate": score_weights_obj.weight_share_rate,
        }
    perf_score = calculate_performance_score(all_metrics, content_list, start_date, end_date, weights)
    
    # Alerts
    alert_config = db.query(AlertConfig).filter(AlertConfig.user_id == user.id).first()
    alert_thresholds = None
    if alert_config:
        alert_thresholds = {
            "view_increase": alert_config.view_increase_threshold,
            "view_decrease": alert_config.view_decrease_threshold,
            "engagement_low": alert_config.engagement_low_threshold,
            "follower_drop": alert_config.follower_drop_threshold,
        }
    alerts = generate_alerts(all_metrics, start_date, end_date, alert_thresholds)
    
    # Anomalies
    anomalies = detect_anomalies(period_metrics)
    
    # Recommendations
    recommendations = generate_recommendations(all_metrics, content_list, start_date, end_date)
    action_plan = generate_daily_action_plan(all_metrics, content_list, date.today())
    performance_summary = generate_today_performance_summary(all_metrics, content_list, start_date, end_date)
    priorities = generate_priorities(all_metrics, content_list, start_date, end_date)
    health_summary = generate_health_summary(all_metrics, content_list, start_date, end_date)
    
    # Data quality warnings
    data_warnings = _check_data_quality(period_metrics, period_content, start_date, end_date)
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "user": user,
            "pages": pages,
            "selected_page": selected_page,
            "has_data": True,
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            # KPIs
            "daily_growth": daily_growth,
            "view_data": view_data,
            "engagement_data": engagement_data,
            "follower_data": follower_data,
            # Content
            "content_perf": content_perf,
            "top_content": top_content,
            "low_content": low_content,
            # Score
            "perf_score": perf_score,
            # Alerts & Anomalies
            "alerts": alerts,
            "anomalies": anomalies[:5],
            # Recommendations
            "recommendations": recommendations,
            "action_plan": action_plan,
            "performance_summary": performance_summary,
            "priorities": priorities,
            "health_summary": health_summary,
            # Data quality
            "data_warnings": data_warnings,
            # Daily table data
            "daily_metrics": sorted(period_metrics, key=lambda m: m.metric_date, reverse=True),
            # Chart data (JSON-serializable)
            "chart_dates": [m.metric_date.isoformat() for m in sorted(period_metrics, key=lambda m: m.metric_date)],
            "chart_views": [m.views for m in sorted(period_metrics, key=lambda m: m.metric_date)],
            "chart_followers": [m.followers for m in sorted(period_metrics, key=lambda m: m.metric_date)],
            "chart_likes": [m.likes for m in sorted(period_metrics, key=lambda m: m.metric_date)],
            "chart_comments": [m.comments for m in sorted(period_metrics, key=lambda m: m.metric_date)],
            "chart_shares": [m.shares for m in sorted(period_metrics, key=lambda m: m.metric_date)],
            "chart_engagement": [m.engagement_rate for m in sorted(period_metrics, key=lambda m: m.metric_date)],
            # Helpers
            "format_number": format_number,
            "is_demo": selected_page.is_demo,
        },
    )


def _check_data_quality(metrics, content, start_date, end_date):
    """Generate data quality warnings."""
    warnings = []
    
    # Check for missing dates
    expected_days = (end_date - start_date).days + 1
    actual_days = len(metrics)
    missing = expected_days - actual_days
    
    if missing > 0:
        warnings.append(f"Analytics data is missing for {missing} date(s) in the selected period.")
    
    # Check for zero-view days
    zero_days = sum(1 for m in metrics if m.views == 0)
    if zero_days > 0:
        warnings.append(f"{zero_days} day(s) have zero views recorded.")
    
    # Content count warning
    if len(content) < 10:
        warnings.append(
            f"Only {len(content)} content items available. "
            "Some analyses (posting time, content type) may be unreliable with limited data."
        )
    
    # Missing engagement data
    no_engagement = sum(1 for m in metrics if m.likes == 0 and m.comments == 0 and m.shares == 0)
    if no_engagement > len(metrics) * 0.3:
        warnings.append("Engagement data (likes, comments, shares) is missing for many dates.")
    
    return warnings
