"""Demo data generator for the Page Analytics Dashboard.

Creates 90 days of realistic sample data including daily metrics,
100 content records, and realistic engagement patterns. All demo
data is clearly labeled with is_demo=True.
"""

import random
from datetime import date, datetime, timedelta, timezone
from typing import List
from sqlalchemy.orm import Session
from app.models.models import (
    User, Page, DailyMetric, Content, Recommendation, AlertConfig, ScoreWeight
)
from app.services.auth_service import hash_password

# Content templates for realistic drama shorts & reels data
CONTENT_TITLES = {
    "reel": [
        "Episode 14: The CEO's Hidden Identity Revealed 😱",
        "She thought he was poor until his bodyguard arrived... #DramaShorts",
        "When the underdog gets revenge | Part 3 🔥",
        "Her secret was discovered in front of everyone 💔",
        "The billionaire tests his fiance's loyalty #Reels",
        "Unexpected Plot Twist: He is actually the boss! 🎬",
        "Part 7: The Betrayal at the Wedding 💍",
        "He saved her life 10 years ago... now she's back ⚡",
        "She rejected the poor guy, but wait for the end! 😳",
        "Cliffhanger Alert: Will she forgive him? | Ep. 22",
        "The stepmother's secret plot exposed 🚨",
        "When kindness changes everything ❤️",
        "Episode 45: The Ultimate Showdown 💥",
        "Short Drama: The Secret Heir Returns",
        "Part 12: A Second Chance at Love #DramaVerse",
        "POV: You found out your boss is your childhood rival 🤫",
        "The truth comes out in court | Episode 19 ⚖️",
        "He bought the whole company just to hire her! 💼",
        "Never judge a book by its cover | Viral Short",
        "Episode 30: She finally remembered her past! 🧠✨",
    ],
    "video": [
        "The Drama Verse Shorts | Full Mini Series Season 1",
        "Top 5 Most Emotional Drama Scenes That Touched Millions",
        "Behind The Scenes: How We Shoot Viral Short Dramas",
        "Cast Interview: Secrets Behind The Season Finale Cliffhanger",
        "Season 1 Marathon: High Stakes & Shocking Twists",
        "Director's Cut: Extended Ending Episode 50",
        "Top 10 Most Watched Drama Shorts of the Month",
        "Character Transformation: From Underdog to CEO",
    ],
    "image": [
        "Character Spotlight: The Mysterious Heir 👤",
        "Poster Reveal: Season 2 of The Drama Verse! 🎭",
        "Behind the Camera: Shooting Episode 25 🎥",
        "Which Plot Twist Surprised You Most? (Vote Below)",
        "Over 10 Million Views on Episode 15! Thank You! 🎉",
        "Guess what happens next in Episode 30? 🤔",
        "Episode Teaser Photo Dump | New Release Tonight",
        "Fan Favorite Character Poll Results 📊",
    ],
    "text": [
        "Drop a ❤️ if you want Episode 50 released early today!",
        "Which character's revenge scene was your favorite so far?",
        "Who do you think leaked the secret company document? Comment below 🤫",
        "Season 2 is officially in production! What storyline do you want to see?",
        "Thank you to our 100K+ followers for supporting The Drama Verse Shorts!",
    ],
    "link": [
        "Watch Full HD Episodes of The Drama Verse Shorts",
        "Official Merch & Behind-The-Scenes Pass",
        "Subscribe for Exclusive Early Access Episodes",
        "Submit Your Short Drama Script Concept",
    ],
}


def generate_demo_data(db: Session, user_id: int) -> Page:
    """Generate a complete set of demo data for a user.
    
    Creates:
    - 1 demo page for The Drama Verse Shorts
    - 90 days of daily metrics with realistic patterns
    - 100 content items with varied performance
    - Initial recommendations
    
    Returns:
        The created Page object.
    """
    # Create demo page for The Drama Verse Shorts
    page = Page(
        user_id=user_id,
        platform="facebook",
        page_name="The Drama Verse Shorts",
        page_external_id="thedramaverseshorts",
        page_url="https://www.facebook.com/thedramaverseshorts/",
        is_demo=True,
        auto_refresh_minutes=0,
    )
    db.add(page)
    db.flush()  # Get page.id

    # Generate 90 days of daily metrics
    _generate_daily_metrics(db, page.id, days=90)
    
    # Generate 100 content items
    _generate_content(db, page.id, count=100)
    
    db.commit()
    return page


