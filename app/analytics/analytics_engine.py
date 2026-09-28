"""Core Analytics Engine for the Page Analytics Dashboard.

All calculation functions in this module are designed to be:
- Testable independently (pure functions where possible)
- Safe with zero/empty values
- Transparent in their methodology

Every formula used is documented in docstrings.
"""

import statistics
from datetime import date, timedelta, datetime
from typing import List, Dict, Optional, Tuple, Any
from collections import defaultdict

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc

from app.models.models import DailyMetric, Content, Page, ScoreWeight
from app.utils.helpers import (
    safe_percent_change, get_previous_period, get_trend_label,
    get_change_direction, calculate_median, calculate_std_dev,
    calculate_z_score, weekday_name, format_number,
)


# ─── Daily Growth ────────────────────────────────────────────────────────────

def calculate_daily_growth(
    metrics: List[DailyMetric],
) -> Dict[str, Any]:
    """Calculate day-over-day growth for the most recent day.
    
    Returns dict with today's metrics and change percentages vs yesterday.
    """
    if not metrics:
        return {"has_data": False}
    
    sorted_m = sorted(metrics, key=lambda m: m.metric_date, reverse=True)
    today_m = sorted_m[0]
    yesterday_m = sorted_m[1] if len(sorted_m) > 1 else None
    
    result = {
        "has_data": True,
        "date": today_m.metric_date,
        "views": today_m.views,
        "followers": today_m.followers,
        "new_followers": today_m.new_followers,
        "likes": today_m.likes,
        "comments": today_m.comments,
        "shares": today_m.shares,
        "posts": today_m.posts,
        "engagement_rate": today_m.engagement_rate,
    }
    
    if yesterday_m:
        result["views_change"] = safe_percent_change(today_m.views, yesterday_m.views)
        result["followers_change"] = today_m.followers - yesterday_m.followers
        result["likes_change"] = safe_percent_change(today_m.likes, yesterday_m.likes)
        result["comments_change"] = safe_percent_change(today_m.comments, yesterday_m.comments)
        result["shares_change"] = safe_percent_change(today_m.shares, yesterday_m.shares)
        result["engagement_change"] = safe_percent_change(
            today_m.engagement_rate, yesterday_m.engagement_rate
        )
    else:
        result["views_change"] = 0.0
        result["followers_change"] = 0
        result["likes_change"] = 0.0
        result["comments_change"] = 0.0
        result["shares_change"] = 0.0
        result["engagement_change"] = 0.0
    
    return result


# ─── View Analysis ───────────────────────────────────────────────────────────

def calculate_view_growth(
    metrics: List[DailyMetric],
    start_date: date,
    end_date: date,
) -> Dict[str, Any]:
    """Calculate comprehensive view analytics for a date range.
    
    Includes total, average, median, min, max, 7-day and 30-day moving averages,
    and identifies spike days.
    
    Formula for growth:
        growth_% = ((current_period_total - previous_period_total) / previous_period_total) × 100
    """
    period_metrics = [m for m in metrics if start_date <= m.metric_date <= end_date]
    
    if not period_metrics:
        return {"has_data": False}
    
    views_list = [m.views for m in period_metrics]
    dates_list = [m.metric_date for m in period_metrics]
    
    total_views = sum(views_list)
    avg_views = round(statistics.mean(views_list), 0) if views_list else 0
    median_views = calculate_median(views_list)
    max_views = max(views_list)
    min_views = min(views_list)
    max_date = period_metrics[views_list.index(max_views)].metric_date
    min_date = period_metrics[views_list.index(min_views)].metric_date
    
    # Previous period comparison
    prev_start, prev_end = get_previous_period(start_date, end_date)
    prev_metrics = [m for m in metrics if prev_start <= m.metric_date <= prev_end]
    prev_total = sum(m.views for m in prev_metrics) if prev_metrics else 0
    growth_percent = safe_percent_change(total_views, prev_total)
    
    # Moving averages
    all_sorted = sorted(metrics, key=lambda m: m.metric_date)
    all_views = [m.views for m in all_sorted]
    
    seven_day_avg = round(statistics.mean(all_views[-7:]), 0) if len(all_views) >= 7 else round(statistics.mean(all_views), 0)
    thirty_day_avg = round(statistics.mean(all_views[-30:]), 0) if len(all_views) >= 30 else round(statistics.mean(all_views), 0)
    
    # Identify spikes (days with views > mean + 1.5 * std_dev)
    spikes = []
    if len(views_list) >= 7:
        mean_v = statistics.mean(views_list)
        std_v = calculate_std_dev(views_list)
        if std_v > 0:
            for i, (v, d) in enumerate(zip(views_list, dates_list)):
                z = calculate_z_score(v, mean_v, std_v)
                if abs(z) > 1.5:
                    # Compare to 7-day window average before the spike
                    window_start = max(0, i - 7)
                    window_avg = statistics.mean(views_list[window_start:i]) if i > window_start else mean_v
                    spike_change = safe_percent_change(v, window_avg)
                    direction = "increased" if z > 0 else "decreased"
                    spikes.append({
                        "date": d,
                        "views": v,
                        "z_score": z,
                        "change_percent": spike_change,
                        "message": f"Views {direction} {abs(spike_change):.0f}% on {d.strftime('%d %B')} compared with the previous 7-day average.",
                    })
    
    return {
        "has_data": True,
        "total_views": total_views,
        "avg_daily_views": int(avg_views),
        "median_daily_views": int(median_views),
        "highest_daily_views": max_views,
        "lowest_daily_views": min_views,
        "best_view_day": max_date,
        "worst_view_day": min_date,
        "seven_day_avg": int(seven_day_avg),
        "thirty_day_avg": int(thirty_day_avg),
        "growth_percent": growth_percent,
        "growth_label": get_trend_label(growth_percent),
        "previous_total": prev_total,
        "spikes": spikes,
        "daily_views": [{"date": d.isoformat(), "views": v} for d, v in zip(dates_list, views_list)],
    }


