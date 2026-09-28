# 📊 The Drama Verse Shorts - Page Analytics & Performance Dashboard

A comprehensive, high-performance Python web application designed for analyzing social media page performance — specifically tailored for **[The Drama Verse Shorts](https://www.facebook.com/thedramaverseshorts/)**. Track views, engagement rates, follower growth, short-drama content performance, and receive data-driven actionable recommendations.

---

### 👨‍💻 Created & Designed By
**Nitish** ([@thenitishmind](https://github.com/thenitishmind))  
Target Page: [The Drama Verse Shorts](https://www.facebook.com/thedramaverseshorts/)  
Repository: [https://github.com/thenitishmind/page_analytic.git](https://github.com/thenitishmind/page_analytic.git)

---

## 🛠️ Complete Technologies & Tech Stack List:

- **Core Language:** Python 3.13+
- **Web Framework:** [FastAPI](https://fastapi.tiangolo.com/) (High-performance Async Web Framework)
- **Database & ORM:** [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (SQLite default, PostgreSQL ready)
- **Data Processing:** [pandas](https://pandas.pydata.org/) & [NumPy](https://numpy.org/) for metrics calculations & analytics engine
- **Security & Authentication:** Bcrypt password hashing & JWT (JSON Web Tokens)
- **Validation & Config:** [Pydantic v2](https://docs.pydantic.dev/) & Pydantic-Settings
- **Frontend UI/UX:** HTML5, Vanilla CSS3 (Glassmorphism, CSS Variables, Responsive Layouts, Dark/Light Mode), Modern ES6+ JavaScript
- **Data Visualization:** [Chart.js 4.4](https://www.chartjs.org/) for interactive responsive charts
- **Templating:** Jinja2 Template Engine
- **Testing:** [Pytest](https://docs.pytest.org/) (49 automated unit tests covering analytics calculations)
- **Containerization & Server:** Docker, Docker Compose, and [Uvicorn](https://www.uvicorn.org/) ASGI web server

---

## 🌟 Key Features

- **Executive Dashboard** — KPI cards, performance score gauge (0-100 scale), interactive view & engagement charts
- **Daily Analytics** — View growth trends, moving averages, anomaly detection using z-scores
- **Content Performance** — Analytics for short-drama Reels, episodes, top 10 & bottom 10 video rankings, best posting days & hours
- **Engagement Insights** — Detailed tracking of Likes, Comments, Shares, and Engagement Rate per view
- **Follower Growth** — Tracking total followers, net gain/loss, and retention trends
- **Actionable Recommendations** — Rule-based priority recommendations & dynamic Daily Action Plan
- **Weekly & Monthly Reports** — Automated performance summaries with PDF & CSV exports
- **Data Import & Management** — Support for Meta Business Suite CSV exports, Excel files, and manual entry

---

## 🚀 Quick Start Guide

### 1. Clone the repository

```bash
git clone https://github.com/thenitishmind/page_analytic.git
cd page_analytic
```

### 2. Set up virtual environment

```bash
python -m venv venv
```

Activate:
- **Windows:** `venv\Scripts\activate`
- **macOS/Linux:** `source venv/bin/activate`

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
copy .env.example .env
```

### 5. Run the server

```bash
uvicorn app.main:app --reload
```

### 6. Open in Browser

Navigate to **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 🧪 Running Unit Tests

To run the complete test suite (49 tests):

```bash
pytest tests/ -v
```

---

## 🐳 Docker Deployment

```bash
docker-compose up --build
```

---

## 📄 License & Attribution

Designed and developed by **Nitish** ([@thenitishmind](https://github.com/thenitishmind)). Distributed under the MIT License.
