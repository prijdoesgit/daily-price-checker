from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.price import PriceRecord
from app.models.vendor import Platform
from app.models.medication import MedicationVariant

router = APIRouter()


class PriceOut(BaseModel):
    id: int
    variant_id: int
    platform_id: Optional[int]
    platform_name: Optional[str]
    platform_slug: Optional[str]
    price: Optional[float]
    mrp: Optional[float]
    discount_pct: Optional[float]
    is_available: bool
    city: Optional[str]
    product_url: Optional[str]
    scraped_at: datetime

    class Config:
        from_attributes = True


class PriceComparisonOut(BaseModel):
    variant_id: int
    medication_name: str
    strength: str
    mrp: Optional[float]
    prices: list[PriceOut]
    cheapest: Optional[PriceOut]
    cheapest_discount_pct: Optional[float]
    last_updated: Optional[datetime]


@router.get("/variant/{variant_id}", response_model=list[PriceOut])
async def get_prices_for_variant(
    variant_id: int,
    city: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(PriceRecord, Platform.name.label("platform_name"), Platform.slug.label("platform_slug"))
        .outerjoin(Platform, PriceRecord.platform_id == Platform.id)
        .where(PriceRecord.variant_id == variant_id, PriceRecord.is_latest == True)
    )
    if city:
        stmt = stmt.where(PriceRecord.city == city)
    stmt = stmt.order_by(PriceRecord.price.asc().nullslast())

    result = await db.execute(stmt)
    rows = result.all()

    out = []
    for row in rows:
        pr = row[0]
        out.append(PriceOut(
            id=pr.id,
            variant_id=pr.variant_id,
            platform_id=pr.platform_id,
            platform_name=row.platform_name,
            platform_slug=row.platform_slug,
            price=pr.price,
            mrp=pr.mrp,
            discount_pct=pr.discount_pct,
            is_available=pr.is_available,
            city=pr.city,
            product_url=pr.product_url,
            scraped_at=pr.scraped_at,
        ))
    return out


@router.get("/compare/{variant_id}", response_model=PriceComparisonOut)
async def compare_prices(
    variant_id: int,
    city: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    variant_stmt = select(MedicationVariant).where(MedicationVariant.id == variant_id)
    variant_result = await db.execute(variant_stmt)
    variant = variant_result.scalar_one_or_none()

    from app.models.medication import Medication
    med_stmt = select(Medication.name).where(Medication.id == variant.medication_id)
    med_result = await db.execute(med_stmt)
    med_name = med_result.scalar_one_or_none() or ""

    prices = await get_prices_for_variant(variant_id, city, db)
    available_prices = [p for p in prices if p.is_available and p.price is not None]
    cheapest = available_prices[0] if available_prices else None
    cheapest_discount = None
    if cheapest and cheapest.mrp and cheapest.price:
        cheapest_discount = round((1 - cheapest.price / cheapest.mrp) * 100, 1)

    last_updated = max((p.scraped_at for p in prices), default=None) if prices else None

    return PriceComparisonOut(
        variant_id=variant_id,
        medication_name=med_name,
        strength=variant.strength if variant else "",
        mrp=variant.mrp if variant else None,
        prices=prices,
        cheapest=cheapest,
        cheapest_discount_pct=cheapest_discount,
        last_updated=last_updated,
    )


@router.get("/history/{variant_id}")
async def price_history(
    variant_id: int,
    platform_id: Optional[int] = Query(None),
    days: int = Query(30, le=365),
    db: AsyncSession = Depends(get_db),
):
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(days=days)
    stmt = (
        select(PriceRecord, Platform.name.label("platform_name"))
        .outerjoin(Platform)
        .where(PriceRecord.variant_id == variant_id, PriceRecord.scraped_at >= cutoff)
    )
    if platform_id:
        stmt = stmt.where(PriceRecord.platform_id == platform_id)
    stmt = stmt.order_by(PriceRecord.scraped_at.asc())

    result = await db.execute(stmt)
    rows = result.all()

    return [
        {
            "date": row[0].scraped_at.isoformat(),
            "price": row[0].price,
            "platform": row.platform_name,
            "platform_id": row[0].platform_id,
        }
        for row in rows
    ]