# ─── Engagement Analysis ────────────────────────────────────────────────────

def calculate_engagement_rate(
    metrics: List[DailyMetric],
    start_date: date,
    end_date: date,
) -> Dict[str, Any]:
    """Calculate engagement metrics for a date range.
    
    Formula:
        Engagement Rate = (Likes + Comments + Shares) / Views × 100
        
    Also calculates per-view ratios for likes, comments, and shares.
    """
    period = [m for m in metrics if start_date <= m.metric_date <= end_date]
    
    if not period:
        return {"has_data": False}
    
    total_views = sum(m.views for m in period)
    total_likes = sum(m.likes for m in period)
    total_comments = sum(m.comments for m in period)
    total_shares = sum(m.shares for m in period)
    
    engagement_rate = 0.0
    likes_per_view = 0.0
    comments_per_view = 0.0
    shares_per_view = 0.0
    
    if total_views > 0:
        engagement_rate = round(((total_likes + total_comments + total_shares) / total_views) * 100, 2)
        likes_per_view = round(total_likes / total_views, 4)
        comments_per_view = round(total_comments / total_views, 4)
        shares_per_view = round(total_shares / total_views, 4)
    
    # Previous period comparison
    prev_start, prev_end = get_previous_period(start_date, end_date)
    prev_metrics = [m for m in metrics if prev_start <= m.metric_date <= prev_end]
    
    prev_engagement = 0.0
    if prev_metrics:
        pv = sum(m.views for m in prev_metrics)
        if pv > 0:
            prev_engagement = ((sum(m.likes for m in prev_metrics) + 
                               sum(m.comments for m in prev_metrics) + 
                               sum(m.shares for m in prev_metrics)) / pv) * 100
    
    engagement_change = safe_percent_change(engagement_rate, prev_engagement)
    
    # Daily breakdown for charts
    daily_engagement = []
    daily_likes = []
    daily_comments = []
    daily_shares = []
    
    for m in sorted(period, key=lambda x: x.metric_date):
        d = m.metric_date.isoformat()
        daily_engagement.append({"date": d, "value": m.engagement_rate})
        daily_likes.append({"date": d, "value": m.likes})
        daily_comments.append({"date": d, "value": m.comments})
        daily_shares.append({"date": d, "value": m.shares})
    
    return {
        "has_data": True,
        "engagement_rate": engagement_rate,
        "engagement_change": engagement_change,
        "engagement_trend": get_trend_label(engagement_change),
        "total_likes": total_likes,
        "total_comments": total_comments,
        "total_shares": total_shares,
        "likes_per_view": likes_per_view,
        "comments_per_view": comments_per_view,
        "shares_per_view": shares_per_view,
        "daily_engagement": daily_engagement,
        "daily_likes": daily_likes,
        "daily_comments": daily_comments,
        "daily_shares": daily_shares,
    }


# ─── Follower Analysis ──────────────────────────────────────────────────────

