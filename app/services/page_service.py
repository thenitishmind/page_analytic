"""Page service for CRUD operations and data import."""

import csv
import io
from datetime import date, datetime
from typing import List, Optional, BinaryIO

import pandas as pd
from sqlalchemy.orm import Session

from app.models.models import Page, DailyMetric, Content


def create_page(
    db: Session,
    user_id: int,
    platform: str,
    page_name: str,
    page_external_id: Optional[str] = None,
    page_url: Optional[str] = None,
    api_token: Optional[str] = None,
) -> Page:
    """Create a new page for tracking."""
    page = Page(
        user_id=user_id,
        platform=platform,
        page_name=page_name,
        page_external_id=page_external_id,
        page_url=page_url,
        api_token=api_token,
    )
    db.add(page)
    db.commit()
    db.refresh(page)
    return page


def get_user_pages(db: Session, user_id: int) -> List[Page]:
    """Get all pages for a user."""
    return db.query(Page).filter(Page.user_id == user_id).all()


def get_page(db: Session, page_id: int, user_id: int) -> Optional[Page]:
    """Get a specific page, ensuring it belongs to the user."""
    return db.query(Page).filter(
        Page.id == page_id, Page.user_id == user_id
    ).first()


def delete_page(db: Session, page_id: int, user_id: int) -> bool:
    """Delete a page and all its associated data."""
    page = get_page(db, page_id, user_id)
    if not page:
        return False
    db.delete(page)
    db.commit()
    return True


