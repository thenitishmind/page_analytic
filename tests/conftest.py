"""Test configuration and fixtures."""

import pytest
from datetime import date, timedelta, datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.models import User, Page, DailyMetric, Content


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_metrics():
    """Generate 30 days of sample daily metrics."""
    today = date.today()
    metrics = []
    base_views = 100000
    
    for i in range(30):
        d = today - timedelta(days=29 - i)
        growth = 1 + (i / 30) * 0.3  # gradual growth
        views = int(base_views * growth * (0.9 + (i % 3) * 0.1))
        followers = 20000 + i * 50
        
        m = DailyMetric(
            id=i + 1,
            page_id=1,
            metric_date=d,
            views=views,
            followers=followers,
            new_followers=int(50 + i * 2),
            lost_followers=int(10 + i),
            likes=int(views * 0.12),
            comments=int(views * 0.01),
            shares=int(views * 0.02),
            posts=2,
            engagement_rate=round(((views * 0.12 + views * 0.01 + views * 0.02) / views) * 100, 2) if views > 0 else 0,
        )
        metrics.append(m)
    
    return metrics


@pytest.fixture
def sample_content():
    """Generate sample content items."""
    content = []
    types = ["video", "reel", "image", "text", "link"]
    today = datetime.now(timezone.utc)
    
    for i in range(50):
        ct = types[i % len(types)]
        published = today - timedelta(days=i % 30, hours=6 + (i % 16))
        
        base = 50000 + (i * 1000)
        if i < 5:  # top performers
            base = 200000 + (i * 50000)
        elif i > 40:  # low performers
            base = 5000 + (i * 100)
        
        c = Content(
            id=i + 1,
            page_id=1,
            content_type=ct,
            title=f"Test Content {i + 1} - {ct}",
            published_at=published,
            views=base,
            likes=int(base * 0.1),
            comments=int(base * 0.01),
            shares=int(base * 0.02),
        )
        content.append(c)
    
    return content