def calculate_follower_growth(
    metrics: List[DailyMetric],
    start_date: date,
    end_date: date,
) -> Dict[str, Any]:
    """Calculate follower growth analytics.
    
    Formula:
        Net Growth = New Followers - Lost Followers
        Growth % = (Net Growth / Start Followers) × 100
    """
    period = sorted(
        [m for m in metrics if start_date <= m.metric_date <= end_date],
        key=lambda m: m.metric_date,
    )
    
    if not period:
        return {"has_data": False}
    
    current_followers = period[-1].followers
    start_followers = period[0].followers
    total_new = sum(m.new_followers for m in period)
    total_lost = sum(m.lost_followers for m in period)
    net_growth = total_new - total_lost
    growth_percent = safe_percent_change(current_followers, start_followers)
    
    # Previous period
    prev_start, prev_end = get_previous_period(start_date, end_date)
    prev_metrics = sorted(
        [m for m in metrics if prev_start <= m.metric_date <= prev_end],
        key=lambda m: m.metric_date,
    )
    
    prev_net_growth = 0
    if prev_metrics:
        prev_net_growth = sum(m.new_followers for m in prev_metrics) - sum(m.lost_followers for m in prev_metrics)
    
    growth_change = safe_percent_change(net_growth, prev_net_growth) if prev_net_growth != 0 else 0.0
    
    # Daily/weekly/monthly charts
    daily_followers = [
        {"date": m.metric_date.isoformat(), "followers": m.followers, "new": m.new_followers, "lost": m.lost_followers}
        for m in period
    ]
    
    # Weekly aggregation
    weekly_data = defaultdict(lambda: {"followers": 0, "new": 0, "lost": 0, "count": 0})
    for m in period:
        week_key = m.metric_date.isocalendar()[1]
        year_key = m.metric_date.year
        key = f"{year_key}-W{week_key:02d}"
        weekly_data[key]["followers"] = m.followers  # Last value in week
        weekly_data[key]["new"] += m.new_followers
        weekly_data[key]["lost"] += m.lost_followers
        weekly_data[key]["count"] += 1
    
    weekly_followers = [
        {"week": k, "followers": v["followers"], "new": v["new"], "lost": v["lost"]}
        for k, v in sorted(weekly_data.items())
    ]
    
    return {
        "has_data": True,
        "current_followers": current_followers,
        "start_followers": start_followers,
        "new_followers": total_new,
        "lost_followers": total_lost,
        "net_growth": net_growth,
        "growth_percent": growth_percent,
        "growth_change": growth_change,
        "growth_trend": get_trend_label(growth_percent),
        "daily_followers": daily_followers,
        "weekly_followers": weekly_followers,
    }


# ─── Content Performance ────────────────────────────────────────────────────

def calculate_content_performance(
    content_list: List[Content],
) -> Dict[str, Any]:
    """Analyze content performance with transparent scoring.
    
    Performance labels:
    - "Above Average": engagement_rate > average + 0.5 * std_dev
    - "Average": within 0.5 * std_dev of mean
    - "Below Average": engagement_rate < average - 0.5 * std_dev
    """
    if not content_list:
        return {"has_data": False, "items": []}
    
    # Calculate engagement rates
    items = []
    engagement_rates = []
    
    for c in content_list:
        er = c.engagement_rate if hasattr(c, 'engagement_rate') and callable(getattr(c, 'engagement_rate', None)) == False else (
            round(((c.likes + c.comments + c.shares) / c.views) * 100, 2) if c.views > 0 else 0.0
        )
        engagement_rates.append(er)
        items.append({
            "id": c.id,
            "title": c.title or "Untitled",
            "content_type": c.content_type,
            "published_at": c.published_at,
            "views": c.views,
            "likes": c.likes,
            "comments": c.comments,
            "shares": c.shares,
            "engagement_rate": er,
        })
    
    avg_engagement = statistics.mean(engagement_rates) if engagement_rates else 0
    std_engagement = calculate_std_dev(engagement_rates)
    avg_views = statistics.mean([c.views for c in content_list])
    
    # Assign performance labels
    for item in items:
        er = item["engagement_rate"]
        if std_engagement > 0:
            if er > avg_engagement + 0.5 * std_engagement:
                item["performance"] = "Above Average"
            elif er < avg_engagement - 0.5 * std_engagement:
                item["performance"] = "Below Average"
            else:
                item["performance"] = "Average"
        else:
            item["performance"] = "Average"
        
        # Difference from average views
        item["views_diff_percent"] = safe_percent_change(item["views"], avg_views)
    
    return {
        "has_data": True,
        "items": items,
        "avg_engagement": round(avg_engagement, 2),
        "avg_views": int(avg_views),
        "total_content": len(items),
    }


