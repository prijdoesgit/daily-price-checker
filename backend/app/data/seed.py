"""
Seed the database with all data from the spreadsheet screenshots.
Run once on fresh DB: python -m app.data.seed
"""
import asyncio
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import AsyncSessionLocal, engine, Base
from app.models.medication import Medication, MedicationVariant
from app.models.vendor import Vendor, Platform
from app.models.price import PriceRecord
from app.services.normalization import normalize_strength, extract_strength_numeric, extract_unit


# ── Platforms ────────────────────────────────────────────────────────────────

PLATFORMS = [
    {"name": "PharmEasy",          "slug": "pharmeasy",        "base_url": "https://pharmeasy.in",                   "scraper_class": "PharmEasyScraper",    "priority": 10},
    {"name": "Apollo Pharmacy",    "slug": "apollo",           "base_url": "https://www.apollopharmacy.in",          "scraper_class": "ApolloScraper",       "priority": 9},
    {"name": "Tata 1mg",           "slug": "tata1mg",          "base_url": "https://www.1mg.com",                    "scraper_class": "Tata1mgScraper",      "priority": 9},
    {"name": "Netmeds",            "slug": "netmeds",          "base_url": "https://www.netmeds.com",                "scraper_class": "NetmedsScraper",      "priority": 8},
    {"name": "Wellness Forever",   "slug": "wellness_forever", "base_url": "https://www.wellnessforever.com",        "scraper_class": "WellnessForeverScraper","priority": 7},
    {"name": "MedPlus Mart",       "slug": "medplus",          "base_url": "https://www.medplusmart.com",            "scraper_class": "MedPlusScraper",      "priority": 7},
    {"name": "Truemeds",           "slug": "truemeds",         "base_url": "https://www.truemeds.in",                "scraper_class": "TrueMedsScraper",     "priority": 7},
    {"name": "MrMed",              "slug": "mrmed",            "base_url": "https://www.mrmed.in",                   "scraper_class": "MrMedScraper",        "priority": 8},
    {"name": "Flipkart Health+",   "slug": "flipkart_health",  "base_url": "https://www.flipkarthealthplus.com",     "scraper_class": "FlipkartHealthScraper","priority": 7},
    {"name": "Practo",             "slug": "practo",           "base_url": "https://www.practo.com",                 "scraper_class": "PractoScraper",       "priority": 5},
    {"name": "Amazon Pharmacy",    "slug": "amazon_pharma",    "base_url": "https://www.amazon.in/pharmacy",         "scraper_class": "AmazonPharmaScraper", "priority": 6},
]


# ── Medications + variants (from Screenshot 1) ────────────────────────────────

MEDICATIONS = [
    {
        "name": "Wegovy",
        "canonical_name": "wegovy",
        "generic_name": "semaglutide",
        "manufacturer": "Novo Nordisk",
        "category": "GLP-1 Agonist",
        "drug_type": "brand",
        "aliases": json.dumps(["Wegovy", "semaglutide", "wego vy"]),
        "description": "Once-weekly injectable semaglutide for chronic weight management",
        "variants": [
            {"strength": "0.25 mg", "mrp": 5660},
            {"strength": "0.5 mg",  "mrp": 8640},
            {"strength": "1 mg",    "mrp": 9100},
            {"strength": "1.7 mg",  "mrp": 12750},
            {"strength": "2.4 mg",  "mrp": 16400},
        ],
    },
    {
        "name": "Ozempic",
        "canonical_name": "ozempic",
        "generic_name": "semaglutide",
        "manufacturer": "Novo Nordisk",
        "category": "GLP-1 Agonist",
        "drug_type": "brand",
        "aliases": json.dumps(["Ozempic", "semaglutide ozempic", "ozempik"]),
        "description": "Once-weekly injectable semaglutide for type 2 diabetes",
        "variants": [
            {"strength": "0.25 mg", "mrp": 5660},
            {"strength": "0.5 mg",  "mrp": 8100},
            {"strength": "1 mg",    "mrp": 9100},
        ],
    },
    {
        "name": "Mounjaro",
        "canonical_name": "mounjaro",
        "generic_name": "tirzepatide",
        "manufacturer": "Eli Lilly",
        "category": "GIP/GLP-1 Dual Agonist",
        "drug_type": "brand",
        "aliases": json.dumps(["Mounjaro", "tirzepatide", "munjaro", "Zepbound"]),
        "description": "Once-weekly injectable tirzepatide for type 2 diabetes and weight management",
        "variants": [
            {"strength": "2.5 mg",  "mrp": 13225},
            {"strength": "5 mg",    "mrp": 16500},
            {"strength": "7.5 mg",  "mrp": 20725},
            {"strength": "10 mg",   "mrp": 20725},
            {"strength": "12.5 mg", "mrp": 25881},
            {"strength": "15 mg",   "mrp": 25881},
        ],
    },
    {
        "name": "Noveltreat",
        "canonical_name": "noveltreat",
        "generic_name": "semaglutide",
        "manufacturer": "Sun Pharma",
        "category": "GLP-1 Agonist",
        "drug_type": "brand",
        "aliases": json.dumps(["Noveltreat", "novel treat", "Sun Pharma semaglutide"]),
        "description": "Sun Pharma branded semaglutide injection",
        "variants": [
            {"strength": "0.25 mg", "mrp": 1571},
            {"strength": "0.5 mg",  "mrp": 1751},
            {"strength": "1 mg",    "mrp": 2246},
            {"strength": "1.7 mg",  "mrp": 2921},
            {"strength": "2.4 mg",  "mrp": 3330},
        ],
    },
    {
        "name": "Obeda",
        "canonical_name": "obeda",
        "generic_name": "orlistat",
        "manufacturer": "Dr. Reddy's",
        "category": "Lipase Inhibitor",
        "drug_type": "brand",
        "aliases": json.dumps(["Obeda", "orlistat", "Dr Reddys orlistat"]),
        "description": "Orlistat capsules for weight management",
        "variants": [
            {"strength": "2 mg",  "mrp": 4200},
            {"strength": "4 mg",  "mrp": 4200},
        ],
    },
]


