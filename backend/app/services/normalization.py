"""
Medication normalization engine.
Handles dosage string canonicalization and brand/generic name mapping.
"""
import re
from typing import Optional

UNIT_ALIASES = {
    "milligram": "mg",
    "milligrams": "mg",
    "microgram": "mcg",
    "micrograms": "mcg",
    "µg": "mcg",
    "ug": "mcg",
    "ml": "ml",
    "milliliter": "ml",
    "millilitre": "ml",
}

FORM_KEYWORDS = {
    "injection": ["injection", "inj", "injectable", "pen", "autoinjector", "vial", "prefilled"],
    "tablet": ["tablet", "tab", "tablets", "oral", "capsule", "cap"],
    "solution": ["solution", "sol", "liquid"],
    "cream": ["cream", "gel", "ointment"],
}

BRAND_TO_GENERIC = {
    "wegovy": "semaglutide",
    "ozempic": "semaglutide",
    "rybelsus": "semaglutide",
    "mounjaro": "tirzepatide",
    "zepbound": "tirzepatide",
    "noveltreat": "semaglutide",
    "victoza": "liraglutide",
    "saxenda": "liraglutide",
    "trulicity": "dulaglutide",
    "obeda": "orlistat",
    "xenical": "orlistat",
}

GENERIC_TO_BRANDS: dict[str, list[str]] = {}
for brand, generic in BRAND_TO_GENERIC.items():
    GENERIC_TO_BRANDS.setdefault(generic, []).append(brand)

MEDICATION_ALIASES: dict[str, list[str]] = {
    "wegovy": ["wegovy", "semaglutide wegovy", "wego vy"],
    "ozempic": ["ozempic", "semaglutide ozempic", "ozempik"],
    "mounjaro": ["mounjaro", "tirzepatide", "munjaro"],
    "noveltreat": ["noveltreat", "novel treat"],
    "obeda": ["obeda"],
}


def normalize_strength(strength_str: str) -> str:
    """
    Normalize '5 MG', '5mg', '5 Mg injection', '5mg pen' → '5mg'
    """
    if not strength_str:
        return ""

    s = strength_str.lower().strip()
    # Remove form keywords
    for keywords in FORM_KEYWORDS.values():
        for kw in keywords:
            s = re.sub(rf'\b{re.escape(kw)}\b', "", s)

    # Normalize unit aliases
    for alias, canonical in UNIT_ALIASES.items():
        s = re.sub(rf'\b{re.escape(alias)}\b', canonical, s)

    # Collapse spaces between number and unit: "5 mg" → "5mg"
    s = re.sub(r'(\d+\.?\d*)\s*(mg|mcg|ml|iu|%)', r'\1\2', s)

    # Strip trailing non-alphanumeric
    s = re.sub(r'[^a-z0-9\.]+$', "", s).strip()
    return s


def extract_strength_numeric(strength_str: str) -> Optional[float]:
    match = re.search(r'(\d+\.?\d*)', normalize_strength(strength_str))
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    return None


def extract_unit(strength_str: str) -> str:
    normalized = normalize_strength(strength_str)
    match = re.search(r'\d+\.?\d*\s*(mg|mcg|ml|iu|%)', normalized)
    return match.group(1) if match else "mg"


def detect_form(text: str) -> str:
    text_lower = text.lower()
    for form, keywords in FORM_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return form
    return "injection"


def canonicalize_medication_name(name: str) -> str:
    """Lowercase, strip, collapse whitespace."""
    return re.sub(r'\s+', ' ', name.lower().strip())


def get_generic_name(brand_name: str) -> Optional[str]:
    return BRAND_TO_GENERIC.get(canonicalize_medication_name(brand_name))


def get_brand_names(generic_name: str) -> list[str]:
    return GENERIC_TO_BRANDS.get(generic_name.lower(), [])


def are_equivalent_medications(name_a: str, name_b: str) -> bool:
    """Check if two medication names refer to the same drug."""
    a = canonicalize_medication_name(name_a)
    b = canonicalize_medication_name(name_b)
    if a == b:
        return True
    generic_a = BRAND_TO_GENERIC.get(a)
    generic_b = BRAND_TO_GENERIC.get(b)
    if generic_a and generic_a == generic_b:
        return True
    if a in GENERIC_TO_BRANDS.get(b, []) or b in GENERIC_TO_BRANDS.get(a, []):
        return True
    return False


def normalize_medication_search_query(query: str) -> list[str]:
    """Expand a search query to include brand + generic alternates."""
    terms = {canonicalize_medication_name(query)}
    generic = BRAND_TO_GENERIC.get(canonicalize_medication_name(query))
    if generic:
        terms.add(generic)
        terms.update(get_brand_names(generic))
    return list(terms)
