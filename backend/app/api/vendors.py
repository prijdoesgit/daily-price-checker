from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.vendor import Vendor, Platform

router = APIRouter()


class VendorOut(BaseModel):
    id: int
    name: str
    contact_name: Optional[str]
    phone: Optional[str]
    city: Optional[str]
    state: Optional[str]
    vendor_type: str
    medications_handled: Optional[str]
    delivery_coverage: Optional[str]
    referred_by: Optional[str]
    is_verified: bool
    is_newly_discovered: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PlatformOut(BaseModel):
    id: int
    name: str
    slug: str
    base_url: str
    is_active: bool
    priority: int
    last_scraped_at: Optional[datetime]
    scrape_success_rate: float

    class Config:
        from_attributes = True


@router.get("/", response_model=list[VendorOut])
async def list_vendors(
    city: Optional[str] = Query(None),
    medication: Optional[str] = Query(None),
    vendor_type: Optional[str] = Query(None),
    newly_discovered: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Vendor).where(Vendor.is_active == True)
    if city:
        stmt = stmt.where(
            or_(
                Vendor.city.ilike(f"%{city}%"),
                Vendor.delivery_coverage.ilike(f"%{city}%"),
            )
        )
    if medication:
        stmt = stmt.where(Vendor.medications_handled.ilike(f"%{medication}%"))
    if vendor_type:
        stmt = stmt.where(Vendor.vendor_type == vendor_type)
    if newly_discovered is not None:
        stmt = stmt.where(Vendor.is_newly_discovered == newly_discovered)

    result = await db.execute(stmt.order_by(Vendor.name))
    return result.scalars().all()


@router.get("/platforms", response_model=list[PlatformOut])
async def list_platforms(db: AsyncSession = Depends(get_db)):
    stmt = select(Platform).where(Platform.is_active == True).order_by(Platform.priority.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{vendor_id}", response_model=VendorOut)
async def get_vendor(vendor_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Vendor).where(Vendor.id == vendor_id)
    result = await db.execute(stmt)
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


@router.get("/cities/list")
async def list_cities(db: AsyncSession = Depends(get_db)):
    stmt = select(Vendor.city).where(Vendor.city != None, Vendor.is_active == True).distinct()
    result = await db.execute(stmt)
    cities = sorted([row[0] for row in result.all() if row[0]])
    return cities
