from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.medication import Medication, MedicationVariant
from app.models.price import PriceRecord
from app.models.vendor import Platform, Vendor

router = APIRouter()


class DashboardStats(BaseModel):
    total_medications: int
    total_variants: int
    total_platforms: int
    total_vendors: int
    total_price_records: int
    last_scrape_at: Optional[datetime]
    new_vendors_discovered: int


class MedicationSearchResult(BaseModel):
    medication_id: int
    medication_name: str
    manufacturer: Optional[str]
    drug_type: str
    variants: list[dict]
    lowest_price: Optional[float]
    highest_price: Optional[float]
    cheapest_platform: Optional[str]


@router.get("/stats", response_model=DashboardStats)
async def get_stats(db: AsyncSession = Depends(get_db)):
    total_meds = (await db.execute(select(func.count(Medication.id)))).scalar_one()
    total_variants = (await db.execute(select(func.count(MedicationVariant.id)))).scalar_one()
    total_platforms = (await db.execute(select(func.count(Platform.id)).where(Platform.is_active == True))).scalar_one()
    total_vendors = (await db.execute(select(func.count(Vendor.id)).where(Vendor.is_active == True))).scalar_one()
    total_prices = (await db.execute(select(func.count(PriceRecord.id)))).scalar_one()
    last_scrape = (await db.execute(select(func.max(PriceRecord.scraped_at)))).scalar_one()
    new_vendors = (await db.execute(select(func.count(Vendor.id)).where(Vendor.is_newly_discovered == True))).scalar_one()

    return DashboardStats(
        total_medications=total_meds,
        total_variants=total_variants,
        total_platforms=total_platforms,
        total_vendors=total_vendors,
        total_price_records=total_prices,
        last_scrape_at=last_scrape,
        new_vendors_discovered=new_vendors,
    )


@router.get("/search")
async def search_medications(
    q: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Medication)
    if q:
        from sqlalchemy import or_
        stmt = stmt.where(
            or_(
                Medication.name.ilike(f"%{q}%"),
                Medication.canonical_name.ilike(f"%{q}%"),
                Medication.generic_name.ilike(f"%{q}%"),
                Medication.aliases.ilike(f"%{q}%"),
            )
        )
    result = await db.execute(stmt.order_by(Medication.name))
    medications = result.scalars().all()

    output = []
    for med in medications:
        variants_stmt = select(MedicationVariant).where(
            MedicationVariant.medication_id == med.id
        ).order_by(MedicationVariant.strength_numeric)
        variants_result = await db.execute(variants_stmt)
        variants = variants_result.scalars().all()

        prices_stmt = (
            select(PriceRecord.price, Platform.name.label("platform_name"))
            .join(MedicationVariant, PriceRecord.variant_id == MedicationVariant.id)
            .join(Platform, PriceRecord.platform_id == Platform.id)
            .where(
                MedicationVariant.medication_id == med.id,
                PriceRecord.is_latest == True,
                PriceRecord.is_available == True,
                PriceRecord.price.isnot(None),
            )
        )
        prices_result = await db.execute(prices_stmt)
        price_rows = prices_result.all()

        lowest_price = None
        highest_price = None
        cheapest_platform = None
        for row in price_rows:
            if lowest_price is None or row.price < lowest_price:
                lowest_price = row.price
                cheapest_platform = row.platform_name
            if highest_price is None or row.price > highest_price:
                highest_price = row.price

        output.append({
            "medication_id": med.id,
            "medication_name": med.name,
            "manufacturer": med.manufacturer,
            "drug_type": med.drug_type,
            "variants": [
                {
                    "id": v.id,
                    "strength": v.strength,
                    "unit": v.unit,
                    "form": v.form,
                    "mrp": v.mrp,
                }
                for v in variants
            ],
            "lowest_price": lowest_price,
            "highest_price": highest_price,
            "cheapest_platform": cheapest_platform,
        })

    return output


@router.get("/price-matrix/{medication_id}")
async def get_price_matrix(
    medication_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Full price matrix: variants × platforms, like the spreadsheet view."""
    variants_stmt = select(MedicationVariant).where(
        MedicationVariant.medication_id == medication_id
    ).order_by(MedicationVariant.strength_numeric)
    variants_result = await db.execute(variants_stmt)
    variants = variants_result.scalars().all()

    platforms_stmt = select(Platform).where(Platform.is_active == True).order_by(Platform.priority.desc())
    platforms_result = await db.execute(platforms_stmt)
    platforms = platforms_result.scalars().all()

    matrix = []
    for variant in variants:
        row = {
            "variant_id": variant.id,
            "strength": variant.strength,
            "unit": variant.unit,
            "form": variant.form,
            "mrp": variant.mrp,
            "prices": {},
            "min_price": None,
            "cheapest_platform": None,
        }
        min_price = None
        cheapest_platform = None

        for platform in platforms:
            price_stmt = select(PriceRecord).where(
                PriceRecord.variant_id == variant.id,
                PriceRecord.platform_id == platform.id,
                PriceRecord.is_latest == True,
            )
            price_result = await db.execute(price_stmt)
            price_rec = price_result.scalar_one_or_none()
            if price_rec:
                row["prices"][platform.slug] = {
                    "price": price_rec.price,
                    "is_available": price_rec.is_available,
                    "product_url": price_rec.product_url,
                    "discount_pct": price_rec.discount_pct,
                }
                if price_rec.price and price_rec.is_available:
                    if min_price is None or price_rec.price < min_price:
                        min_price = price_rec.price
                        cheapest_platform = platform.name
            else:
                row["prices"][platform.slug] = None

        row["min_price"] = min_price
        row["cheapest_platform"] = cheapest_platform
        matrix.append(row)

    return {
        "medication_id": medication_id,
        "platforms": [{"id": p.id, "name": p.name, "slug": p.slug} for p in platforms],
        "matrix": matrix,
    }


@router.get("/recommendations/{medication_id}/{variant_id}")
async def get_recommendations(
    medication_id: int,
    variant_id: int,
    city: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    from app.services.recommendation import get_recommendations_for_variant
    return await get_recommendations_for_variant(db, variant_id, city)
