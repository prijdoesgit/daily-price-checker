"""
Scraper manager — instantiates, runs, and persists results for all scrapers.
Add new scrapers here to register them automatically.
"""
import asyncio
from typing import Optional
from datetime import datetime
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.scrapers.base import ScrapedPrice
from app.scrapers.pharmeasy import PharmEasyScraper
from app.scrapers.apollo import ApolloScraper
from app.scrapers.tata1mg import Tata1mgScraper
from app.scrapers.netmeds import NetmedsScraper
from app.scrapers.mrmed import MrMedScraper
from app.scrapers.wellness_forever import WellnessForeverScraper
from app.scrapers.medplus import MedPlusScraper
from app.scrapers.truemeds import TrueMedsScraper
from app.scrapers.flipkart_health import FlipkartHealthScraper
from app.models.price import PriceRecord
from app.models.vendor import Platform
from app.models.medication import Medication, MedicationVariant
from app.services.normalization import normalize_strength

log = structlog.get_logger()

SCRAPER_REGISTRY = {
    "pharmeasy": PharmEasyScraper,
    "apollo": ApolloScraper,
    "tata1mg": Tata1mgScraper,
    "netmeds": NetmedsScraper,
    "mrmed": MrMedScraper,
    "wellness_forever": WellnessForeverScraper,
    "medplus": MedPlusScraper,
    "truemeds": TrueMedsScraper,
    "flipkart_health": FlipkartHealthScraper,
}


def get_scraper(slug: str):
    cls = SCRAPER_REGISTRY.get(slug)
    return cls() if cls else None


def get_all_scrapers():
    return [cls() for cls in SCRAPER_REGISTRY.values()]


async def run_scraper_and_persist(
    db: AsyncSession,
    scraper_slug: str,
    medications: list[dict],
    job_id: Optional[int] = None,
) -> dict:
    scraper = get_scraper(scraper_slug)
    if not scraper:
        return {"error": f"Unknown scraper: {scraper_slug}"}

    platform_result = await db.execute(select(Platform).where(Platform.slug == scraper_slug))
    platform = platform_result.scalar_one_or_none()
    if not platform:
        log.warning("Platform not found in DB", slug=scraper_slug)
        return {"error": "Platform not in DB"}

    log.info("Starting scraper", platform=scraper_slug, medications=len(medications))
    scraped = await scraper.scrape_all_medications(medications)
    log.info("Scraper completed", platform=scraper_slug, results=len(scraped))

    success = 0
    failed = 0

    for result in scraped:
        try:
            variant = await _find_variant(db, result.medication_name, result.strength)
            if not variant:
                failed += 1
                continue

            # Mark old records stale
            await db.execute(
                update(PriceRecord)
                .where(
                    PriceRecord.variant_id == variant.id,
                    PriceRecord.platform_id == platform.id,
                    PriceRecord.is_latest == True,
                )
                .values(is_latest=False)
            )

            record = PriceRecord(
                variant_id=variant.id,
                platform_id=platform.id,
                price=result.price,
                mrp=result.mrp,
                discount_pct=result.discount_pct,
                is_available=result.is_available,
                product_url=result.product_url,
                product_name_raw=result.product_name_raw,
                pack_info=result.pack_info,
                scraped_at=result.scraped_at,
                is_latest=True,
                scraping_job_id=job_id,
            )
            db.add(record)
            success += 1

        except Exception as e:
            log.warning("Failed to persist price record", error=str(e))
            failed += 1

    await db.execute(
        update(Platform)
        .where(Platform.id == platform.id)
        .values(last_scraped_at=datetime.utcnow())
    )
    await db.commit()

    return {"success": success, "failed": failed, "total": len(scraped)}


async def _find_variant(db: AsyncSession, medication_name: str, strength: str) -> Optional[MedicationVariant]:
    """Find a MedicationVariant by name and normalized strength."""
    canonical = normalize_strength(strength)

    stmt = (
        select(MedicationVariant)
        .join(Medication, MedicationVariant.medication_id == Medication.id)
        .where(
            Medication.name.ilike(f"%{medication_name}%"),
            MedicationVariant.canonical_strength == canonical,
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
