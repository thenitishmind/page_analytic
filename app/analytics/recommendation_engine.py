"""Rule-based Recommendation Engine.

Generates actionable recommendations based on calculated metrics.
Each recommendation is derived from available data — no invented claims.

Design:
- Rules are explicit if/else conditions on real metrics
- Recommendations are categorized: performance, content, engagement, growth, action
- Priority: 1 (highest) to 5 (lowest)
- A future LLM integration can consume these metrics to produce natural-language summaries
"""

from datetime import date, timedelta
from typing import List, Dict, Any

from app.analytics.analytics_engine import (
    calculate_daily_growth,
    calculate_view_growth,
    calculate_engagement_rate,
    calculate_follower_growth,
    calculate_content_performance,
    find_top_content,
    find_best_posting_day,
    find_best_posting_time,
    analyze_content_types,
)
from app.models.models import DailyMetric, Content
from app.utils.helpers import format_number


def generate_recommendations(
    metrics: List[DailyMetric],
    content_list: List[Content],
    start_date: date,
    end_date: date,
) -> List[Dict[str, Any]]:
    """Generate data-driven recommendations.
    
    Returns a list of recommendation dicts, each with:
    - category: str (performance, content, engagement, growth, action)
    - recommendation: str (the advice)
    - priority: int (1-5, 1=highest)
    - data_basis: str (what data supports this)
    """
    recs = []
    
    view_data = calculate_view_growth(metrics, start_date, end_date)
    eng_data = calculate_engagement_rate(metrics, start_date, end_date)
    fol_data = calculate_follower_growth(metrics, start_date, end_date)
    content_perf = calculate_content_performance(content_list)
    type_data = analyze_content_types(content_list)
    best_day_data = find_best_posting_day(content_list)
    best_time_data = find_best_posting_time(content_list)
    
    # ── View Growth Recommendations ──
    if view_data.get("has_data"):
        growth = view_data.get("growth_percent", 0)
        
        if growth > 20:
            recs.append({
                "category": "performance",
                "recommendation": (
                    f"Views are increasing ({growth:+.1f}%). "
                    "Analyze your recent high-performing content and test related topics."
                ),
                "priority": 2,
                "data_basis": f"View growth: {growth:+.1f}% vs previous period",
            })
        elif growth < -20:
            recs.append({
                "category": "performance",
                "recommendation": (
                    f"Views have decreased ({growth:.1f}%). "
                    "Review recent content changes and consider returning to formats that historically performed well."
                ),
                "priority": 1,
                "data_basis": f"View decline: {growth:.1f}% vs previous period",
            })
        elif -5 <= growth <= 5:
            recs.append({
                "category": "performance",
                "recommendation": (
                    "Views are stable. Consider testing new content formats or posting times "
                    "to find growth opportunities."
                ),
                "priority": 3,
                "data_basis": f"View growth: {growth:+.1f}% (within ±5% range)",
            })
    
    # ── Engagement Recommendations ──
    if eng_data.get("has_data"):
        er = eng_data.get("engagement_rate", 0)
        eng_change = eng_data.get("engagement_change", 0)
        
        if eng_change < -15:
            recs.append({
                "category": "engagement",
                "recommendation": (
                    f"Engagement has decreased ({eng_change:.1f}%). "
                    "Review recent content and test stronger calls-to-action."
                ),
                "priority": 1,
                "data_basis": f"Engagement change: {eng_change:.1f}%",
            })
        elif er > 8:
            recs.append({
                "category": "engagement",
                "recommendation": (
                    f"Engagement rate is strong at {er:.2f}%. "
                    "Continue the current content approach and experiment with variations."
                ),
                "priority": 3,
                "data_basis": f"Engagement rate: {er:.2f}%",
            })
        elif er < 3:
            recs.append({
                "category": "engagement",
                "recommendation": (
                    f"Engagement rate is {er:.2f}%, which is below typical benchmarks. "
                    "Try asking questions, using polls, or creating more interactive content."
                ),
                "priority": 2,
                "data_basis": f"Engagement rate: {er:.2f}%",
            })
        
        # Check shares specifically
        shares_per_view = eng_data.get("shares_per_view", 0)
        if shares_per_view < 0.01:
            recs.append({
                "category": "engagement",
                "recommendation": (
                    "Share rate is low. Consider creating more shareable content "
                    "such as infographics, tips lists, or relatable posts."
                ),
                "priority": 3,
                "data_basis": f"Shares per view: {shares_per_view:.4f}",
            })
    
    # ── Follower Recommendations ──
    if fol_data.get("has_data"):
        net = fol_data.get("net_growth", 0)
        lost = fol_data.get("lost_followers", 0)
        new = fol_data.get("new_followers", 0)
        
        if lost > new * 0.3:
            recs.append({
                "category": "growth",
                "recommendation": (
                    f"Lost {format_number(lost)} followers during this period. "
                    "Review if recent content aligns with your audience's expectations."
                ),
                "priority": 2,
                "data_basis": f"Lost: {lost}, New: {new}",
            })
        
        if net > 0:
            recs.append({
                "category": "growth",
                "recommendation": (
                    f"Net gain of {format_number(net)} followers. "
                    "Maintain posting consistency to sustain growth."
                ),
                "priority": 3,
                "data_basis": f"Net follower growth: {net}",
            })
    
    # ── Content Type Recommendations ──
    if type_data.get("has_data"):
        types = type_data.get("types", [])
        if types:
            best_type = types[0]
            recs.append({
                "category": "content",
                "recommendation": (
                    f"{best_type['type']} content has the highest average views "
                    f"({format_number(best_type['avg_views'])} per post). "
                    "Consider increasing the proportion of this format."
                ),
                "priority": 2,
                "data_basis": f"Avg views by type: {best_type['type']} = {best_type['avg_views']}",
            })
    
    # ── Best Posting Day Recommendation ──
    if best_day_data.get("has_data"):
        best_day = best_day_data.get("best_day", "")
        if best_day and best_day != "Insufficient data":
            recs.append({
                "category": "action",
                "recommendation": (
                    f"Historically, {best_day} has shown the highest average views. "
                    "Prioritize publishing your best content on this day."
                ),
                "priority": 3,
                "data_basis": f"Best performing day (historical): {best_day}",
            })
    
    # ── Best Posting Time Recommendation ──
    if best_time_data.get("has_data") and not best_time_data.get("insufficient_data"):
        best_time = best_time_data.get("best_time", "")
        if best_time:
            recs.append({
                "category": "action",
                "recommendation": (
                    f"Content posted around {best_time} has historically performed better. "
                    "Test scheduling your posts near this time window."
                ),
                "priority": 3,
                "data_basis": f"Best performing hour (historical): {best_time}",
            })
    
    # Sort by priority
    recs.sort(key=lambda r: r["priority"])
    return recs


