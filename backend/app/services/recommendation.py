"""
Recommendation engine — ranks vendors and platforms by price, availability, city proximity.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.models.price import PriceRecord
from app.models.vendor import Platform, Vendor
from app.models.medication import MedicationVariant, Medication


CITY_SERVICEABLE_PLATFORMS = {
    "pharmeasy": "pan-india",
    "apollo": "pan-india",
    "tata1mg": "pan-india",
    "netmeds": "pan-india",
    "mrmed": "pan-india",
    "medplus": "selected",
    "wellness_forever": "selected",
}


async def get_recommendations_for_variant(
    db: AsyncSession,
    variant_id: int,
    city: Optional[str] = None,
) -> dict:
    variant_stmt = (
        select(MedicationVariant, Medication.name.label("med_name"), Medication.generic_name)
        .join(Medication, MedicationVariant.medication_id == Medication.id)
        .where(MedicationVariant.id == variant_id)
    )
    variant_result = await db.execute(variant_stmt)
    row = variant_result.first()
    if not row:
        return {"error": "Variant not found"}

    variant, med_name, generic_name = row[0], row.med_name, row.generic_name

    # Load all latest prices for this variant
    price_stmt = (
        select(PriceRecord, Platform.name.label("platform_name"), Platform.slug)
        .outerjoin(Platform, PriceRecord.platform_id == Platform.id)
        .where(PriceRecord.variant_id == variant_id, PriceRecord.is_latest == True)
        .order_by(PriceRecord.price.asc().nullslast())
    )
    price_result = await db.execute(price_stmt)
    price_rows = price_result.all()

    available_platforms = []
    unavailable_platforms = []

    for pr_row in price_rows:
        pr = pr_row[0]
        entry = {
            "platform_id": pr.platform_id,
            "platform_name": pr_row.platform_name,
            "platform_slug": pr_row.slug,
            "price": pr.price,
            "mrp": pr.mrp,
            "discount_pct": pr.discount_pct,
            "is_available": pr.is_available,
            "product_url": pr.product_url,
            "scraped_at": pr.scraped_at.isoformat() if pr.scraped_at else None,
        }
        if pr.is_available and pr.price is not None:
            available_platforms.append(entry)
        else:
            unavailable_platforms.append(entry)

    # City-specific vendors
    city_vendors = []
    if city:
        vendor_stmt = select(Vendor).where(
            Vendor.is_active == True,
            or_(
                Vendor.city.ilike(f"%{city}%"),
                Vendor.delivery_coverage.ilike(f"%{city}%"),
            ),
        )
        if med_name:
            vendor_stmt = vendor_stmt.where(
                or_(
                    Vendor.medications_handled.ilike(f"%{med_name}%"),
                    Vendor.medications_handled.ilike(f"%Mounjaro%") if "mounjaro" in med_name.lower() else Vendor.medications_handled.ilike(f"%{med_name}%"),
                )
            )
        vendor_result = await db.execute(vendor_stmt)
        vendors = vendor_result.scalars().all()
        city_vendors = [
            {
                "vendor_id": v.id,
                "name": v.name,
                "contact_name": v.contact_name,
                "phone": v.phone,
                "city": v.city,
                "vendor_type": v.vendor_type,
                "is_verified": v.is_verified,
                "referred_by": v.referred_by,
            }
            for v in vendors
        ]

    cheapest = available_platforms[0] if available_platforms else None
    savings = None
    if cheapest and cheapest["price"] and variant.mrp:
        savings = round(variant.mrp - cheapest["price"], 2)

    # Generic alternatives
    alternatives = []
    if generic_name:
        alt_stmt = (
            select(Medication)
            .where(
                or_(
                    Medication.generic_name == generic_name,
                    Medication.name.ilike(f"%{generic_name}%"),
                ),
                Medication.id != variant.medication_id,
            )
        )
        alt_result = await db.execute(alt_stmt)
        alt_meds = alt_result.scalars().all()
        alternatives = [
            {"id": m.id, "name": m.name, "manufacturer": m.manufacturer, "drug_type": m.drug_type}
            for m in alt_meds
        ]

    return {
        "variant_id": variant_id,
        "medication_name": med_name,
        "strength": variant.strength,
        "mrp": variant.mrp,
        "cheapest": cheapest,
        "savings_vs_mrp": savings,
        "available_platforms": available_platforms,
        "unavailable_platforms": unavailable_platforms,
        "city_vendors": city_vendors,
        "generic_alternatives": alternatives,
        "city": city,
    }
