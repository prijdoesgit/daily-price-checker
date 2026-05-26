# MedPrice Intelligence Platform — Setup Guide

## Quick Start (Docker)

```powershell
# 1. Ensure Docker Desktop is running
# 2. Run the startup script
.\start-dev.ps1

# Or manually:
docker-compose up --build
```

**URLs:**
| Service | URL |
|---------|-----|
| Dashboard (Frontend) | http://localhost:3000 |
| API (FastAPI) | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Task Monitor (Flower) | http://localhost:5555 |

---

## Manual Local Setup (without Docker)

### Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium

# Start PostgreSQL + Redis (via Docker or local install)
docker run -d -p 5432:5432 -e POSTGRES_DB=medprice -e POSTGRES_USER=medprice -e POSTGRES_PASSWORD=medprice_secret postgres:15
docker run -d -p 6379:6379 redis:7

# Apply migrations + seed data
alembic upgrade head
python -m app.data.seed

# Start API
uvicorn app.main:app --reload --port 8000
```

### Celery Worker (optional, for background scraping)
```powershell
celery -A app.tasks.celery_app worker --loglevel=info
celery -A app.tasks.celery_app beat --loglevel=info
```

### Frontend
```powershell
cd frontend
npm install
npm run dev   # http://localhost:3000
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   Next.js Frontend (3000)                │
│  Search → MedicationCard → PriceMatrix → Recommendations │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP / Proxy Rewrite
┌────────────────────▼────────────────────────────────────┐
│                  FastAPI Backend (8000)                   │
│  /api/medications  /api/prices  /api/vendors             │
│  /api/dashboard    /api/scraping                         │
└──────┬──────────────────────────────────┬───────────────┘
       │                                  │
┌──────▼──────┐                  ┌────────▼───────┐
│  PostgreSQL  │                  │  Celery + Redis │
│  (all data)  │                  │  (scrape jobs)  │
└─────────────┘                  └─────────────────┘
                                          │
                         ┌────────────────▼──────────────┐
                         │   Scraper Swarm (Playwright)   │
                         │  PharmEasy · Apollo · 1mg      │
                         │  Netmeds · MrMed · Truemeds    │
                         │  Flipkart · Wellness · MedPlus │
                         └───────────────────────────────┘
```

## Key Features
- **5 medications, 22 strengths** pre-seeded from your spreadsheets
- **35+ vendors** pre-seeded with contact details
- **9 pharmacy platform scrapers** with anti-bot protection
- **Daily automated scraping** at 6am and 2pm IST
- **Vendor discovery engine** runs weekly
- **Price history tracking** and trend charts
- **City-filtered recommendations** with local vendor contacts

## Adding New Medications
Edit `backend/app/data/seed.py` — add entries to `MEDICATIONS` and `SEED_PRICES`, then re-run seed.

## Adding New Scrapers
1. Create `backend/app/scrapers/your_platform.py` extending `BaseScraper`
2. Register in `SCRAPER_REGISTRY` in `backend/app/scrapers/manager.py`
3. Add platform entry in `PLATFORMS` in `backend/app/data/seed.py`
