from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Text, Float, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Platform(Base):
    """Online pharmacy platforms (PharmEasy, Apollo, etc.)"""
    __tablename__ = "platforms"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    base_url: Mapped[str] = mapped_column(String(500))
    scraper_class: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500))
    priority: Mapped[int] = mapped_column(default=0)
    last_scraped_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    scrape_success_rate: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    price_records: Mapped[list["PriceRecord"]] = relationship("PriceRecord", back_populates="platform")

    def __repr__(self):
        return f"<Platform {self.name}>"


class Vendor(Base):
    """Offline/independent distributors and regional vendors"""
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    contact_name: Mapped[Optional[str]] = mapped_column(String(200))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(200))
    city: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    state: Mapped[Optional[str]] = mapped_column(String(100))
    address: Mapped[Optional[str]] = mapped_column(Text)
    vendor_type: Mapped[str] = mapped_column(String(50), default="distributor")  # distributor, wholesaler, regional, b2b
    medications_handled: Mapped[Optional[str]] = mapped_column(Text)  # JSON array
    delivery_coverage: Mapped[Optional[str]] = mapped_column(Text)  # JSON array of cities
    referred_by: Mapped[Optional[str]] = mapped_column(String(500))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_newly_discovered: Mapped[bool] = mapped_column(Boolean, default=False)
    discovery_source: Mapped[Optional[str]] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("name", "city", "phone", name="uq_vendor"),
    )

    def __repr__(self):
        return f"<Vendor {self.name} ({self.city})>"