def generate_daily_action_plan(
    metrics: List[DailyMetric],
    content_list: List[Content],
    target_date: date,
) -> Dict[str, Any]:
    """Generate a dynamic daily action plan based on analytics.
    
    The plan is structured into Morning, Content, Engagement, and Evening sections.
    Actions are informed by actual data patterns.
    """
    # Get recent data for context
    week_ago = target_date - timedelta(days=7)
    recent_metrics = [m for m in metrics if week_ago <= m.metric_date <= target_date]
    
    growth = calculate_daily_growth(metrics)
    best_type_data = analyze_content_types(content_list)
    
    # Determine best content type
    best_type = "your historically strong format"
    if best_type_data.get("has_data") and best_type_data["types"]:
        best_type = best_type_data["types"][0]["type"].lower() + " content"
    
    # Check engagement trend
    engagement_action = "Reply to comments and foster discussion"
    if growth.get("engagement_change", 0) < -10:
        engagement_action = "Engagement is declining — focus on responding to comments and asking questions in posts"
    
    # Check views trend
    views_note = ""
    if growth.get("views_change", 0) > 15:
        views_note = "Views are up — analyze what's driving the increase"
    elif growth.get("views_change", 0) < -15:
        views_note = "Views are down — review recent posting times and formats"
    
    plan = {
        "date": target_date.isoformat(),
        "morning": [
            "Review yesterday's analytics",
            "Check new comments and respond",
            f"Check follower growth ({format_number(growth.get('new_followers', 0))} new yesterday)" if growth.get("has_data") else "Check follower growth",
            views_note or "Review view trends for the past 7 days",
        ],
        "content": [
            "Prepare today's content",
            f"Use {best_type} (historically strongest format)",
            "Test a new hook or opening",
            "Include a clear call-to-action",
        ],
        "engagement": [
            engagement_action,
            "Review and share top-performing content insights",
            "Identify frequently asked questions from comments",
            "Engage with your community's content",
        ],
        "evening": [
            "Check today's view count",
            "Compare today's performance against yesterday",
            "Note what worked and what didn't",
            "Plan tomorrow's content topic",
        ],
    }
    
    # Filter out empty items
    for section in plan:
        if isinstance(plan[section], list):
            plan[section] = [item for item in plan[section] if item]
    
    return plan


