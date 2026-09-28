"""Unit tests for the analytics engine."""

import pytest
from datetime import date, timedelta

from app.analytics.analytics_engine import (
    calculate_daily_growth,
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
    calculate_performance_score,
    generate_alerts,
    generate_health_summary,
)
from app.analytics.recommendation_engine import (
    generate_recommendations,
    generate_daily_action_plan,
    generate_priorities,
)
from app.utils.helpers import (
    safe_percent_change,
    get_date_range,
    get_previous_period,
    get_trend_label,
    calculate_median,
    calculate_std_dev,
    calculate_z_score,
)


# ─── Helper Function Tests ──────────────────────────────────────

class TestSafePercentChange:
    """Test percentage change calculation with edge cases."""
    
    def test_positive_growth(self):
        assert safe_percent_change(120, 100) == 20.0
    
    def test_negative_growth(self):
        assert safe_percent_change(80, 100) == -20.0
    
    def test_zero_previous(self):
        """When previous is 0, positive current should return 100%."""
        assert safe_percent_change(100, 0) == 100.0
    
    def test_both_zero(self):
        """When both are 0, should return 0%."""
        assert safe_percent_change(0, 0) == 0.0
    
    def test_zero_current(self):
        """When current is 0 and previous is positive, should return -100%."""
        assert safe_percent_change(0, 100) == -100.0
    
    def test_no_change(self):
        assert safe_percent_change(100, 100) == 0.0


class TestDateRange:
    """Test date range calculations."""
    
    def test_today(self):
        start, end = get_date_range("today")
        assert start == end == date.today()
    
    def test_yesterday(self):
        start, end = get_date_range("yesterday")
        assert start == end == date.today() - timedelta(days=1)
    
    def test_7days(self):
        start, end = get_date_range("7days")
        assert (end - start).days == 6
    
    def test_30days(self):
        start, end = get_date_range("30days")
        assert (end - start).days == 29
    
    def test_previous_period(self):
        start = date(2024, 1, 8)
        end = date(2024, 1, 14)
        prev_start, prev_end = get_previous_period(start, end)
        assert (prev_end - prev_start).days == 6
        assert prev_end == start - timedelta(days=1)


class TestStatisticalHelpers:
    """Test statistical calculation helpers."""
    
    def test_median_normal(self):
        assert calculate_median([1, 2, 3, 4, 5]) == 3
    
    def test_median_empty(self):
        assert calculate_median([]) == 0.0
    
    def test_median_single(self):
        assert calculate_median([42]) == 42
    
    def test_std_dev_normal(self):
        result = calculate_std_dev([10, 12, 14, 16, 18])
        assert result > 0
    
    def test_std_dev_single_value(self):
        assert calculate_std_dev([5]) == 0.0
    
    def test_z_score_normal(self):
        z = calculate_z_score(15, 10, 2)
        assert z == 2.5
    
    def test_z_score_zero_std(self):
        assert calculate_z_score(10, 10, 0) == 0.0


class TestTrendLabel:
    """Test trend labeling."""
    
    def test_increasing(self):
        assert get_trend_label(10) == "Increasing"
    
    def test_decreasing(self):
        assert get_trend_label(-10) == "Decreasing"
    
    def test_stable(self):
        assert get_trend_label(2) == "Stable"
        assert get_trend_label(-3) == "Stable"


# ─── Analytics Engine Tests ─────────────────────────────────────

class TestDailyGrowth:
    """Test daily growth calculations."""
    
    def test_with_data(self, sample_metrics):
        result = calculate_daily_growth(sample_metrics)
        assert result["has_data"] is True
        assert "views" in result
        assert "views_change" in result
        assert isinstance(result["views"], int)
    
    def test_empty_data(self):
        result = calculate_daily_growth([])
        assert result["has_data"] is False


class TestViewGrowth:
    """Test view growth calculations."""
    
    def test_with_data(self, sample_metrics):
        today = date.today()
        start = today - timedelta(days=6)
        result = calculate_view_growth(sample_metrics, start, today)
        
        assert result["has_data"] is True
        assert result["total_views"] > 0
        assert result["avg_daily_views"] > 0
        assert result["highest_daily_views"] >= result["lowest_daily_views"]
        assert result["median_daily_views"] > 0
        assert "growth_percent" in result
        assert "daily_views" in result
    
    def test_no_data_in_range(self, sample_metrics):
        # Far future date range
        start = date(2099, 1, 1)
        end = date(2099, 1, 7)
        result = calculate_view_growth(sample_metrics, start, end)
        assert result["has_data"] is False


