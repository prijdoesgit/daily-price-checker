from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.medication import Medication, MedicationVariant

router = APIRouter()


class MedicationOut(BaseModel):
    id: int
    name: str
    canonical_name: str
    generic_name: Optional[str]
    manufacturer: Optional[str]
    category: Optional[str]
    drug_type: str
    aliases: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class VariantOut(BaseModel):
    id: int
    medication_id: int
    strength: str
    strength_numeric: Optional[float]
    unit: str
    form: str
    pack_size: Optional[str]
    mrp: Optional[float]
    canonical_strength: str

    class Config:
        from_attributes = True


class MedicationDetailOut(MedicationOut):
    variants: list[VariantOut]


@router.get("/", response_model=list[MedicationOut])
async def list_medications(
    search: Optional[str] = Query(None),
    drug_type: Optional[str] = Query(None),
    manufacturer: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Medication)
    if search:
        stmt = stmt.where(
            or_(
                Medication.name.ilike(f"%{search}%"),
                Medication.canonical_name.ilike(f"%{search}%"),
                Medication.generic_name.ilike(f"%{search}%"),
                Medication.aliases.ilike(f"%{search}%"),
            )
        )
    if drug_type:
        stmt = stmt.where(Medication.drug_type == drug_type)
    if manufacturer:
        stmt = stmt.where(Medication.manufacturer.ilike(f"%{manufacturer}%"))

    result = await db.execute(stmt.order_by(Medication.name))
    return result.scalars().all()


@router.get("/{medication_id}", response_model=MedicationDetailOut)
async def get_medication(medication_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Medication).where(Medication.id == medication_id)
    result = await db.execute(stmt)
    med = result.scalar_one_or_none()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")

    variant_stmt = select(MedicationVariant).where(MedicationVariant.medication_id == medication_id)
    variants_result = await db.execute(variant_stmt.order_by(MedicationVariant.strength_numeric))
    med.variants = variants_result.scalars().all()
    return med


@router.get("/{medication_id}/variants", response_model=list[VariantOut])
async def list_variants(medication_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(MedicationVariant).where(
        MedicationVariant.medication_id == medication_id
    ).order_by(MedicationVariant.strength_numeric)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/search/autocomplete")
async def autocomplete(q: str = Query(..., min_length=1), db: AsyncSession = Depends(get_db)):
    stmt = select(Medication.id, Medication.name, Medication.canonical_name, Medication.manufacturer).where(
        or_(
            Medication.name.ilike(f"%{q}%"),
            Medication.canonical_name.ilike(f"%{q}%"),
            Medication.generic_name.ilike(f"%{q}%"),
        )
    ).limit(10)
    result = await db.execute(stmt)
    rows = result.all()
    return [{"id": r.id, "name": r.name, "canonical_name": r.canonical_name, "manufacturer": r.manufacturer} for r in rows]