def get_daily_metrics(
    db: Session,
    page_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[DailyMetric]:
    """Get daily metrics for a page within an optional date range."""
    query = db.query(DailyMetric).filter(DailyMetric.page_id == page_id)
    
    if start_date:
        query = query.filter(DailyMetric.metric_date >= start_date)
    if end_date:
        query = query.filter(DailyMetric.metric_date <= end_date)
    
    return query.order_by(DailyMetric.metric_date).all()


def get_all_metrics(db: Session, page_id: int) -> List[DailyMetric]:
    """Get all daily metrics for a page (for calculations needing full history)."""
    return db.query(DailyMetric).filter(
        DailyMetric.page_id == page_id
    ).order_by(DailyMetric.metric_date).all()


def get_content(
    db: Session,
    page_id: int,
    content_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[Content]:
    """Get content items for a page with optional filters."""
    query = db.query(Content).filter(Content.page_id == page_id)
    
    if content_type:
        query = query.filter(Content.content_type == content_type)
    if start_date:
        query = query.filter(Content.published_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Content.published_at <= datetime.combine(end_date, datetime.max.time()))
    
    return query.order_by(Content.published_at.desc()).all()


def add_manual_metric(
    db: Session,
    page_id: int,
    metric_date: date,
    views: int = 0,
    followers: int = 0,
    new_followers: int = 0,
    lost_followers: int = 0,
    likes: int = 0,
    comments: int = 0,
    shares: int = 0,
    posts: int = 0,
) -> DailyMetric:
    """Add or update a daily metric entry manually."""
    # Check for existing entry on this date
    existing = db.query(DailyMetric).filter(
        DailyMetric.page_id == page_id,
        DailyMetric.metric_date == metric_date,
    ).first()
    
    engagement_rate = 0.0
    if views > 0:
        engagement_rate = round(((likes + comments + shares) / views) * 100, 2)
    
    if existing:
        existing.views = views
        existing.followers = followers
        existing.new_followers = new_followers
        existing.lost_followers = lost_followers
        existing.likes = likes
        existing.comments = comments
        existing.shares = shares
        existing.posts = posts
        existing.engagement_rate = engagement_rate
        metric = existing
    else:
        metric = DailyMetric(
            page_id=page_id,
            metric_date=metric_date,
            views=views,
            followers=followers,
            new_followers=new_followers,
            lost_followers=lost_followers,
            likes=likes,
            comments=comments,
            shares=shares,
            posts=posts,
            engagement_rate=engagement_rate,
        )
        db.add(metric)
    
    db.commit()
    db.refresh(metric)
    return metric


def _extract_val(row_dict: dict, aliases: list) -> int:
    """Extract metric value using flexible column alias matching."""
    for key, val in row_dict.items():
        clean_key = str(key).strip().lower().replace(" ", "_").replace("-", "_")
        if clean_key in aliases:
            return _safe_int(val)
    return 0


def import_csv(db: Session, page_id: int, file_content: bytes) -> dict:
    """Import daily metrics from CSV with support for Meta Business Suite & custom exports."""
    try:
        text = file_content.decode("utf-8-sig", errors="ignore")
        reader = csv.DictReader(io.StringIO(text))
        
        imported = 0
        errors = []
        
        for row_num, row in enumerate(reader, start=2):
            try:
                date_raw = None
                for k in row:
                    if k and k.strip().lower() in ("date", "metric_date", "day", "created_time", "timestamp"):
                        date_raw = row[k]
                        break
                if not date_raw and row:
                    date_raw = list(row.values())[0]
                
                metric_date = _parse_date(str(date_raw or "").strip())
                if not metric_date:
                    errors.append(f"Row {row_num}: Invalid or missing date '{date_raw}'")
                    continue
                
                views = _extract_val(row, ["views", "page_views", "daily_views", "reach", "daily_reach", "impressions"])
                followers = _extract_val(row, ["followers", "total_followers", "page_followers", "fans"])
                new_followers = _extract_val(row, ["new_followers", "new_fans", "net_followers", "follows", "paid_followers"])
                lost_followers = _extract_val(row, ["lost_followers", "unfollows"])
                likes = _extract_val(row, ["likes", "reactions", "post_reactions", "page_likes"])
                comments = _extract_val(row, ["comments", "post_comments"])
                shares = _extract_val(row, ["shares", "post_shares"])
                posts = _extract_val(row, ["posts", "posts_published", "content_published", "reels_published"])
                
                add_manual_metric(
                    db=db,
                    page_id=page_id,
                    metric_date=metric_date,
                    views=views,
                    followers=followers,
                    new_followers=new_followers,
                    lost_followers=lost_followers,
                    likes=likes,
                    comments=comments,
                    shares=shares,
                    posts=posts,
                )
                imported += 1
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        
        return {"imported": imported, "errors": errors, "total_rows": imported + len(errors)}
    
    except Exception as e:
        return {"imported": 0, "errors": [str(e)], "total_rows": 0}


def import_excel(db: Session, page_id: int, file_content: bytes) -> dict:
    """Import daily metrics from Excel with support for Meta Business Suite & custom exports."""
    try:
        df = pd.read_excel(io.BytesIO(file_content))
        
        imported = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                row_dict = row.to_dict()
                date_raw = None
                for k, v in row_dict.items():
                    if str(k).strip().lower() in ("date", "metric_date", "day", "created_time", "timestamp"):
                        date_raw = v
                        break
                
                metric_date = _parse_date(str(date_raw or ""))
                if not metric_date:
                    errors.append(f"Row {idx + 2}: Invalid date '{date_raw}'")
                    continue
                
                views = _extract_val(row_dict, ["views", "page_views", "daily_views", "reach", "daily_reach", "impressions"])
                followers = _extract_val(row_dict, ["followers", "total_followers", "page_followers", "fans"])
                new_followers = _extract_val(row_dict, ["new_followers", "new_fans", "net_followers", "follows"])
                lost_followers = _extract_val(row_dict, ["lost_followers", "unfollows"])
                likes = _extract_val(row_dict, ["likes", "reactions", "post_reactions", "page_likes"])
                comments = _extract_val(row_dict, ["comments", "post_comments"])
                shares = _extract_val(row_dict, ["shares", "post_shares"])
                posts = _extract_val(row_dict, ["posts", "posts_published", "content_published"])
                
                add_manual_metric(
                    db=db,
                    page_id=page_id,
                    metric_date=metric_date,
                    views=views,
                    followers=followers,
                    new_followers=new_followers,
                    lost_followers=lost_followers,
                    likes=likes,
                    comments=comments,
                    shares=shares,
                    posts=posts,
                )
                imported += 1
            except Exception as e:
                errors.append(f"Row {idx + 2}: {str(e)}")
        
        return {"imported": imported, "errors": errors, "total_rows": imported + len(errors)}
    
    except Exception as e:
        return {"imported": 0, "errors": [str(e)], "total_rows": 0}


def _parse_date(date_str: str) -> Optional[date]:
    """Parse a date string in common formats."""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    # Try pandas parser as fallback
    try:
        return pd.to_datetime(date_str).date()
    except Exception:
        return None


def _safe_int(value) -> int:
    """Safely convert a value to int."""
    try:
        if pd.isna(value):
            return 0
        return int(float(value))
    except (ValueError, TypeError):
        return 0
