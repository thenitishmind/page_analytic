"""Settings and data import router."""

from datetime import date
from fastapi import APIRouter, Request, Depends, Form, Query, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.jwt_handler import get_current_user_from_cookie
from app.models.models import User, AlertConfig, ScoreWeight, Page
from app.services.page_service import (
    get_user_pages, import_csv, import_excel, add_manual_metric,
)
from app.utils.helpers import format_number

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, db: Session = Depends(get_db)):
    """Settings page."""
    try:
        user = get_current_user_from_cookie(request, db)
    except Exception:
        return RedirectResponse(url="/login", status_code=302)
    
    alert_config = db.query(AlertConfig).filter(AlertConfig.user_id == user.id).first()
    score_weights = db.query(ScoreWeight).filter(ScoreWeight.user_id == user.id).first()
    pages = get_user_pages(db, user.id)
    
    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={
            "user": user,
            "pages": pages,
            "alert_config": alert_config,
            "score_weights": score_weights,
            "message": None,
            "format_number": format_number,
        },
    )


@router.post("/settings/theme")
async def update_theme(
    request: Request,
    theme: str = Form(...),
    db: Session = Depends(get_db),
):
    """Update user's theme preference."""
    try:
        user = get_current_user_from_cookie(request, db)
    except Exception:
        return RedirectResponse(url="/login", status_code=302)
    
    user.theme = theme
    db.commit()
    return RedirectResponse(url="/settings", status_code=302)


@router.post("/settings/alerts")
async def update_alerts(
    request: Request,
    view_increase_threshold: float = Form(25.0),
    view_decrease_threshold: float = Form(20.0),
    engagement_low_threshold: float = Form(3.0),
    follower_drop_threshold: float = Form(10.0),
    db: Session = Depends(get_db),
):
    """Update alert thresholds."""
    try:
        user = get_current_user_from_cookie(request, db)
    except Exception:
        return RedirectResponse(url="/login", status_code=302)
    
    config = db.query(AlertConfig).filter(AlertConfig.user_id == user.id).first()
    if config:
        config.view_increase_threshold = view_increase_threshold
        config.view_decrease_threshold = view_decrease_threshold
        config.engagement_low_threshold = engagement_low_threshold
        config.follower_drop_threshold = follower_drop_threshold
    else:
        config = AlertConfig(
            user_id=user.id,
            view_increase_threshold=view_increase_threshold,
            view_decrease_threshold=view_decrease_threshold,
            engagement_low_threshold=engagement_low_threshold,
            follower_drop_threshold=follower_drop_threshold,
        )
        db.add(config)
    
    db.commit()
    return RedirectResponse(url="/settings", status_code=302)


@router.post("/settings/weights")
async def update_score_weights(
    request: Request,
    weight_view_growth: float = Form(0.25),
    weight_engagement: float = Form(0.25),
    weight_follower_growth: float = Form(0.20),
    weight_consistency: float = Form(0.15),
    weight_share_rate: float = Form(0.15),
    db: Session = Depends(get_db),
):
    """Update performance score weights."""
    try:
        user = get_current_user_from_cookie(request, db)
    except Exception:
        return RedirectResponse(url="/login", status_code=302)
    
    weights = db.query(ScoreWeight).filter(ScoreWeight.user_id == user.id).first()
    if weights:
        weights.weight_view_growth = weight_view_growth
        weights.weight_engagement = weight_engagement
        weights.weight_follower_growth = weight_follower_growth
        weights.weight_consistency = weight_consistency
        weights.weight_share_rate = weight_share_rate
    else:
        weights = ScoreWeight(
            user_id=user.id,
            weight_view_growth=weight_view_growth,
            weight_engagement=weight_engagement,
            weight_follower_growth=weight_follower_growth,
            weight_consistency=weight_consistency,
            weight_share_rate=weight_share_rate,
        )
        db.add(weights)
    
    db.commit()
    return RedirectResponse(url="/settings", status_code=302)


@router.post("/import/upload")
async def upload_data(
    request: Request,
    page_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Handle CSV/Excel file upload."""
    try:
        user = get_current_user_from_cookie(request, db)
    except Exception:
        return RedirectResponse(url="/login", status_code=302)
    
    content = await file.read()
    
    if file.filename.endswith(".csv"):
        result = import_csv(db, page_id, content)
    elif file.filename.endswith((".xlsx", ".xls")):
        result = import_excel(db, page_id, content)
    else:
        result = {"imported": 0, "errors": ["Unsupported file format. Use CSV or XLSX."]}
    
    pages = get_user_pages(db, user.id)
    alert_config = db.query(AlertConfig).filter(AlertConfig.user_id == user.id).first()
    score_weights = db.query(ScoreWeight).filter(ScoreWeight.user_id == user.id).first()
    
    message = f"Imported {result['imported']} records."
    if result.get("errors"):
        message += f" {len(result['errors'])} error(s)."
    
    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={
            "user": user,
            "pages": pages,
            "alert_config": alert_config,
            "score_weights": score_weights,
            "message": message,
            "import_result": result,
            "format_number": format_number,
        },
    )


@router.post("/import/manual")
async def manual_entry(
    request: Request,
    page_id: int = Form(...),
    metric_date: str = Form(...),
    views: int = Form(0),
    followers: int = Form(0),
    new_followers: int = Form(0),
    lost_followers: int = Form(0),
    likes: int = Form(0),
    comments: int = Form(0),
    shares: int = Form(0),
    posts: int = Form(0),
    db: Session = Depends(get_db),
):
    """Handle manual metric entry."""
    try:
        user = get_current_user_from_cookie(request, db)
    except Exception:
        return RedirectResponse(url="/login", status_code=302)
    
    from datetime import datetime
    parsed_date = datetime.strptime(metric_date, "%Y-%m-%d").date()
    
    add_manual_metric(
        db=db,
        page_id=page_id,
        metric_date=parsed_date,
        views=views,
        followers=followers,
        new_followers=new_followers,
        lost_followers=lost_followers,
        likes=likes,
        comments=comments,
        shares=shares,
        posts=posts,
    )
    
    return RedirectResponse(url="/settings", status_code=302)
