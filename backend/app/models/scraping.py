from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ScrapingJob(Base):
    __tablename__ = "scraping_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_type: Mapped[str] = mapped_column(String(50))  # full_scrape, single_platform, single_medication
    platform_id: Mapped[Optional[int]] = mapped_column(ForeignKey("platforms.id"))
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)  # pending, running, completed, failed
    triggered_by: Mapped[str] = mapped_column(String(50), default="scheduler")  # scheduler, manual, api
    total_records: Mapped[int] = mapped_column(Integer, default=0)
    success_records: Mapped[int] = mapped_column(Integer, default=0)
    failed_records: Mapped[int] = mapped_column(Integer, default=0)
    error_log: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def success_rate(self) -> float:
        if self.total_records == 0:
            return 0.0
        return self.success_records / self.total_records


class VendorDiscovery(Base):
    """Newly discovered vendors from automated research."""
    __tablename__ = "vendor_discoveries"

    id: Mapped[int] = mapped_column(primary_key=True)
    raw_name: Mapped[str] = mapped_column(String(300))
    raw_city: Mapped[Optional[str]] = mapped_column(String(100))
    raw_phone: Mapped[Optional[str]] = mapped_column(String(100))
    raw_url: Mapped[Optional[str]] = mapped_column(Text)
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(50))  # google, directory, b2b_portal
    medications_found: Mapped[Optional[str]] = mapped_column(Text)  # JSON array
    confidence_score: Mapped[float] = mapped_column(Float, default=0.5)
    status: Mapped[str] = mapped_column(String(30), default="pending")  # pending, approved, rejected, merged
    vendor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("vendors.id"))
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
