from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.scraping import ScrapingJob
from app.models.vendor import Platform

router = APIRouter()


class ScrapingJobOut(BaseModel):
    id: int
    job_type: str
    platform_id: Optional[int]
    status: str
    triggered_by: str
    total_records: int
    success_records: int
    failed_records: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/trigger/full")
async def trigger_full_scrape(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Trigger a full scrape across all active platforms."""
    job = ScrapingJob(
        job_type="full_scrape",
        status="pending",
        triggered_by="manual",
    )
    db.add(job)
    await db.flush()
    job_id = job.id
    await db.commit()

    background_tasks.add_task(_run_full_scrape, job_id)
    return {"job_id": job_id, "status": "queued", "message": "Full scrape triggered"}


@router.post("/trigger/platform/{platform_id}")
async def trigger_platform_scrape(
    platform_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    platform_result = await db.execute(select(Platform).where(Platform.id == platform_id))
    platform = platform_result.scalar_one_or_none()
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")

    job = ScrapingJob(
        job_type="single_platform",
        platform_id=platform_id,
        status="pending",
        triggered_by="manual",
    )
    db.add(job)
    await db.flush()
    job_id = job.id
    await db.commit()

    background_tasks.add_task(_run_platform_scrape, job_id, platform_id)
    return {"job_id": job_id, "status": "queued", "platform": platform.name}


@router.get("/jobs", response_model=list[ScrapingJobOut])
async def list_jobs(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ScrapingJob).order_by(desc(ScrapingJob.created_at)).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/jobs/{job_id}", response_model=ScrapingJobOut)
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(ScrapingJob).where(ScrapingJob.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


async def _run_full_scrape(job_id: int):
    import asyncio
    import structlog
    from app.scrapers.manager import run_scraper_and_persist
    from app.models.medication import Medication, MedicationVariant
    from app.models.vendor import Platform as Plat
    from app.models.scraping import ScrapingJob as SJ
    from sqlalchemy import select, update
    from app.core.database import AsyncSessionLocal
    from datetime import datetime

    log = structlog.get_logger()

    async def _inline():
        try:
            async with AsyncSessionLocal() as db:
                await db.execute(update(SJ).where(SJ.id == job_id).values(
                    status="running", started_at=datetime.utcnow()))
                await db.commit()

                stmt = (select(Medication.name, MedicationVariant.strength)
                        .join(MedicationVariant, MedicationVariant.medication_id == Medication.id))
                meds = [{"name": r.name, "strength": r.strength}
                        for r in (await db.execute(stmt)).all()]

                plats = (await db.execute(
                    select(Plat).where(Plat.is_active == True)
                )).scalars().all()

                s, f = 0, 0
                for plat in plats:
                    try:
                        stats = await run_scraper_and_persist(db, plat.slug, meds, job_id)
                        s += stats.get("success", 0)
                        f += stats.get("failed", 0)
                    except Exception as e:
                        log.error("Platform scrape failed", platform=plat.slug, error=str(e))
                        f += len(meds)

                await db.execute(update(SJ).where(SJ.id == job_id).values(
                    status="completed", completed_at=datetime.utcnow(),
                    success_records=s, failed_records=f, total_records=s + f))
                await db.commit()
                log.info("Full scrape complete", job_id=job_id, success=s, failed=f)
        except Exception as e:
            log.error("Inline scrape job crashed", job_id=job_id, error=str(e))
            try:
                async with AsyncSessionLocal() as db:
                    await db.execute(update(SJ).where(SJ.id == job_id).values(
                        status="failed", completed_at=datetime.utcnow(),
                        error_log=str(e)))
                    await db.commit()
            except Exception:
                pass

    import threading
    threading.Thread(target=lambda: asyncio.run(_inline()), daemon=False).start()


async def _run_platform_scrape(job_id: int, platform_id: int):
    import asyncio
    import structlog
    from app.scrapers.manager import run_scraper_and_persist
    from app.models.medication import Medication, MedicationVariant
    from app.models.vendor import Platform as Plat
    from app.models.scraping import ScrapingJob as SJ
    from sqlalchemy import select, update
    from app.core.database import AsyncSessionLocal
    from datetime import datetime

    log = structlog.get_logger()

    async def _inline():
        try:
            async with AsyncSessionLocal() as db:
                platform_result = await db.execute(select(Plat).where(Plat.id == platform_id))
                platform = platform_result.scalar_one_or_none()
                if not platform:
                    return

                await db.execute(update(SJ).where(SJ.id == job_id).values(
                    status="running", started_at=datetime.utcnow()))
                await db.commit()

                stmt = (select(Medication.name, MedicationVariant.strength)
                        .join(MedicationVariant, MedicationVariant.medication_id == Medication.id))
                meds = [{"name": r.name, "strength": r.strength}
                        for r in (await db.execute(stmt)).all()]

                stats = await run_scraper_and_persist(db, platform.slug, meds, job_id)

                await db.execute(update(SJ).where(SJ.id == job_id).values(
                    status="completed", completed_at=datetime.utcnow(),
                    success_records=stats.get("success", 0),
                    failed_records=stats.get("failed", 0),
                    total_records=stats.get("total", 0)))
                await db.commit()
        except Exception as e:
            log.error("Platform scrape job crashed", job_id=job_id, platform_id=platform_id, error=str(e))
            try:
                async with AsyncSessionLocal() as db:
                    await db.execute(update(SJ).where(SJ.id == job_id).values(
                        status="failed", completed_at=datetime.utcnow(),
                        error_log=str(e)))
                    await db.commit()
            except Exception:
                pass

    import threading
    threading.Thread(target=lambda: asyncio.run(_inline()), daemon=False).start()