# ── Platform prices from Screenshot 1 ────────────────────────────────────────
# Format: {medication_name: {strength: {platform_slug: price}}}
# None means not available / same as MRP

SEED_PRICES = {
    "Wegovy": {
        "0.25 mg": {"pharmeasy": 5660, "apollo": 5660, "tata1mg": 5094, "netmeds": 5660, "wellness_forever": 5660, "medplus": 5660, "truemeds": 5660, "mrmed": 4755, "flipkart_health": 5660},
        "0.5 mg":  {"pharmeasy": 8640, "apollo": 8640, "tata1mg": 7290, "netmeds": 8640, "wellness_forever": 8640, "medplus": 8640, "truemeds": 8640, "mrmed": 6805, "flipkart_health": 8640},
        "1 mg":    {"pharmeasy": 9100, "apollo": 9100, "tata1mg": 8190, "netmeds": 9100, "wellness_forever": 9100, "medplus": 9100, "truemeds": 9100, "mrmed": 7645, "flipkart_health": 9100},
        "1.7 mg":  {"pharmeasy": 12750, "apollo": 12750, "tata1mg": 11475, "netmeds": 12750, "wellness_forever": 12750, "medplus": 12750, "truemeds": 12750, "mrmed": 10710, "flipkart_health": 12750},
        "2.4 mg":  {"pharmeasy": 14432, "apollo": 16400, "tata1mg": 14760, "netmeds": 16400, "wellness_forever": 16400, "medplus": 16400, "truemeds": 16400, "mrmed": 13800, "flipkart_health": 16400},
    },
    "Ozempic": {
        "0.25 mg": {"pharmeasy": 5660, "apollo": 5660, "tata1mg": 5660, "netmeds": 5660, "wellness_forever": 5660, "medplus": 5660, "truemeds": 5660, "mrmed": 4755, "flipkart_health": 5660},
        "0.5 mg":  {"pharmeasy": 7290, "apollo": 8100, "tata1mg": 8100, "netmeds": 8100, "wellness_forever": 8100, "medplus": 8100, "truemeds": 8100, "mrmed": 6805, "flipkart_health": 8100},
        "1 mg":    {"pharmeasy": 9100, "apollo": 9100, "tata1mg": 9100, "netmeds": 9100, "wellness_forever": 9100, "medplus": 9100, "truemeds": 9100, "mrmed": 7645, "flipkart_health": 9100},
    },
    "Mounjaro": {
        "2.5 mg":  {"pharmeasy": 13225, "apollo": 13225, "tata1mg": 13225, "netmeds": 13225, "wellness_forever": 13225, "medplus": 13225, "truemeds": 13225, "mrmed": 11109, "flipkart_health": 13225},
        "5 mg":    {"pharmeasy": 16500, "apollo": 16500, "tata1mg": 16500, "netmeds": 16500, "wellness_forever": 16500, "medplus": 16500, "truemeds": 16500, "mrmed": 13860, "flipkart_health": 16500},
        "7.5 mg":  {"pharmeasy": 20725, "apollo": 20725, "tata1mg": 20725, "netmeds": 20725, "wellness_forever": 20725, "medplus": 20725, "truemeds": 20725, "mrmed": 17409, "flipkart_health": 20725},
        "10 mg":   {"pharmeasy": 20725, "apollo": 20725, "tata1mg": 20725, "netmeds": 20725, "wellness_forever": 20725, "medplus": 20725, "truemeds": 20725, "mrmed": 17409, "flipkart_health": 20725},
        "12.5 mg": {"pharmeasy": 25881, "apollo": 25881, "tata1mg": 25881, "netmeds": 25881, "wellness_forever": 25881, "medplus": 25881, "truemeds": 25881, "mrmed": 21740, "flipkart_health": 25881},
        "15 mg":   {"pharmeasy": 22687, "apollo": 25881, "tata1mg": 25881, "netmeds": 25881, "wellness_forever": 25881, "medplus": 25881, "truemeds": 25881, "mrmed": 21740, "flipkart_health": 25881},
    },
    "Noveltreat": {
        "0.25 mg": {"pharmeasy": 1571, "apollo": 1571, "tata1mg": 1751, "netmeds": 1571, "wellness_forever": 1571, "medplus": 1571, "truemeds": 1571, "mrmed": 1571, "flipkart_health": 1571},
        "0.5 mg":  {"pharmeasy": 1751, "apollo": 1751, "tata1mg": 1751, "netmeds": 1751, "wellness_forever": 1751, "medplus": 1751, "truemeds": 1751, "mrmed": 1751, "flipkart_health": 1751},
        "1 mg":    {"pharmeasy": 2246, "apollo": 2246, "tata1mg": 2246, "netmeds": 2246, "wellness_forever": 2246, "medplus": 2246, "truemeds": 2246, "mrmed": 2246, "flipkart_health": 2246},
        "1.7 mg":  {"pharmeasy": 2921, "apollo": 2921, "tata1mg": 2921, "netmeds": 2759, "wellness_forever": 2921, "medplus": 2921, "truemeds": 2921, "mrmed": 2921, "flipkart_health": 2921},
        "2.4 mg":  {"pharmeasy": 3330, "apollo": 3330, "tata1mg": 3330, "netmeds": 3330, "wellness_forever": 3330, "medplus": 3330, "truemeds": 3515, "mrmed": 3330, "flipkart_health": 3330},
    },
    "Obeda": {
        "2 mg": {"pharmeasy": 4200, "apollo": 4200, "tata1mg": 4200, "netmeds": 4200, "wellness_forever": 4200, "medplus": 4200, "truemeds": 4200, "mrmed": 4200, "flipkart_health": 4200},
        "4 mg": {"pharmeasy": 4200, "apollo": 4200, "tata1mg": 4200, "netmeds": 4200, "wellness_forever": 4200, "medplus": 4200, "truemeds": 4200, "mrmed": 4200, "flipkart_health": 4200},
    },
}