def _generate_daily_metrics(db: Session, page_id: int, days: int = 90):
    """Generate realistic daily metrics with trends and patterns.
    
    Patterns applied:
    - Overall growth trend (upward)
    - Weekend effect (slightly lower on weekends)
    - Random variation
    - Occasional spikes (viral days)
    - Seasonal fluctuation
    """
    today = date.today()
    base_views = 80000
    base_followers = 20000
    base_likes = 10000
    base_comments = 800
    base_shares = 1500
    
    for i in range(days - 1, -1, -1):
        metric_date = today - timedelta(days=i)
        day_of_week = metric_date.weekday()
        days_from_start = days - i
        
        # Growth trend factor (gradual increase over time)
        growth_factor = 1 + (days_from_start / days) * 0.4
        
        # Weekend effect (lower on Sat/Sun)
        weekend_factor = 0.78 if day_of_week >= 5 else 1.0
        
        # Mid-week boost (Tue-Thu tend to perform better)
        midweek_factor = 1.12 if 1 <= day_of_week <= 3 else 1.0
        
        # Random daily variation (±20%)
        random_factor = random.uniform(0.80, 1.20)
        
        # Occasional viral spike (5% chance, 2-3x views)
        viral_spike = random.uniform(2.0, 3.0) if random.random() < 0.05 else 1.0
        
        combined_factor = growth_factor * weekend_factor * midweek_factor * random_factor * viral_spike
        
        views = max(1, int(base_views * combined_factor))
        followers = base_followers + int(days_from_start * random.uniform(40, 80))
        new_followers = max(0, int(random.uniform(200, 600) * growth_factor * random_factor))
        lost_followers = max(0, int(random.uniform(20, 80) * random_factor))
        likes = max(0, int(base_likes * combined_factor * random.uniform(0.8, 1.2)))
        comments = max(0, int(base_comments * combined_factor * random.uniform(0.7, 1.3)))
        shares = max(0, int(base_shares * combined_factor * random.uniform(0.7, 1.3)))
        posts = random.choice([1, 1, 2, 2, 2, 3, 3, 4, 0])
        
        # Calculate engagement rate
        engagement_rate = 0.0
        if views > 0:
            engagement_rate = round(((likes + comments + shares) / views) * 100, 2)
        
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


def _generate_content(db: Session, page_id: int, count: int = 100):
    """Generate realistic content items with varied performance.
    
    Distribution:
    - 30% Reels
    - 25% Videos
    - 25% Images
    - 12% Text
    - 8% Links
    """
    today = datetime.now(timezone.utc)
    content_types = (
        ["reel"] * 30 + ["video"] * 25 + ["image"] * 25 + ["text"] * 12 + ["link"] * 8
    )
    random.shuffle(content_types)
    
    # Performance multipliers by content type (reels tend to get more views)
    type_multipliers = {
        "reel": {"views": 1.8, "likes": 1.5, "comments": 1.2, "shares": 2.0},
        "video": {"views": 1.4, "likes": 1.2, "comments": 1.5, "shares": 1.3},
        "image": {"views": 1.0, "likes": 1.3, "comments": 1.0, "shares": 0.8},
        "text": {"views": 0.6, "likes": 0.8, "comments": 1.8, "shares": 0.5},
        "link": {"views": 0.5, "likes": 0.5, "comments": 0.6, "shares": 1.5},
    }
    
    for i in range(count):
        ct = content_types[i % len(content_types)]
        mult = type_multipliers[ct]
        
        # Published over the last 90 days
        published_at = today - timedelta(
            days=random.randint(0, 89),
            hours=random.randint(6, 22),
            minutes=random.randint(0, 59),
        )
        
        # Base views with performance variation (some go viral, some flop)
        performance_roll = random.random()
        if performance_roll < 0.05:
            # Viral content (top 5%)
            base = random.randint(200000, 500000)
        elif performance_roll < 0.20:
            # Above average (15%)
            base = random.randint(80000, 200000)
        elif performance_roll < 0.70:
            # Average (50%)
            base = random.randint(30000, 80000)
        else:
            # Below average (30%)
            base = random.randint(5000, 30000)
        
        views = int(base * mult["views"])
        likes = int(views * random.uniform(0.08, 0.18) * mult["likes"])
        comments = int(views * random.uniform(0.005, 0.02) * mult["comments"])
        shares = int(views * random.uniform(0.01, 0.04) * mult["shares"])
        
        titles = CONTENT_TITLES.get(ct, CONTENT_TITLES["text"])
        title = titles[i % len(titles)]
        
        content = Content(
            page_id=page_id,
            external_content_id=f"demo_content_{i+1:04d}",
            content_type=ct,
            title=title,
            description=f"Demo content item #{i+1} - {ct.capitalize()} format",
            published_at=published_at,
            views=views,
            likes=likes,
            comments=comments,
            shares=shares,
        )
        db.add(content)


def create_demo_user(db: Session) -> User:
    """Create a demo user account if it doesn't exist.
    
    Credentials:
        Email: demo@example.com
        Password: demo123
    """
    existing = db.query(User).filter(User.email == "demo@example.com").first()
    if existing:
        return existing
    
    user = User(
        name="Demo User",
        email="demo@example.com",
        password_hash=hash_password("demo123"),
        theme="dark",
    )
    db.add(user)
    db.flush()
    
    # Create default alert config
    alert_config = AlertConfig(
        user_id=user.id,
        view_increase_threshold=25.0,
        view_decrease_threshold=20.0,
        engagement_low_threshold=3.0,
        follower_drop_threshold=10.0,
        enabled=True,
    )
    db.add(alert_config)
    
    # Create default score weights
    score_weight = ScoreWeight(
        user_id=user.id,
        weight_view_growth=0.25,
        weight_engagement=0.25,
        weight_follower_growth=0.20,
        weight_consistency=0.15,
        weight_share_rate=0.15,
    )
    db.add(score_weight)
    
    db.commit()
    return user


def initialize_demo_data(db: Session):
    """Initialize full demo environment: user + page + data.
    
    Safe to call multiple times; will sync page details if demo data exists.
    """
    user = create_demo_user(db)
    
    # Check if demo page already exists
    existing_page = db.query(Page).filter(
        Page.user_id == user.id, Page.is_demo == True
    ).first()
    
    if not existing_page:
        generate_demo_data(db, user.id)
    else:
        # Update existing demo page to match target page
        existing_page.page_name = "The Drama Verse Shorts"
        existing_page.page_external_id = "thedramaverseshorts"
        existing_page.page_url = "https://www.facebook.com/thedramaverseshorts/"
        db.commit()
