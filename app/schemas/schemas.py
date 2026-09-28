"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date, datetime


# ─── Auth Schemas ────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    theme: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ─── Page Schemas ────────────────────────────────────────────────────────────

class PageCreate(BaseModel):
    platform: str = Field(..., max_length=50)
    page_name: str = Field(..., max_length=255)
    page_external_id: Optional[str] = None
    page_url: Optional[str] = None
    api_token: Optional[str] = None


class PageResponse(BaseModel):
    id: int
    platform: str
    page_name: str
    page_external_id: Optional[str] = None
    page_url: Optional[str] = None
    is_demo: bool
    auto_refresh_minutes: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Daily Metrics Schemas ───────────────────────────────────────────────────

class DailyMetricCreate(BaseModel):
    metric_date: date
    views: int = 0
    followers: int = 0
    new_followers: int = 0
    lost_followers: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    posts: int = 0
    engagement_rate: float = 0.0


class DailyMetricResponse(BaseModel):
    id: int
    metric_date: date
    views: int
    followers: int
    new_followers: int
    lost_followers: int
    likes: int
    comments: int
    shares: int
    posts: int
    engagement_rate: float

    class Config:
        from_attributes = True


# ─── Content Schemas ─────────────────────────────────────────────────────────

class ContentCreate(BaseModel):
    content_type: str = Field(..., max_length=50)
    title: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    published_at: Optional[datetime] = None
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0


class ContentResponse(BaseModel):
    id: int
    content_type: str
    title: Optional[str] = None
    description: Optional[str] = None
    published_at: Optional[datetime] = None
    views: int
    likes: int
    comments: int
    shares: int
    engagement_rate: float = 0.0

    class Config:
        from_attributes = True


# ─── Report / Analytics Schemas ──────────────────────────────────────────────

class DateRange(BaseModel):
    start_date: date
    end_date: date


class KPICard(BaseModel):
    label: str
    value: str
    change_percent: Optional[float] = None
    change_direction: Optional[str] = None  # "up", "down", "stable"
    sub_label: Optional[str] = None


class DashboardResponse(BaseModel):
    page: PageResponse
    kpis: List[KPICard]
    daily_data: List[DailyMetricResponse]
    top_content: List[ContentResponse]
    low_content: List[ContentResponse]
    alerts: List[dict]
    recommendations: List[dict]
    health_summary: dict
    priorities: List[str]


# ─── Settings Schemas ────────────────────────────────────────────────────────

class AlertConfigUpdate(BaseModel):
    view_increase_threshold: float = 25.0
    view_decrease_threshold: float = 20.0
    engagement_low_threshold: float = 3.0
    follower_drop_threshold: float = 10.0
    enabled: bool = True


class ScoreWeightUpdate(BaseModel):
    weight_view_growth: float = 0.25
    weight_engagement: float = 0.25
    weight_follower_growth: float = 0.20
    weight_consistency: float = 0.15
    weight_share_rate: float = 0.15


class ManualMetricEntry(BaseModel):
    page_id: int
    metric_date: date
    views: int = 0
    followers: int = 0
    new_followers: int = 0
    lost_followers: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    posts: int = 0