def find_top_content(
    content_list: List[Content],
    sort_by: str = "views",
    limit: int = 10,
) -> List[Dict]:
    """Find top-performing content sorted by a given metric.
    
    Args:
        sort_by: One of 'views', 'likes', 'comments', 'shares', 'engagement'
    """
    if not content_list:
        return []
    
    items = []
    for c in content_list:
        er = round(((c.likes + c.comments + c.shares) / c.views) * 100, 2) if c.views > 0 else 0.0
        items.append({
            "id": c.id,
            "title": c.title or "Untitled",
            "content_type": c.content_type,
            "published_at": c.published_at.isoformat() if c.published_at else None,
            "views": c.views,
            "likes": c.likes,
            "comments": c.comments,
            "shares": c.shares,
            "engagement_rate": er,
        })
    
    sort_key = "engagement_rate" if sort_by == "engagement" else sort_by
    items.sort(key=lambda x: x.get(sort_key, 0), reverse=True)
    
    return items[:limit]


def find_low_performing_content(
    content_list: List[Content],
    limit: int = 10,
) -> List[Dict]:
    """Find content that needs attention (below average performance).
    
    Each item includes how far below average it is and a data-driven note.
    """
    if not content_list:
        return []
    
    avg_views = statistics.mean([c.views for c in content_list])
    avg_engagement_rates = []
    items = []
    
    for c in content_list:
        er = round(((c.likes + c.comments + c.shares) / c.views) * 100, 2) if c.views > 0 else 0.0
        avg_engagement_rates.append(er)
        items.append({
            "id": c.id,
            "title": c.title or "Untitled",
            "content_type": c.content_type,
            "published_at": c.published_at.isoformat() if c.published_at else None,
            "views": c.views,
            "likes": c.likes,
            "comments": c.comments,
            "shares": c.shares,
            "engagement_rate": er,
            "avg_views": int(avg_views),
            "views_diff_percent": safe_percent_change(c.views, avg_views),
        })
    
    avg_er = statistics.mean(avg_engagement_rates) if avg_engagement_rates else 0
    
    # Filter to below-average content
    below_avg = [i for i in items if i["views"] < avg_views]
    below_avg.sort(key=lambda x: x["views"])
    
    for item in below_avg:
        diff = abs(item["views_diff_percent"])
        item["note"] = f"This post received {diff:.0f}% fewer views than the page's average for the selected period."
        
        if item["engagement_rate"] < avg_er * 0.5:
            item["improvement_area"] = "Low engagement - consider testing different hooks or calls-to-action"
        elif item["views"] < avg_views * 0.3:
            item["improvement_area"] = "Very low reach - review posting time and format"
        else:
            item["improvement_area"] = "Moderate underperformance - analyze what differs from top content"
    
    return below_avg[:limit]


# ─── Best Posting Days ───────────────────────────────────────────────────────

def find_best_posting_day(
    content_list: List[Content],
) -> Dict[str, Any]:
    """Analyze historical average views by weekday.
    
    Note: This is historical analysis, not a guarantee of future performance.
    """
    if not content_list:
        return {"has_data": False}
    
    weekday_data = defaultdict(lambda: {"total_views": 0, "total_engagement": 0, "count": 0})
    
    for c in content_list:
        if c.published_at:
            wd = c.published_at.weekday()
            er = ((c.likes + c.comments + c.shares) / c.views * 100) if c.views > 0 else 0
            weekday_data[wd]["total_views"] += c.views
            weekday_data[wd]["total_engagement"] += er
            weekday_data[wd]["count"] += 1
    
    days = []
    for wd in range(7):
        d = weekday_data[wd]
        if d["count"] > 0:
            days.append({
                "day": weekday_name(wd),
                "day_number": wd,
                "posts": d["count"],
                "avg_views": int(d["total_views"] / d["count"]),
                "avg_engagement": round(d["total_engagement"] / d["count"], 2),
            })
        else:
            days.append({
                "day": weekday_name(wd),
                "day_number": wd,
                "posts": 0,
                "avg_views": 0,
                "avg_engagement": 0.0,
            })
    
    best_day = max(days, key=lambda x: x["avg_views"]) if days else None
    
    return {
        "has_data": True,
        "days": days,
        "best_day": best_day["day"] if best_day and best_day["posts"] > 0 else "Insufficient data",
        "note": "This is historical analysis based on available data. Past performance does not guarantee future results.",
    }


