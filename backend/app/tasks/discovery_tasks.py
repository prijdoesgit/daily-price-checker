import asyncio
from app.tasks.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.services.vendor_discovery import run_vendor_discovery_job
import structlog

log = structlog.get_logger()


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=1, default_retry_delay=3600)
def run_discovery(self):
    async def _run():
        async with AsyncSessionLocal() as db:
            result = await run_vendor_discovery_job(db)
            log.info("Vendor discovery complete", result=result)
            return result

    try:
        return _run_async(_run())
    except Exception as exc:
        log.error("Discovery task failed", error=str(exc))
        raise self.retry(exc=exc)