def generate_today_performance_summary(
    metrics: List[DailyMetric],
    content_list: List[Content],
    start_date: date,
    end_date: date,
) -> Dict[str, Any]:
    """Generate the 'Today's Performance' narrative section for the dashboard.
    
    Returns structured sections: performance, what_is_working, what_needs_attention, what_to_do.
    """
    growth = calculate_daily_growth(metrics)
    view_data = calculate_view_growth(metrics, start_date, end_date)
    eng_data = calculate_engagement_rate(metrics, start_date, end_date)
    type_data = analyze_content_types(content_list)
    
    result = {
        "performance": "",
        "what_is_working": [],
        "what_needs_attention": [],
        "what_to_do": [],
    }
    
    # Performance narrative
    if growth.get("has_data"):
        views = growth.get("views", 0)
        change = growth.get("views_change", 0)
        direction = "higher" if change > 0 else "lower"
        result["performance"] = (
            f"Your page received {format_number(views)} views today, "
            f"which is {abs(change):.1f}% {direction} than yesterday."
        )
    
    # What is working
    if type_data.get("has_data") and type_data["types"]:
        best = type_data["types"][0]
        result["what_is_working"].append(
            f"{best['type']} content generated the highest average views "
            f"({format_number(best['avg_views'])} avg) during the selected period."
        )
    
    if eng_data.get("has_data") and eng_data.get("engagement_change", 0) > 5:
        result["what_is_working"].append(
            f"Engagement rate is trending up ({eng_data['engagement_change']:+.1f}%)."
        )
    
    # What needs attention
    if eng_data.get("has_data") and eng_data.get("engagement_change", 0) < -5:
        result["what_needs_attention"].append(
            f"Engagement decreased ({eng_data['engagement_change']:.1f}%) compared with the previous period."
        )
    
    if view_data.get("has_data") and view_data.get("growth_percent", 0) < -10:
        result["what_needs_attention"].append(
            f"Views decreased {abs(view_data['growth_percent']):.1f}% vs the previous period."
        )
    
    # What to do today
    result["what_to_do"] = [
        "Publish one piece of content using a historically strong format.",
        "Review the top-performing content from the previous 7 days.",
        "Respond to recent comments to boost engagement.",
        "Reuse successful topics with a new presentation or angle.",
        "Test a different opening hook or thumbnail.",
    ]
    
    return result


def generate_priorities(
    metrics: List[DailyMetric],
    content_list: List[Content],
    start_date: date,
    end_date: date,
) -> List[str]:
    """Generate TODAY'S PRIORITIES based on actual analytics.
    
    Returns a list of 5 priority strings.
    """
    priorities = []
    
    growth = calculate_daily_growth(metrics)
    view_data = calculate_view_growth(metrics, start_date, end_date)
    eng_data = calculate_engagement_rate(metrics, start_date, end_date)
    fol_data = calculate_follower_growth(metrics, start_date, end_date)
    
    # Priority 1: Address biggest issue or capitalize on biggest win
    if view_data.get("has_data"):
        vg = view_data.get("growth_percent", 0)
        if vg < -15:
            priorities.append(f"Address view decline ({vg:.1f}%) — review recent content format and timing")
        elif vg > 20:
            priorities.append(f"Capitalize on view growth ({vg:+.1f}%) — publish follow-up content in the same format")
        else:
            priorities.append("Publish content today to maintain consistency")
    else:
        priorities.append("Start tracking daily metrics for actionable insights")
    
    # Priority 2: Engagement
    if eng_data.get("has_data"):
        if eng_data.get("engagement_change", 0) < -10:
            priorities.append("Boost engagement — add calls-to-action and respond to all comments")
        else:
            priorities.append("Respond to comments from the last 24 hours")
    else:
        priorities.append("Review and respond to audience comments")
    
    # Priority 3: Content
    priorities.append("Prepare tomorrow's content using insights from top performers")
    
    # Priority 4: Follower growth
    if fol_data.get("has_data"):
        net = fol_data.get("net_growth", 0)
        if net < 0:
            priorities.append("Investigate follower loss — review content alignment with audience expectations")
        else:
            priorities.append(f"Continue follower growth strategy (net +{net} this period)")
    else:
        priorities.append("Review follower growth trends")
    
    # Priority 5: Analysis
    priorities.append("Review this week's analytics and note patterns")
    
    return priorities[:5]
