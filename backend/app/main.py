from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import structlog

from app.core.config import settings
from app.core.database import engine, Base
from app.api import medications, vendors, prices, scraping, dashboard

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting Medication Price Intelligence Platform")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("Database tables ready")
    yield
    await engine.dispose()
    log.info("Shutdown complete")


app = FastAPI(
    title="Medication Price Intelligence Platform",
    description="Real-time medication price tracking across Indian pharmacy platforms",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(medications.router, prefix="/api/medications", tags=["Medications"])
app.include_router(vendors.router, prefix="/api/vendors", tags=["Vendors"])
app.include_router(prices.router, prefix="/api/prices", tags=["Prices"])
app.include_router(scraping.router, prefix="/api/scraping", tags=["Scraping"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
