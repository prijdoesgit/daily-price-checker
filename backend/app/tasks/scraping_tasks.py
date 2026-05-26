import asyncio
from datetime import datetime
from typing import Optional
import structlog
from sqlalchemy import select, update

from app.tasks.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.models.medication import Medication, MedicationVariant
from app.models.vendor import Platform
from app.models.scraping import ScrapingJob
from app.scrapers.manager import run_scraper_and_persist

log = structlog.get_logger()


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _get_all_medications(db) -> list[dict]:
    stmt = (
        select(Medication.name, MedicationVariant.strength, MedicationVariant.id)
        .join(MedicationVariant, MedicationVariant.medication_id == Medication.id)
    )
    result = await db.execute(stmt)
    return [{"name": r.name, "strength": r.strength, "variant_id": r.id} for r in result.all()]


@celery_app.task(bind=True, max_retries=2, default_retry_delay=300)
def run_full_scrape_sync(self, job_id: Optional[int] = None):
    async def _run():
        async with AsyncSessionLocal() as db:
            job = None
            if job_id:
                stmt = select(ScrapingJob).where(ScrapingJob.id == job_id)
                result = await db.execute(stmt)
                job = result.scalar_one_or_none()

            if job:
                job.status = "running"
                job.started_at = datetime.utcnow()
                await db.commit()

            medications = await _get_all_medications(db)
            platforms_result = await db.execute(select(Platform).where(Platform.is_active == True))
            platforms = platforms_result.scalars().all()

            total_success = 0
            total_failed = 0

            for platform in platforms:
                try:
                    stats = await run_scraper_and_persist(db, platform.slug, medications, job_id)
                    total_success += stats.get("success", 0)
                    total_failed += stats.get("failed", 0)
                    log.info("Platform scrape done", platform=platform.slug, stats=stats)
                except Exception as e:
                    log.error("Platform scrape error", platform=platform.slug, error=str(e))
                    total_failed += len(medications)

            if job:
                await db.execute(
                    update(ScrapingJob).where(ScrapingJob.id == job_id).values(
                        status="completed",
                        completed_at=datetime.utcnow(),
                        success_records=total_success,
                        failed_records=total_failed,
                        total_records=total_success + total_failed,
                    )
                )
                await db.commit()

            return {"success": total_success, "failed": total_failed}

    try:
        return _run_async(_run())
    except Exception as exc:
        log.error("Full scrape task failed", error=str(exc))
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def run_platform_scrape_sync(self, job_id: int, platform_id: int):
    async def _run():
        async with AsyncSessionLocal() as db:
            platform_result = await db.execute(select(Platform).where(Platform.id == platform_id))
            platform = platform_result.scalar_one_or_none()
            if not platform:
                return {"error": "Platform not found"}

            await db.execute(
                update(ScrapingJob).where(ScrapingJob.id == job_id).values(
                    status="running", started_at=datetime.utcnow()
                )
            )
            await db.commit()

            medications = await _get_all_medications(db)
            stats = await run_scraper_and_persist(db, platform.slug, medications, job_id)

            await db.execute(
                update(ScrapingJob).where(ScrapingJob.id == job_id).values(
                    status="completed",
                    completed_at=datetime.utcnow(),
                    success_records=stats.get("success", 0),
                    failed_records=stats.get("failed", 0),
                    total_records=stats.get("total", 0),
                )
            )
            await db.commit()
            return stats

    try:
        return _run_async(_run())
    except Exception as exc:
        raise self.retry(exc=exc)
