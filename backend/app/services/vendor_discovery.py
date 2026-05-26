"""
Vendor Discovery Engine — searches the web for new pharmacy vendors,
distributors, and wholesalers selling GLP-1 medications in India.
"""
import re
import asyncio
from typing import Optional
from datetime import datetime
import structlog
import httpx

from app.core.anti_bot import get_random_headers, human_delay
from app.models.scraping import VendorDiscovery

log = structlog.get_logger()

SEARCH_QUERIES = [
    "Mounjaro distributor India buy",
    "Wegovy supplier India pharmacy",
    "Ozempic wholesale India distributor",
    "semaglutide distributor India B2B",
    "tirzepatide India pharmacy contact",
    "GLP-1 medication wholesale India",
    "Noveltreat Sun Pharma distributor",
    "Obeda Dr Reddys wholesale India",
    "weight loss injection distributor Mumbai Delhi",
    "weight loss injection distributor Bangalore Hyderabad",
]

PHARMA_DIRECTORY_URLS = [
    "https://www.indiamart.com/search.mp?ss=mounjaro+distributor",
    "https://dir.indiamart.com/search.mp?ss=semaglutide+supplier",
]

PHONE_PATTERN = re.compile(r'(?:\+91[\s\-]?)?[6-9]\d{9}')
EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
CITY_LIST = [
    "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata",
    "Pune", "Ahmedabad", "Jaipur", "Surat", "Lucknow", "Chandigarh",
    "Nagpur", "Indore", "Coimbatore", "Bhopal", "Patna", "Amritsar",
    "Ludhiana", "Jabalpur", "Secunderabad", "Tirupati",
]


def extract_phones(text: str) -> list[str]:
    return list(set(PHONE_PATTERN.findall(text)))


def extract_emails(text: str) -> list[str]:
    return list(set(EMAIL_PATTERN.findall(text)))


def detect_city(text: str) -> Optional[str]:
    text_lower = text.lower()
    for city in CITY_LIST:
        if city.lower() in text_lower:
            return city
    return None


def detect_medications(text: str) -> list[str]:
    medications = ["Mounjaro", "Wegovy", "Ozempic", "Noveltreat", "Obeda", "Rybelsus",
                   "semaglutide", "tirzepatide", "liraglutide", "orlistat"]
    found = []
    text_lower = text.lower()
    for med in medications:
        if med.lower() in text_lower:
            found.append(med)
    return found


def score_discovery(raw_data: dict) -> float:
    score = 0.0
    if raw_data.get("phone"):
        score += 0.3
    if raw_data.get("city"):
        score += 0.2
    if raw_data.get("medications"):
        score += 0.3
    if raw_data.get("email"):
        score += 0.1
    if raw_data.get("url"):
        score += 0.1
    return min(score, 1.0)


async def discover_vendors_from_text(text: str, source_url: str) -> list[dict]:
    """Extract vendor candidates from a block of text."""
    candidates = []
    phones = extract_phones(text)
    emails = extract_emails(text)
    city = detect_city(text)
    meds = detect_medications(text)

    if phones or emails:
        raw = {
            "phone": phones[0] if phones else None,
            "email": emails[0] if emails else None,
            "city": city,
            "medications": meds,
            "url": source_url,
        }
        score = score_discovery(raw)
        if score >= 0.3:
            candidates.append({
                "raw_name": f"Discovered Vendor ({city or 'Unknown'})",
                "raw_city": city,
                "raw_phone": raw["phone"],
                "raw_url": source_url,
                "source_url": source_url,
                "source_type": "web_discovery",
                "medications_found": str(meds),
                "confidence_score": score,
                "status": "pending",
            })

    return candidates


async def run_vendor_discovery_job(db) -> dict:
    """Main entry point for the vendor discovery background job."""
    import json
    from sqlalchemy import select
    from app.models.scraping import VendorDiscovery as VDModel

    total_found = 0
    headers = get_random_headers()

    async with httpx.AsyncClient(headers=headers, timeout=30, follow_redirects=True) as client:
        for url in PHARMA_DIRECTORY_URLS[:2]:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    candidates = await discover_vendors_from_text(response.text, url)
                    for c in candidates:
                        existing_stmt = select(VDModel).where(
                            VDModel.raw_phone == c.get("raw_phone"),
                            VDModel.source_url == c.get("source_url"),
                        )
                        existing_result = await db.execute(existing_stmt)
                        if not existing_result.scalar_one_or_none():
                            vd = VDModel(**c)
                            db.add(vd)
                            total_found += 1
                await human_delay(2.0, 5.0)
            except Exception as e:
                log.warning("Discovery request failed", url=url, error=str(e))

    await db.commit()
    return {"discovered": total_found}
