from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey, Integer, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class PriceRecord(Base):
    __tablename__ = "price_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("medication_variants.id"), index=True)
    platform_id: Mapped[Optional[int]] = mapped_column(ForeignKey("platforms.id"), index=True)

    price: Mapped[Optional[float]] = mapped_column(Float)
    mrp: Mapped[Optional[float]] = mapped_column(Float)
    discount_pct: Mapped[Optional[float]] = mapped_column(Float)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    is_serviceable: Mapped[bool] = mapped_column(Boolean, default=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), index=True)

    product_url: Mapped[Optional[str]] = mapped_column(Text)
    product_name_raw: Mapped[Optional[str]] = mapped_column(String(500))
    pack_info: Mapped[Optional[str]] = mapped_column(String(200))

    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    is_latest: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    scraping_job_id: Mapped[Optional[int]] = mapped_column(ForeignKey("scraping_jobs.id"))

    variant: Mapped["MedicationVariant"] = relationship("MedicationVariant", back_populates="price_records")
    platform: Mapped[Optional["Platform"]] = relationship("Platform", back_populates="price_records")

    __table_args__ = (
        Index("ix_price_variant_platform_latest", "variant_id", "platform_id", "is_latest"),
        Index("ix_price_scraped_at", "scraped_at"),
    )

    def __repr__(self):
        return f"<PriceRecord variant={self.variant_id} platform={self.platform_id} price={self.price}>"