# ─── Best Posting Time ──────────────────────────────────────────────────────

def find_best_posting_time(
    content_list: List[Content],
    min_posts_per_hour: int = 3,
) -> Dict[str, Any]:
    """Analyze performance by posting hour.
    
    Args:
        min_posts_per_hour: Minimum posts at a given hour to consider the data reliable.
    """
    if not content_list:
        return {"has_data": False}
    
    hour_data = defaultdict(lambda: {"total_views": 0, "total_engagement": 0, "count": 0})
    
    for c in content_list:
        if c.published_at:
            hour = c.published_at.hour
            er = ((c.likes + c.comments + c.shares) / c.views * 100) if c.views > 0 else 0
            hour_data[hour]["total_views"] += c.views
            hour_data[hour]["total_engagement"] += er
            hour_data[hour]["count"] += 1
    
    hours = []
    heatmap = [[0] * 24 for _ in range(7)]  # 7 days × 24 hours
    
    for h in range(24):
        d = hour_data[h]
        if d["count"] > 0:
            hours.append({
                "hour": h,
                "label": f"{h:02d}:00",
                "posts": d["count"],
                "avg_views": int(d["total_views"] / d["count"]),
                "avg_engagement": round(d["total_engagement"] / d["count"], 2),
                "reliable": d["count"] >= min_posts_per_hour,
            })
        else:
            hours.append({
                "hour": h,
                "label": f"{h:02d}:00",
                "posts": 0,
                "avg_views": 0,
                "avg_engagement": 0.0,
                "reliable": False,
            })
    
    # Build heatmap data
    for c in content_list:
        if c.published_at:
            wd = c.published_at.weekday()
            h = c.published_at.hour
            heatmap[wd][h] += c.views
    
    reliable_hours = [h for h in hours if h["reliable"]]
    
    if not reliable_hours:
        return {
            "has_data": True,
            "hours": hours,
            "heatmap": heatmap,
            "best_time": None,
            "note": "Not enough historical data to confidently identify a posting-time pattern.",
            "insufficient_data": True,
        }
    
    best_hour = max(reliable_hours, key=lambda x: x["avg_views"])
    
    return {
        "has_data": True,
        "hours": hours,
        "heatmap": heatmap,
        "best_time": best_hour["label"],
        "best_hour_data": best_hour,
        "note": "This is based on historical performance. Results may vary.",
        "insufficient_data": False,
    }


# ─── Content Type Analysis ───────────────────────────────────────────────────

def analyze_content_types(content_list: List[Content]) -> Dict[str, Any]:
    """Compare performance across content types."""
    if not content_list:
        return {"has_data": False}
    
    type_data = defaultdict(lambda: {
        "count": 0, "total_views": 0, "total_likes": 0,
        "total_shares": 0, "total_comments": 0,
    })
    
    for c in content_list:
        td = type_data[c.content_type]
        td["count"] += 1
        td["total_views"] += c.views
        td["total_likes"] += c.likes
        td["total_shares"] += c.shares
        td["total_comments"] += c.comments
    
    types = []
    for ct, d in type_data.items():
        n = d["count"]
        total_engagement = d["total_likes"] + d["total_comments"] + d["total_shares"]
        types.append({
            "type": ct.capitalize(),
            "count": n,
            "avg_views": int(d["total_views"] / n),
            "avg_likes": int(d["total_likes"] / n),
            "avg_shares": int(d["total_shares"] / n),
            "avg_comments": int(d["total_comments"] / n),
            "engagement": round((total_engagement / d["total_views"]) * 100, 2) if d["total_views"] > 0 else 0,
        })
    
    types.sort(key=lambda x: x["avg_views"], reverse=True)
    
    return {"has_data": True, "types": types}


# ─── Anomaly Detection ──────────────────────────────────────────────────────

