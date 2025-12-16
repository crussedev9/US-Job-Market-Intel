"""US location parsing and validation utilities."""

import re
from typing import Optional
from dataclasses import dataclass


# US States mapping (abbrev -> full name)
US_STATES = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
    "DC": "District of Columbia",
}

# Reverse mapping for full state name lookup
STATE_NAMES_TO_ABBREV = {v.lower(): k for k, v in US_STATES.items()}

# Remote work indicators
REMOTE_KEYWORDS = [
    "remote",
    "work from home",
    "wfh",
    "anywhere",
    "distributed",
    "virtual",
]


@dataclass
class LocationParse:
    """Parsed US location components."""

    city: Optional[str] = None
    state: Optional[str] = None  # 2-letter code
    postal_code: Optional[str] = None
    is_remote: bool = False
    is_us: bool = False
    confidence: float = 0.0


def is_remote(location_text: str) -> bool:
    """Check if location indicates remote work.

    Args:
        location_text: Location string

    Returns:
        True if remote indicators found
    """
    if not location_text:
        return False

    text_lower = location_text.lower()
    return any(keyword in text_lower for keyword in REMOTE_KEYWORDS)


def extract_state_code(text: str) -> Optional[str]:
    """Extract US state code from text.

    Args:
        text: Location text

    Returns:
        2-letter state code or None
    """
    # Pattern: 2-letter state code (possibly followed by zip)
    # e.g., "San Francisco, CA", "Boston, MA 02101"
    pattern = r"\b([A-Z]{2})\b(?:\s+\d{5})?(?:\s*,|\s*$)"
    matches = re.findall(pattern, text.upper())

    for match in matches:
        if match in US_STATES:
            return match

    # Also check for full state names
    text_lower = text.lower()
    for state_name, abbrev in STATE_NAMES_TO_ABBREV.items():
        if state_name in text_lower:
            return abbrev

    return None


def extract_city(text: str, state_code: Optional[str] = None) -> Optional[str]:
    """Extract city name from location text.

    Args:
        text: Location text
        state_code: Optional state code to help parse

    Returns:
        City name or None
    """
    # Pattern: "City, State" or "City, ST ZIP"
    if state_code:
        # Look for text before state code
        pattern = rf"^(.+?),\s*{state_code}\b"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            city = match.group(1).strip()
            # Clean common prefixes
            city = re.sub(r"^(Greater|Metro)\s+", "", city, flags=re.IGNORECASE)
            return city

    # Fallback: take first part before comma
    parts = text.split(",")
    if parts:
        city = parts[0].strip()
        if city and not city.upper() in US_STATES:
            return city

    return None


def extract_postal_code(text: str) -> Optional[str]:
    """Extract US postal code from text.

    Args:
        text: Location text

    Returns:
        5-digit ZIP code or None
    """
    # Pattern: 5-digit ZIP code
    pattern = r"\b(\d{5})\b"
    match = re.search(pattern, text)
    return match.group(1) if match else None


def parse_us_location(location_text: str, strict: bool = True) -> LocationParse:
    """Parse US location string into components.

    Args:
        location_text: Raw location string from job posting
        strict: If True, reject ambiguous non-US locations

    Returns:
        LocationParse with extracted components
    """
    result = LocationParse()

    if not location_text:
        return result

    text = location_text.strip()

    # Check for remote
    result.is_remote = is_remote(text)

    # Extract state code
    state_code = extract_state_code(text)
    if state_code:
        result.state = state_code
        result.is_us = True
        result.confidence = 0.9

        # Extract city
        result.city = extract_city(text, state_code)

        # Extract postal code
        result.postal_code = extract_postal_code(text)

    else:
        # No state code found - check if explicitly US
        text_lower = text.lower()
        if any(keyword in text_lower for keyword in ["united states", "usa", "u.s."]):
            result.is_us = True
            result.confidence = 0.7
        elif strict:
            # Strict mode: exclude ambiguous
            result.is_us = False
            result.confidence = 0.0
        else:
            # Non-strict: low confidence US
            result.is_us = True
            result.confidence = 0.3

    return result


def validate_us_location(location_text: str, strict: bool = True) -> bool:
    """Validate if location is clearly US-based.

    Args:
        location_text: Raw location string
        strict: If True, exclude ambiguous locations

    Returns:
        True if location is US (or acceptable under non-strict mode)
    """
    parsed = parse_us_location(location_text, strict=strict)
    return parsed.is_us and (not strict or parsed.confidence >= 0.7)
