"""SQLAlchemy ORM models for the Page Analytics Dashboard."""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Date, Text,
    ForeignKey, Boolean, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """Registered user account."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    theme = Column(String(10), default="dark")  # "light" or "dark"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    pages = relationship("Page", back_populates="user", cascade="all, delete-orphan")
    alert_configs = relationship("AlertConfig", back_populates="user", cascade="all, delete-orphan")
    score_weights = relationship("ScoreWeight", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Page(Base):
    """A social media page being tracked."""
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    platform = Column(String(50), nullable=False)  # facebook, youtube, instagram, etc.
    page_name = Column(String(255), nullable=False)
    page_external_id = Column(String(255), nullable=True)
    page_url = Column(String(500), nullable=True)
    api_token = Column(String(500), nullable=True)  # Encrypted in production
    is_demo = Column(Boolean, default=False)
    auto_refresh_minutes = Column(Integer, default=0)  # 0 = manual only
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="pages")
    daily_metrics = relationship("DailyMetric", back_populates="page", cascade="all, delete-orphan")
    content = relationship("Content", back_populates="page", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="page", cascade="all, delete-orphan")


class DailyMetric(Base):
    """Daily aggregated metrics for a page."""
    __tablename__ = "daily_metrics"
    __table_args__ = (
        UniqueConstraint("page_id", "metric_date", name="uq_page_metric_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("pages.id"), nullable=False)
    metric_date = Column(Date, nullable=False, index=True)
    views = Column(Integer, default=0)
    followers = Column(Integer, default=0)
    new_followers = Column(Integer, default=0)
    lost_followers = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    posts = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)

    # Relationships
    page = relationship("Page", back_populates="daily_metrics")


class Content(Base):
    """Individual content items (posts, videos, reels, etc.)."""
    __tablename__ = "content"

    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("pages.id"), nullable=False)
    external_content_id = Column(String(255), nullable=True)
    content_type = Column(String(50), nullable=False)  # video, reel, image, text, link, other
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    page = relationship("Page", back_populates="content")

    @property
    def engagement_rate(self):
        """Calculate engagement rate: (likes + comments + shares) / views * 100."""
        if self.views and self.views > 0:
            return round(((self.likes + self.comments + self.shares) / self.views) * 100, 2)
        return 0.0


class Recommendation(Base):
    """Generated recommendations for a page."""
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("pages.id"), nullable=False)
    recommendation_date = Column(Date, nullable=False)
    category = Column(String(50), nullable=False)  # performance, content, engagement, growth, action
    recommendation = Column(Text, nullable=False)
    priority = Column(Integer, default=3)  # 1=highest, 5=lowest
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    page = relationship("Page", back_populates="recommendations")


class AlertConfig(Base):
    """User-configurable alert thresholds."""
    __tablename__ = "alert_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    view_increase_threshold = Column(Float, default=25.0)  # % increase to trigger positive alert
    view_decrease_threshold = Column(Float, default=20.0)  # % decrease to trigger warning
    engagement_low_threshold = Column(Float, default=3.0)   # engagement % below this triggers alert
    follower_drop_threshold = Column(Float, default=10.0)   # % follower drop to trigger alert
    enabled = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="alert_configs")


class ScoreWeight(Base):
    """Customizable performance score weights per user."""
    __tablename__ = "score_weights"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    weight_view_growth = Column(Float, default=0.25)
    weight_engagement = Column(Float, default=0.25)
    weight_follower_growth = Column(Float, default=0.20)
    weight_consistency = Column(Float, default=0.15)
    weight_share_rate = Column(Float, default=0.15)

    # Relationships
    user = relationship("User", back_populates="score_weights")