def detect_anomalies(
    metrics: List[DailyMetric],
    z_threshold: float = 2.0,
) -> List[Dict]:
    """Detect statistical anomalies in daily metrics using z-scores.
    
    Method:
    1. Calculate mean and standard deviation for each metric
    2. Flag days where z-score exceeds threshold
    3. Label as anomaly (NOT as an explanation of why)
    
    Args:
        z_threshold: Z-score threshold to flag as anomaly (default 2.0)
    """
    if len(metrics) < 7:
        return []
    
    sorted_m = sorted(metrics, key=lambda m: m.metric_date)
    anomalies = []
    
    fields = [
        ("views", "Views"),
        ("followers", "Followers"),
        ("likes", "Likes"),
        ("comments", "Comments"),
        ("shares", "Shares"),
        ("engagement_rate", "Engagement Rate"),
    ]
    
    for field, label in fields:
        values = [getattr(m, field) for m in sorted_m]
        if len(values) < 2:
            continue
        
        mean_val = statistics.mean(values)
        std_val = calculate_std_dev(values)
        
        if std_val == 0:
            continue
        
        for m in sorted_m:
            val = getattr(m, field)
            z = calculate_z_score(val, mean_val, std_val)
            
            if abs(z) >= z_threshold:
                direction = "spike" if z > 0 else "drop"
                anomalies.append({
                    "date": m.metric_date.isoformat(),
                    "metric": label,
                    "value": val,
                    "mean": round(mean_val, 2),
                    "z_score": z,
                    "type": direction,
                    "severity": "high" if abs(z) >= 3 else "medium",
                    "message": f"Statistical anomaly: {label} showed an unusual {direction} on {m.metric_date.strftime('%d %B')} (z-score: {z:.1f}). This is a statistical observation, not an explanation of cause.",
                })
    
    # Sort by absolute z-score descending
    anomalies.sort(key=lambda x: abs(x["z_score"]), reverse=True)
    return anomalies


# ─── Performance Score ───────────────────────────────────────────────────────