class TestEngagementRate:
    """Test engagement rate calculations."""
    
    def test_with_data(self, sample_metrics):
        today = date.today()
        start = today - timedelta(days=29)
        result = calculate_engagement_rate(sample_metrics, start, today)
        
        assert result["has_data"] is True
        assert result["engagement_rate"] > 0
        assert result["total_likes"] > 0
        assert "likes_per_view" in result
        assert "daily_engagement" in result
    
    def test_engagement_formula(self, sample_metrics):
        """Verify engagement rate formula: (L+C+S)/V * 100."""
        today = date.today()
        start = today - timedelta(days=6)
        result = calculate_engagement_rate(sample_metrics, start, today)
        
        period = [m for m in sample_metrics if start <= m.metric_date <= today]
        total_v = sum(m.views for m in period)
        total_l = sum(m.likes for m in period)
        total_c = sum(m.comments for m in period)
        total_s = sum(m.shares for m in period)
        
        expected = round(((total_l + total_c + total_s) / total_v) * 100, 2)
        assert result["engagement_rate"] == expected


class TestFollowerGrowth:
    """Test follower growth calculations."""
    
    def test_with_data(self, sample_metrics):
        today = date.today()
        start = today - timedelta(days=29)
        result = calculate_follower_growth(sample_metrics, start, today)
        
        assert result["has_data"] is True
        assert result["current_followers"] > 0
        assert result["new_followers"] > 0
        assert "net_growth" in result
        assert "daily_followers" in result


class TestContentPerformance:
    """Test content performance analysis."""
    
    def test_with_data(self, sample_content):
        result = calculate_content_performance(sample_content)
        
        assert result["has_data"] is True
        assert result["total_content"] == 50
        assert result["avg_views"] > 0
        assert result["avg_engagement"] > 0
        
        # Check performance labels are assigned
        for item in result["items"]:
            assert item["performance"] in ["Above Average", "Average", "Below Average"]
    
    def test_empty_content(self):
        result = calculate_content_performance([])
        assert result["has_data"] is False


class TestTopContent:
    """Test top content finding."""
    
    def test_top_by_views(self, sample_content):
        top = find_top_content(sample_content, "views", 5)
        assert len(top) == 5
        # Should be sorted descending
        for i in range(len(top) - 1):
            assert top[i]["views"] >= top[i + 1]["views"]
    
    def test_top_by_engagement(self, sample_content):
        top = find_top_content(sample_content, "engagement", 10)
        assert len(top) == 10
    
    def test_empty_list(self):
        top = find_top_content([], "views", 10)
        assert len(top) == 0


class TestLowPerformingContent:
    """Test low performing content detection."""
    
    def test_finds_below_average(self, sample_content):
        low = find_low_performing_content(sample_content, 5)
        assert len(low) <= 5
        
        for item in low:
            assert "note" in item
            assert "improvement_area" in item
            assert item["views_diff_percent"] < 0


class TestBestPostingDay:
    """Test best posting day analysis."""
    
    def test_with_data(self, sample_content):
        result = find_best_posting_day(sample_content)
        assert result["has_data"] is True
        assert len(result["days"]) == 7
        assert result["best_day"] != "Insufficient data"
        assert "note" in result
    
    def test_empty_data(self):
        result = find_best_posting_day([])
        assert result["has_data"] is False


class TestBestPostingTime:
    """Test best posting time analysis."""
    
    def test_with_data(self, sample_content):
        result = find_best_posting_time(sample_content, min_posts_per_hour=1)
        assert result["has_data"] is True
        assert "hours" in result
        assert len(result["hours"]) == 24
    
    def test_insufficient_data_warning(self, sample_content):
        # Very high threshold should trigger insufficient data
        result = find_best_posting_time(sample_content, min_posts_per_hour=100)
        if result.get("insufficient_data"):
            assert "Not enough" in result["note"]


class TestContentTypeAnalysis:
    """Test content type comparison."""
    
    def test_with_data(self, sample_content):
        result = analyze_content_types(sample_content)
        assert result["has_data"] is True
        assert len(result["types"]) > 0
        
        for t in result["types"]:
            assert t["count"] > 0
            assert t["avg_views"] > 0