# ── Vendors from Screenshot 2 ────────────────────────────────────────────────

VENDORS = [
    {"name": "Pharmeasy", "contact_name": "Anuj", "phone": "9730156829", "city": None, "vendor_type": "online_platform", "medications_handled": json.dumps(["Mounjaro"]), "delivery_coverage": json.dumps(["Pan India"]), "referred_by": "Depends on serviceability"},
    {"name": "Lilly (Novo)", "contact_name": "Vishal", "phone": "8655004359", "city": "Mumbai", "vendor_type": "distributor", "medications_handled": json.dumps(["Mounjaro"]), "delivery_coverage": json.dumps(["Pan India"]), "referred_by": "Can help with contacts pan India"},
    {"name": "Novo", "contact_name": "Shashwat", "phone": "9167768707", "city": None, "vendor_type": "distributor", "medications_handled": json.dumps(["Wegovy", "Ozempic", "Rybelsus"]), "delivery_coverage": json.dumps(["Pan India"]), "referred_by": "Can help with delivery pan India"},
    {"name": "Tata 1mg", "contact_name": "Suman", "phone": "9999591090", "city": None, "vendor_type": "online_platform", "medications_handled": json.dumps(["Wegovy", "Ozempic", "Rybelsus"]), "delivery_coverage": json.dumps(["Pan India"]), "referred_by": "Om Khade"},
    {"name": "Rajesh Pharma", "contact_name": "Aniket", "phone": "7771000128", "city": "Jabalpur", "vendor_type": "distributor", "medications_handled": json.dumps(["Mounjaro"]), "delivery_coverage": json.dumps(["Jabalpur"]), "referred_by": "Ankit - 9830084143", "notes": "Amairiah Keswani"},
    {"name": "Shri Balaji Medical Distributors", "contact_name": "Shashank", "phone": "8639110871", "city": "Secunderabad", "vendor_type": "distributor", "medications_handled": json.dumps(["Mounjaro"]), "delivery_coverage": json.dumps(["Hyderabad", "Secunderabad"]), "referred_by": "Shashank - 8686738372", "notes": "Sheetal Kontham, Venkat Shyam"},
    {"name": "Lilly", "contact_name": "N T Raja", "phone": "9865453348", "city": "Coimbatore", "vendor_type": "distributor", "medications_handled": json.dumps(["Mounjaro"]), "delivery_coverage": json.dumps(["Coimbatore", "Tamil Nadu"]), "notes": "Lakshmi Priya"},
    {"name": "Novo (RDRK)", "contact_name": "RDRK", "phone": "9072619128", "city": "Tamil Nadu", "vendor_type": "distributor", "medications_handled": json.dumps(["Wegovy", "Ozempic", "Rybelsus"]), "delivery_coverage": json.dumps(["Tamil Nadu"]), "notes": "Krishnamurthy Ilango, Jayaraj C"},
    {"name": "Novo (Vinay lad)", "contact_name": "Vinay lad", "phone": "9822483666", "city": "Dharwad", "vendor_type": "distributor", "medications_handled": json.dumps(["Wegovy", "Ozempic", "Rybelsus"]), "delivery_coverage": json.dumps(["Dharwad", "Karnataka"]), "referred_by": "Dr. Deep", "notes": "Vinit Dajjode"},
    {"name": "Lilly (Ramanathan S)", "contact_name": "Ramanathan S", "phone": "9790657485", "city": "Chennai", "vendor_type": "distributor", "medications_handled": json.dumps(["Mounjaro"]), "delivery_coverage": json.dumps(["Chennai"]), "notes": "MUBEENA FATIMA, Alhaj Tasneem, Tapan Chitkara, Kartik Naik"},
    {"name": "Medcross", "contact_name": "Jitesh", "phone": "8217277449", "city": "Bangalore", "vendor_type": "distributor", "medications_handled": json.dumps(["Mounjaro"]), "delivery_coverage": json.dumps(["Bangalore"]), "referred_by": "Jitesh - 9762446612", "notes": "Devendra Deshmukh"},
    {"name": "Lilly (Dhanraj)", "contact_name": "Dhanraj", "phone": "9923037479", "city": "Parbhani", "vendor_type": "distributor", "medications_handled": json.dumps(["Mounjaro"]), "delivery_coverage": json.dumps(["Parbhani", "Maharashtra"]), "notes": "Devendra Deshmukh"},
    {"name": "Devang", "phone": "8291123455", "city": "Dombivali", "vendor_type": "distributor", "medications_handled": json.dumps(["Mounjaro"]), "delivery_coverage": json.dumps(["Dombivali", "Mumbai"]), "notes": "Atul Choudhan"},
    {"name": "Prabhat Shah", "phone": "9431115064", "city": "Ranchi", "vendor_type": "distributor", "medications_handled": json.dumps(["Mounjaro"]), "delivery_coverage": json.dumps(["Ranchi"]), "notes": "Mirza ather ali baig"},
    {"name": "SRI SAI MEDICALS", "contact_name": "Ramanathan S", "phone": "9244234499", "city": "Chennai", "vendor_type": "distributor", "medications_handled": json.dumps(["Mounjaro"]), "delivery_coverage": json.dumps(["Chennai"]), "referred_by": "Ramanathan S - 9790657485"},
    {"name": "Lilly (Shagufta)", "contact_name": "Shagufta", "phone": "9965409866", "city": "Tirupati", "vendor_type": "distributor", "medications_handled": json.dumps(["Mounjaro"]), "delivery_coverage": json.dumps(["Tirupati", "Andhra Pradesh"]), "notes": "Vamsee Krishna Reddy, Maneesh Rai"},
    {"name": "Zenica Pharma", "phone": "9665653468", "city": "Goa", "vendor_type": "distributor", "medications_handled": json.dumps(["Mounjaro"]), "delivery_coverage": json.dumps(["Goa"]), "notes": "Abhimanyu Dev"},
    {"name": "Shubham", "phone": "8484043056", "city": "Pune", "vendor_type": "distributor", "medications_handled": json.dumps(["Mounjaro"]), "delivery_coverage": json.dumps(["Pune"]), "notes": "Manisha Biraris"},
    {"name": "A1 Medicos", "phone": "8288688212", "city": "Ludhiana", "vendor_type": "distributor", "medications_handled": json.dumps(["Mounjaro"]), "delivery_coverage": json.dumps(["Ludhiana", "Punjab"]), "referred_by": "Priyanka Puri - 8146693777", "notes": "Singh Daler"},
    {"name": "Gaurav Sharma", "phone": "8837735117", "city": "Amritsar", "vendor_type": "distributor", "medications_handled": json.dumps(["Mounjaro"]), "delivery_coverage": json.dumps(["Amritsar", "Punjab"])},
    # Obeda distributors
    {"name": "Obeda Distributor (Allahabad)", "city": "Allahabad", "vendor_type": "distributor", "medications_handled": json.dumps(["Obeda"]), "notes": "Rajeev D - 9405458940"},
    {"name": "Obeda Distributor (Hyderabad 1)", "phone": "8106571411", "city": "Hyderabad", "vendor_type": "distributor", "medications_handled": json.dumps(["Obeda"]), "notes": "Divya CH"},
    {"name": "Obeda Distributor (Mumbai 1)", "phone": "9322506369", "city": "Mumbai", "vendor_type": "distributor", "medications_handled": json.dumps(["Obeda"]), "notes": "Vishal Sher"},
    {"name": "Obeda Distributor (Hyderabad 2)", "phone": "9280800648", "city": "Hyderabad", "vendor_type": "distributor", "medications_handled": json.dumps(["Obeda"]), "notes": "Mishil Parikh"},
    {"name": "Obeda Distributor (Hyderabad 3)", "phone": "9441112354", "city": "Hyderabad", "vendor_type": "distributor", "medications_handled": json.dumps(["Obeda"]), "notes": "Swathi Reddy"},
    {"name": "Obeda Distributor (Chennai 1)", "phone": "9882848686", "city": "Chennai", "vendor_type": "distributor", "medications_handled": json.dumps(["Obeda"]), "notes": "Sandeep Sethi"},
    {"name": "Obeda Distributor (Bangalore)", "phone": "9884164375", "city": "Bangalore", "vendor_type": "distributor", "medications_handled": json.dumps(["Obeda"]), "notes": "Meena Ramkumar"},
    {"name": "Obeda Distributor (Bangalore 2)", "phone": "8618156546", "city": "Bangalore", "vendor_type": "distributor", "medications_handled": json.dumps(["Obeda"]), "notes": "Kasturi V"},
    {"name": "Obeda Distributor (Delhi 1)", "phone": "9036022567", "city": "New Delhi", "vendor_type": "distributor", "medications_handled": json.dumps(["Obeda"]), "notes": "Swetha Rohith"},
    {"name": "Obeda Distributor (Bangalore 3)", "phone": "9888018813", "city": "Bangalore", "vendor_type": "distributor", "medications_handled": json.dumps(["Obeda"]), "notes": "Rajesh Wadhera"},
    {"name": "Obeda Distributor (Chennai 2)", "phone": "9600369024", "city": "Chennai", "vendor_type": "distributor", "medications_handled": json.dumps(["Obeda"]), "notes": "Selwyn Moses"},
    {"name": "Obeda Distributor (Hyderabad 4)", "phone": "7019910194", "city": "Hyderabad", "vendor_type": "distributor", "medications_handled": json.dumps(["Obeda"]), "notes": "Praveen Ramesh"},
    {"name": "Obeda Distributor (Chennai 3)", "phone": "9003120185", "city": "Chennai", "vendor_type": "distributor", "medications_handled": json.dumps(["Obeda"]), "notes": "Prabhu G"},
    {"name": "Obeda Distributor (Hyderabad 5)", "phone": "9389029194", "city": "Hyderabad", "vendor_type": "distributor", "medications_handled": json.dumps(["Obeda"]), "notes": "Janani Madhava"},
    {"name": "Obeda Distributor (Bangalore 4)", "phone": "9538924313", "city": "Bangalore", "vendor_type": "distributor", "medications_handled": json.dumps(["Obeda"]), "notes": "Veena B G"},
    {"name": "Lily (Pan India) Delhi Vendor", "contact_name": "Delhi Vendor (Priyanka)", "phone": "88828 58811", "city": "Delhi", "vendor_type": "distributor", "medications_handled": json.dumps(["Mounjaro"]), "delivery_coverage": json.dumps(["Pan India"])},
]