def calculate_performance_score(
    metrics: List[DailyMetric],
    content_list: List[Content],
    start_date: date,
    end_date: date,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Calculate a transparent performance score from 0-100.
    
    Components (default weights):
    - View Growth (25%): Based on view trend vs previous period
    - Engagement (25%): Based on engagement rate relative to benchmarks
    - Follower Growth (20%): Based on net follower change
    - Consistency (15%): Based on regularity of posting
    - Share Rate (15%): Based on shares per view
    
    Each component is scored 0-100 and weighted.
    Formula is fully transparent and weights are configurable.
    """
    if not weights:
        weights = {
            "view_growth": 0.25,
            "engagement": 0.25,
            "follower_growth": 0.20,
            "consistency": 0.15,
            "share_rate": 0.15,
        }
    
    period = [m for m in metrics if start_date <= m.metric_date <= end_date]
    
    if not period:
        return {"has_data": False}
    
    # ── View Growth Score (0-100)
    view_data = calculate_view_growth(metrics, start_date, end_date)
    growth = view_data.get("growth_percent", 0)
    # Map growth: -50% → 0, 0% → 50, +50% → 100
    view_score = min(100, max(0, int(50 + growth)))
    
    # ── Engagement Score (0-100)
    eng_data = calculate_engagement_rate(metrics, start_date, end_date)
    eng_rate = eng_data.get("engagement_rate", 0)
    # Map: 0% → 0, 5% → 50, 10%+ → 100
    engagement_score = min(100, max(0, int(eng_rate * 10)))
    
    # ── Follower Growth Score (0-100)
    fol_data = calculate_follower_growth(metrics, start_date, end_date)
    fol_growth = fol_data.get("growth_percent", 0)
    follower_score = min(100, max(0, int(50 + fol_growth * 2)))
    
    # ── Consistency Score (0-100)
    days_in_period = (end_date - start_date).days + 1
    days_with_posts = sum(1 for m in period if m.posts > 0)
    consistency_score = min(100, int((days_with_posts / max(1, days_in_period)) * 100))
    
    # ── Share Rate Score (0-100)
    total_views = sum(m.views for m in period)
    total_shares = sum(m.shares for m in period)
    share_rate = (total_shares / total_views * 100) if total_views > 0 else 0
    share_score = min(100, max(0, int(share_rate * 20)))
    
    # Weighted total
    total_score = int(
        view_score * weights["view_growth"] +
        engagement_score * weights["engagement"] +
        follower_score * weights["follower_growth"] +
        consistency_score * weights["consistency"] +
        share_score * weights["share_rate"]
    )
    
    return {
        "has_data": True,
        "total_score": total_score,
        "components": {
            "view_growth": {"score": view_score, "weight": weights["view_growth"], "label": "View Growth"},
            "engagement": {"score": engagement_score, "weight": weights["engagement"], "label": "Engagement"},
            "follower_growth": {"score": follower_score, "weight": weights["follower_growth"], "label": "Follower Growth"},
            "consistency": {"score": consistency_score, "weight": weights["consistency"], "label": "Consistency"},
            "share_rate": {"score": share_score, "weight": weights["share_rate"], "label": "Share Rate"},
        },
        "formula": "Score = Σ(component_score × weight). Each component mapped 0-100 based on documented thresholds.",
    }


# ─── Report Generators ──────────────────────────────────────────────────────

def generate_daily_summary(
    metrics: List[DailyMetric],
    content_list: List[Content],
    target_date: date,
) -> Dict[str, Any]:
    """Generate a daily performance summary."""
    growth = calculate_daily_growth(metrics)
    
    # Find content published today
    today_content = [c for c in content_list if c.published_at and c.published_at.date() == target_date]
    
    return {
        "date": target_date.isoformat(),
        "growth": growth,
        "content_published": len(today_content),
        "today_content": [
            {"title": c.title, "type": c.content_type, "views": c.views}
            for c in today_content
        ],
    }


def generate_weekly_summary(
    metrics: List[DailyMetric],
    content_list: List[Content],
    end_date: date,
) -> Dict[str, Any]:
    """Generate a weekly performance report."""
    start_date = end_date - timedelta(days=6)
    
    view_data = calculate_view_growth(metrics, start_date, end_date)
    eng_data = calculate_engagement_rate(metrics, start_date, end_date)
    fol_data = calculate_follower_growth(metrics, start_date, end_date)
    
    period_content = [
        c for c in content_list
        if c.published_at and start_date <= c.published_at.date() <= end_date
    ]
    
    top = find_top_content(period_content, "views", 5)
    low = find_low_performing_content(period_content, 3)
    best_day = find_best_posting_day(period_content)
    
    # Executive summary
    total_views = view_data.get("total_views", 0)
    growth_pct = view_data.get("growth_percent", 0)
    direction = "increase" if growth_pct >= 0 else "decrease"
    
    executive_summary = (
        f"During the last 7 days, the page generated {format_number(total_views)} views, "
        f"representing a {abs(growth_pct):.1f}% {direction} compared with the previous 7-day period."
    )
    
    return {
        "period": f"{start_date.isoformat()} to {end_date.isoformat()}",
        "executive_summary": executive_summary,
        "views": view_data,
        "engagement": eng_data,
        "followers": fol_data,
        "posts_published": len(period_content),
        "top_content": top,
        "low_content": low,
        "best_day": best_day,
    }


def generate_monthly_summary(
    metrics: List[DailyMetric],
    content_list: List[Content],
    end_date: date,
) -> Dict[str, Any]:
    """Generate a monthly performance report."""
    start_date = end_date - timedelta(days=29)
    
    view_data = calculate_view_growth(metrics, start_date, end_date)
    eng_data = calculate_engagement_rate(metrics, start_date, end_date)
    fol_data = calculate_follower_growth(metrics, start_date, end_date)
    content_types = analyze_content_types(content_list)
    
    period_content = [
        c for c in content_list
        if c.published_at and start_date <= c.published_at.date() <= end_date
    ]
    
    top = find_top_content(period_content, "views", 10)
    low = find_low_performing_content(period_content, 5)
    best_day = find_best_posting_day(period_content)
    best_time = find_best_posting_time(period_content)
    score = calculate_performance_score(metrics, content_list, start_date, end_date)
    
    # Week-by-week breakdown
    weeks = []
    for w in range(4):
        w_start = start_date + timedelta(days=w * 7)
        w_end = min(w_start + timedelta(days=6), end_date)
        w_metrics = [m for m in metrics if w_start <= m.metric_date <= w_end]
        weeks.append({
            "week": w + 1,
            "period": f"{w_start.strftime('%d %b')} - {w_end.strftime('%d %b')}",
            "views": sum(m.views for m in w_metrics),
            "engagement": round(statistics.mean([m.engagement_rate for m in w_metrics]), 2) if w_metrics else 0,
            "new_followers": sum(m.new_followers for m in w_metrics),
        })
    
    total_views = view_data.get("total_views", 0)
    growth_pct = view_data.get("growth_percent", 0)
    
    return {
        "period": f"{start_date.isoformat()} to {end_date.isoformat()}",
        "executive_summary": (
            f"Monthly overview: {format_number(total_views)} total views with "
            f"{growth_pct:+.1f}% change vs previous month."
        ),
        "views": view_data,
        "engagement": eng_data,
        "followers": fol_data,
        "content_types": content_types,
        "posts_published": len(period_content),
        "top_content": top,
        "low_content": low,
        "best_day": best_day,
        "best_time": best_time,
        "performance_score": score,
        "weekly_breakdown": weeks,
    }


# ─── Alerts ──────────────────────────────────────────────────────────────────

def generate_alerts(
    metrics: List[DailyMetric],
    start_date: date,
    end_date: date,
    thresholds: Optional[Dict[str, float]] = None,
) -> List[Dict]:
    """Generate alerts based on configurable thresholds.
    
    Default thresholds:
    - view_increase: 25% (positive alert)
    - view_decrease: 20% (warning)
    - engagement_low: 3% (engagement alert)
    - follower_drop: 10% (follower alert)
    """
    if not thresholds:
        thresholds = {
            "view_increase": 25.0,
            "view_decrease": 20.0,
            "engagement_low": 3.0,
            "follower_drop": 10.0,
        }
    
    alerts = []
    view_data = calculate_view_growth(metrics, start_date, end_date)
    eng_data = calculate_engagement_rate(metrics, start_date, end_date)
    fol_data = calculate_follower_growth(metrics, start_date, end_date)
    
    if view_data.get("has_data"):
        growth = view_data.get("growth_percent", 0)
        if growth > thresholds["view_increase"]:
            alerts.append({
                "type": "positive",
                "icon": "🎉",
                "title": "Views Increasing",
                "message": f"Views increased by {growth:.1f}% compared with the previous period's average.",
            })
        elif growth < -thresholds["view_decrease"]:
            alerts.append({
                "type": "warning",
                "icon": "⚠️",
                "title": "Views Decreasing",
                "message": f"Views decreased by {abs(growth):.1f}% compared with the previous period.",
            })
    
    if eng_data.get("has_data"):
        er = eng_data.get("engagement_rate", 0)
        if er < thresholds["engagement_low"]:
            alerts.append({
                "type": "warning",
                "icon": "📉",
                "title": "Low Engagement",
                "message": f"Engagement rate is {er:.2f}%, below your {thresholds['engagement_low']}% threshold.",
            })
        eng_change = eng_data.get("engagement_change", 0)
        if eng_change < -15:
            alerts.append({
                "type": "warning",
                "icon": "💬",
                "title": "Engagement Declining",
                "message": f"Engagement decreased by {abs(eng_change):.1f}% compared with the previous period.",
            })
    
    if fol_data.get("has_data"):
        fol_growth = fol_data.get("growth_percent", 0)
        if fol_growth < -thresholds["follower_drop"]:
            alerts.append({
                "type": "warning",
                "icon": "👥",
                "title": "Follower Growth Slowing",
                "message": f"Follower growth is {fol_growth:.1f}% compared with the previous period.",
            })
        elif fol_data.get("net_growth", 0) > 0:
            alerts.append({
                "type": "positive",
                "icon": "✨",
                "title": "Growing Audience",
                "message": f"Net gain of {format_number(fol_data['net_growth'])} followers during this period.",
            })
    
    return alerts


# ─── Health Summary ──────────────────────────────────────────────────────────

def generate_health_summary(
    metrics: List[DailyMetric],
    content_list: List[Content],
    start_date: date,
    end_date: date,
) -> Dict[str, Any]:
    """Generate the PAGE HEALTH SUMMARY for the dashboard bottom section."""
    view_data = calculate_view_growth(metrics, start_date, end_date)
    eng_data = calculate_engagement_rate(metrics, start_date, end_date)
    fol_data = calculate_follower_growth(metrics, start_date, end_date)
    content_perf = calculate_content_performance(content_list)
    
    # Determine status for each area
    views_status = get_trend_label(view_data.get("growth_percent", 0)) if view_data.get("has_data") else "No Data"
    followers_status = get_trend_label(fol_data.get("growth_percent", 0)) if fol_data.get("has_data") else "No Data"
    engagement_status = get_trend_label(eng_data.get("engagement_change", 0)) if eng_data.get("has_data") else "No Data"
    
    # Content performance label
    if content_perf.get("has_data"):
        avg_eng = content_perf.get("avg_engagement", 0)
        if avg_eng > 8:
            content_status = "Above Average"
        elif avg_eng > 4:
            content_status = "Average"
        else:
            content_status = "Below Average"
    else:
        content_status = "No Data"
    
    return {
        "views": views_status,
        "followers": followers_status,
        "engagement": engagement_status,
        "content_performance": content_status,
    }
