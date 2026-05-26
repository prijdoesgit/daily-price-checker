from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, DateTime, ForeignKey, Text, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Medication(Base):
    __tablename__ = "medications"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    canonical_name: Mapped[str] = mapped_column(String(200), index=True)
    generic_name: Mapped[Optional[str]] = mapped_column(String(200))
    manufacturer: Mapped[Optional[str]] = mapped_column(String(200))
    category: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    drug_type: Mapped[str] = mapped_column(String(50), default="brand")  # brand, generic
    aliases: Mapped[Optional[str]] = mapped_column(Text)  # JSON array of alternate names
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    variants: Mapped[list["MedicationVariant"]] = relationship("MedicationVariant", back_populates="medication", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Medication {self.name}>"


class MedicationVariant(Base):
    __tablename__ = "medication_variants"

    id: Mapped[int] = mapped_column(primary_key=True)
    medication_id: Mapped[int] = mapped_column(ForeignKey("medications.id"), index=True)
    strength: Mapped[str] = mapped_column(String(50))
    strength_numeric: Mapped[Optional[float]] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(20), default="mg")
    form: Mapped[str] = mapped_column(String(50), default="injection")  # tablet, injection, pen
    pack_size: Mapped[Optional[str]] = mapped_column(String(100))
    mrp: Mapped[Optional[float]] = mapped_column(Float)
    canonical_strength: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    medication: Mapped["Medication"] = relationship("Medication", back_populates="variants")
    price_records: Mapped[list["PriceRecord"]] = relationship("PriceRecord", back_populates="variant", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("medication_id", "strength", "form", name="uq_variant"),
        Index("ix_variant_canonical", "canonical_strength"),
    )

    def __repr__(self):
        return f"<MedicationVariant {self.medication_id} {self.strength}>"
