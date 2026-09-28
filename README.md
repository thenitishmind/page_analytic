# 📊 Page Analytics & Performance Dashboard

A comprehensive, Python-based web application for analyzing social media page performance. Track views, engagement, followers, content performance, and get data-driven recommendations.

## Features

- **Dashboard** — KPI cards, charts, daily performance at a glance
- **Daily Analytics** — View trends, moving averages, anomaly detection
- **Content Analytics** — Top/low performing content, type comparison, best posting day/time
- **Engagement Analytics** — Engagement rate, likes/comments/shares trends
- **Growth Analytics** — Follower growth, net gain/loss, view trends
- **Recommendations** — Data-driven action plans and priorities
- **Reports** — Weekly and monthly performance reports with export
- **Performance Score** — Transparent 0-100 score with configurable weights
- **Alert System** — Configurable thresholds for views, engagement, followers
- **Anomaly Detection** — Statistical anomaly detection using z-scores
- **Data Import** — CSV, Excel upload, and manual entry
- **Dark/Light Mode** — User-selectable theme preference
- **Demo Mode** — 90 days of realistic sample data included

## Tech Stack

- **Backend:** Python 3.12+, FastAPI, SQLAlchemy, Pydantic
- **Frontend:** Jinja2, HTML5, CSS3, JavaScript, Chart.js
- **Database:** SQLite (default), PostgreSQL (optional)
- **Analytics:** pandas, NumPy, statistics
- **Auth:** JWT (cookie-based for web UI)

## Quick Start

### 1. Clone and navigate

```bash
cd page_analytics
```

### 2. Create virtual environment

```bash
python -m venv venv
```

### 3. Activate (Windows)

```bash
venv\Scripts\activate
```

### 3. Activate (macOS/Linux)

```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment

```bash
copy .env.example .env
```

Edit `.env` as needed. Default settings work for local development.

### 6. Run

```bash
uvicorn app.main:app --reload
```

### 7. Open

```
http://127.0.0.1:8000
```

### Demo Credentials

| Field    | Value              |
| -------- | ------------------ |
| Email    | `demo@example.com` |
| Password | `demo123`          |

## Project Structure

```
page_analytics/
├── app/
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Settings from environment
│   ├── database.py             # SQLAlchemy engine & session
│   ├── models/
│   │   └── models.py           # ORM models (User, Page, Metrics, Content, etc.)
│   ├── schemas/
│   │   └── schemas.py          # Pydantic validation schemas
│   ├── routers/
│   │   ├── auth.py             # Login, register, logout
│   │   ├── dashboard.py        # Main dashboard
│   │   ├── pages_router.py     # Page management
│   │   ├── analytics_router.py # Daily/content/engagement/growth pages
│   │   ├── api_router.py       # REST API endpoints
│   │   ├── reports.py          # Weekly/monthly reports & export
│   │   └── settings_router.py  # Settings, import, manual entry
│   ├── analytics/
│   │   ├── analytics_engine.py # All calculation functions
│   │   └── recommendation_engine.py # Rule-based recommendations
│   ├── auth/
│   │   └── jwt_handler.py      # JWT token handling
│   ├── services/
│   │   ├── auth_service.py     # User auth operations
│   │   └── page_service.py     # Page CRUD & data import
│   └── utils/
│       ├── helpers.py          # Utility functions
│       └── demo_data.py        # Demo data generator
├── templates/                  # Jinja2 HTML templates
├── static/
│   ├── css/style.css           # Complete design system
│   └── js/app.js               # Client-side functionality
├── tests/
│   ├── conftest.py             # Test fixtures
│   └── test_analytics.py       # Unit tests
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## API Endpoints

| Method | Endpoint                          | Description           |
| ------ | --------------------------------- | --------------------- |
| GET    | `/api/dashboard/{page_id}`        | Full dashboard data   |
| GET    | `/api/analytics/daily/{page_id}`  | Daily view analytics  |
| GET    | `/api/analytics/content/{page_id}`| Content performance   |
| GET    | `/api/analytics/engagement/{page_id}` | Engagement metrics |
| GET    | `/api/analytics/growth/{page_id}` | Growth analytics      |
| GET    | `/api/recommendations/{page_id}`  | Recommendations       |
| GET    | `/api/reports/weekly/{page_id}`   | Weekly report         |
| GET    | `/api/reports/monthly/{page_id}`  | Monthly report        |
| POST   | `/api/pages`                      | Create page           |
| DELETE | `/api/pages/{page_id}`            | Delete page           |
| POST   | `/api/import/csv`                 | Import CSV            |
| POST   | `/api/import/excel`               | Import Excel          |
| POST   | `/api/import/manual`              | Manual metric entry   |

## Running Tests

```bash
pytest tests/ -v
```

## Docker

```bash
docker-compose up --build
```

## Performance Score Formula

The performance score (0-100) is calculated from 5 weighted components:

| Component       | Default Weight | Scoring                                  |
| --------------- | -------------- | ---------------------------------------- |
| View Growth     | 25%            | Maps -50% → 0, 0% → 50, +50% → 100     |
| Engagement      | 25%            | Maps 0% → 0, 5% → 50, 10%+ → 100       |
| Follower Growth | 20%            | Maps based on growth percentage          |
| Consistency     | 15%            | Days with posts / total days × 100       |
| Share Rate      | 15%            | Maps share rate to 0-100 scale           |

Weights are fully configurable in Settings.

## Data Quality

The application warns about:
- Missing dates in selected period
- Zero-view days
- Insufficient content for posting-time analysis
- Missing engagement data

**No values are silently invented.** Missing data is clearly labeled.

## Security

- Password hashing (bcrypt)
- JWT authentication (httponly cookies)
- Input validation (Pydantic)
- SQL injection protection (SQLAlchemy ORM)
- Environment variables for secrets
- No API keys exposed in frontend

## License

MIT