async def seed_db():
    async with AsyncSessionLocal() as db:
        print("Creating tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        print("Seeding platforms...")
        for p_data in PLATFORMS:
            existing = await db.execute(select(Platform).where(Platform.slug == p_data["slug"]))
            if not existing.scalar_one_or_none():
                platform = Platform(**p_data, is_active=True)
                db.add(platform)
        await db.commit()

        print("Seeding medications and variants...")
        platform_map: dict[str, int] = {}
        platforms_result = await db.execute(select(Platform))
        for p in platforms_result.scalars().all():
            platform_map[p.slug] = p.id

        for med_data in MEDICATIONS:
            variants_data = med_data.pop("variants")
            existing = await db.execute(select(Medication).where(Medication.name == med_data["name"]))
            med = existing.scalar_one_or_none()
            if not med:
                med = Medication(**med_data)
                db.add(med)
                await db.flush()
            else:
                med_data["variants"] = variants_data
                med_data = med_data  # restore

            for v_data in variants_data:
                strength = v_data["strength"]
                canonical = normalize_strength(strength)
                existing_v = await db.execute(
                    select(MedicationVariant).where(
                        MedicationVariant.medication_id == med.id,
                        MedicationVariant.canonical_strength == canonical,
                    )
                )
                if not existing_v.scalar_one_or_none():
                    variant = MedicationVariant(
                        medication_id=med.id,
                        strength=strength,
                        strength_numeric=extract_strength_numeric(strength),
                        unit=extract_unit(strength),
                        form="injection",
                        mrp=v_data["mrp"],
                        canonical_strength=canonical,
                    )
                    db.add(variant)

            med_data["variants"] = variants_data

        await db.commit()

        print("Seeding prices from spreadsheet data...")
        now = datetime.utcnow()

        for med_name, strengths in SEED_PRICES.items():
            for strength, platform_prices in strengths.items():
                canonical = normalize_strength(strength)
                variant_stmt = (
                    select(MedicationVariant)
                    .join(Medication, MedicationVariant.medication_id == Medication.id)
                    .where(Medication.name == med_name, MedicationVariant.canonical_strength == canonical)
                )
                variant_result = await db.execute(variant_stmt)
                variant = variant_result.scalar_one_or_none()
                if not variant:
                    print(f"  WARNING: variant not found for {med_name} {strength}")
                    continue

                for platform_slug, price in platform_prices.items():
                    platform_id = platform_map.get(platform_slug)
                    if not platform_id:
                        continue

                    existing_price = await db.execute(
                        select(PriceRecord).where(
                            PriceRecord.variant_id == variant.id,
                            PriceRecord.platform_id == platform_id,
                            PriceRecord.is_latest == True,
                        )
                    )
                    if existing_price.scalar_one_or_none():
                        continue

                    mrp = variant.mrp
                    discount = round((1 - price / mrp) * 100, 1) if mrp and mrp > 0 else None
                    record = PriceRecord(
                        variant_id=variant.id,
                        platform_id=platform_id,
                        price=float(price) if price else None,
                        mrp=mrp,
                        discount_pct=discount,
                        is_available=price is not None,
                        is_latest=True,
                        scraped_at=now,
                    )
                    db.add(record)

        await db.commit()

        print("Seeding vendors...")
        for v_data in VENDORS:
            name = v_data["name"]
            city = v_data.get("city")
            phone = v_data.get("phone")
            existing = await db.execute(
                select(Vendor).where(Vendor.name == name, Vendor.city == city)
            )
            if not existing.scalar_one_or_none():
                vendor = Vendor(is_verified=True, is_active=True, is_newly_discovered=False, **v_data)
                db.add(vendor)

        await db.commit()
        print("Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed_db())
