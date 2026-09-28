"""Utility helper functions."""

from datetime import date, timedelta, datetime
from typing import List, Optional, Tuple
import statistics


def safe_percent_change(current: float, previous: float) -> float:
    """Calculate percentage change safely, handling zero division.
    
    Formula: ((current - previous) / previous) * 100
    Returns 0.0 if previous is 0.
    """
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100, 2)


def format_number(n: int) -> str:
    """Format a number with commas for display (e.g., 125,450)."""
    return f"{n:,}"


def get_date_range(period: str, reference_date: Optional[date] = None) -> Tuple[date, date]:
    """Get start and end dates for a named period.
    
    Args:
        period: One of 'today', 'yesterday', '7days', '30days', '90days',
                'this_month', 'last_month'
        reference_date: Reference date (defaults to today)
    
    Returns:
        Tuple of (start_date, end_date)
    """
    ref = reference_date or date.today()
    
    if period == "today":
        return ref, ref
    elif period == "yesterday":
        yesterday = ref - timedelta(days=1)
        return yesterday, yesterday
    elif period == "7days":
        return ref - timedelta(days=6), ref
    elif period == "30days":
        return ref - timedelta(days=29), ref
    elif period == "90days":
        return ref - timedelta(days=89), ref
    elif period == "this_month":
        start = ref.replace(day=1)
        return start, ref
    elif period == "last_month":
        first_of_this_month = ref.replace(day=1)
        end = first_of_this_month - timedelta(days=1)
        start = end.replace(day=1)
        return start, end
    else:
        # Default to last 30 days
        return ref - timedelta(days=29), ref


def get_previous_period(start_date: date, end_date: date) -> Tuple[date, date]:
    """Get the equivalent previous period for comparison.
    
    If selected period is 7 days, previous period is the 7 days before that.
    """
    period_length = (end_date - start_date).days + 1
    prev_end = start_date - timedelta(days=1)
    prev_start = prev_end - timedelta(days=period_length - 1)
    return prev_start, prev_end


def get_trend_label(change_percent: float) -> str:
    """Get a human-readable trend label from a percentage change."""
    if change_percent > 5:
        return "Increasing"
    elif change_percent < -5:
        return "Decreasing"
    else:
        return "Stable"


def get_change_direction(change_percent: float) -> str:
    """Get direction string for KPI cards."""
    if change_percent > 0:
        return "up"
    elif change_percent < 0:
        return "down"
    return "stable"


def calculate_median(values: List[float]) -> float:
    """Calculate median value from a list, handling empty lists."""
    if not values:
        return 0.0
    return round(statistics.median(values), 2)


def calculate_std_dev(values: List[float]) -> float:
    """Calculate standard deviation, handling edge cases."""
    if len(values) < 2:
        return 0.0
    return round(statistics.stdev(values), 2)


def calculate_z_score(value: float, mean: float, std_dev: float) -> float:
    """Calculate z-score for anomaly detection.
    
    A z-score > 2 or < -2 typically indicates an anomaly.
    """
    if std_dev == 0:
        return 0.0
    return round((value - mean) / std_dev, 2)


def weekday_name(day_number: int) -> str:
    """Convert weekday number (0=Monday) to name."""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return days[day_number] if 0 <= day_number <= 6 else "Unknown"


def hour_label(hour: int) -> str:
    """Convert hour (0-23) to readable label."""
    if hour == 0:
        return "12:00 AM"
    elif hour < 12:
        return f"{hour}:00 AM"
    elif hour == 12:
        return "12:00 PM"
    else:
        return f"{hour-12}:00 PM"