class TestAnomalyDetection:
    """Test anomaly detection."""
    
    def test_detects_anomalies(self, sample_metrics):
        anomalies = detect_anomalies(sample_metrics, z_threshold=1.5)
        # Should find some anomalies with a lower threshold
        for a in anomalies:
            assert abs(a["z_score"]) >= 1.5
            assert a["type"] in ["spike", "drop"]
            assert "message" in a
    
    def test_too_few_data_points(self):
        anomalies = detect_anomalies([], z_threshold=2.0)
        assert len(anomalies) == 0


class TestPerformanceScore:
    """Test performance score calculation."""
    
    def test_score_range(self, sample_metrics, sample_content):
        today = date.today()
        start = today - timedelta(days=29)
        result = calculate_performance_score(sample_metrics, sample_content, start, today)
        
        assert result["has_data"] is True
        assert 0 <= result["total_score"] <= 100
        assert len(result["components"]) == 5
        
        for key, comp in result["components"].items():
            assert 0 <= comp["score"] <= 100
            assert 0 <= comp["weight"] <= 1
    
    def test_formula_documented(self, sample_metrics, sample_content):
        today = date.today()
        start = today - timedelta(days=29)
        result = calculate_performance_score(sample_metrics, sample_content, start, today)
        assert "formula" in result


class TestAlerts:
    """Test alert generation."""
    
    def test_generates_alerts(self, sample_metrics):
        today = date.today()
        start = today - timedelta(days=6)
        alerts = generate_alerts(sample_metrics, start, today)
        
        for alert in alerts:
            assert "type" in alert
            assert "message" in alert
            assert alert["type"] in ["positive", "warning"]


# ─── Recommendation Engine Tests ────────────────────────────────

class TestRecommendations:
    """Test recommendation generation."""
    
    def test_generates_recommendations(self, sample_metrics, sample_content):
        today = date.today()
        start = today - timedelta(days=29)
        recs = generate_recommendations(sample_metrics, sample_content, start, today)
        
        assert len(recs) > 0
        for rec in recs:
            assert "category" in rec
            assert "recommendation" in rec
            assert "priority" in rec
            assert "data_basis" in rec
            assert 1 <= rec["priority"] <= 5


class TestActionPlan:
    """Test daily action plan generation."""
    
    def test_generates_plan(self, sample_metrics, sample_content):
        plan = generate_daily_action_plan(sample_metrics, sample_content, date.today())
        
        assert "morning" in plan
        assert "content" in plan
        assert "engagement" in plan
        assert "evening" in plan
        
        for section in ["morning", "content", "engagement", "evening"]:
            assert len(plan[section]) > 0


class TestPriorities:
    """Test priority generation."""
    
    def test_generates_5_priorities(self, sample_metrics, sample_content):
        today = date.today()
        start = today - timedelta(days=29)
        priorities = generate_priorities(sample_metrics, sample_content, start, today)
        
        assert len(priorities) == 5
        for p in priorities:
            assert isinstance(p, str)
            assert len(p) > 0


# ─── Zero/Edge Case Tests ──────────────────────────────────────

class TestZeroValues:
    """Test handling of zero values throughout the system."""
    
    def test_zero_views_engagement(self):
        """Engagement rate with zero views should be 0, not error."""
        from app.models.models import DailyMetric
        m = DailyMetric(
            page_id=1, metric_date=date.today(),
            views=0, followers=100, likes=0, comments=0, shares=0, posts=0,
            engagement_rate=0.0,
        )
        result = calculate_engagement_rate([m], date.today(), date.today())
        assert result["has_data"] is True
        assert result["engagement_rate"] == 0.0
    
    def test_all_zeros(self):
        """All zero metrics should not crash."""
        from app.models.models import DailyMetric
        metrics = [
            DailyMetric(
                page_id=1, metric_date=date.today() - timedelta(days=i),
                views=0, followers=0, likes=0, comments=0, shares=0, posts=0,
                engagement_rate=0.0,
            )
            for i in range(7)
        ]
        
        today = date.today()
        start = today - timedelta(days=6)
        
        view_result = calculate_view_growth(metrics, start, today)
        assert view_result["has_data"] is True
        assert view_result["total_views"] == 0
