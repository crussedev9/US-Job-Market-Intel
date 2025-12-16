"""Text processing utilities."""

import re
from typing import Optional


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text.

    Args:
        text: Input text

    Returns:
        Text with normalized whitespace
    """
    if not text:
        return ""
    return " ".join(text.split())


def clean_text(text: str, lowercase: bool = False) -> str:
    """Clean and normalize text.

    Args:
        text: Input text
        lowercase: Convert to lowercase

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Remove HTML tags (basic)
    text = re.sub(r"<[^>]+>", " ", text)

    # Normalize whitespace
    text = normalize_whitespace(text)

    if lowercase:
        text = text.lower()

    return text.strip()


def extract_keywords(text: str, min_length: int = 3) -> list[str]:
    """Extract keywords from text (basic tokenization).

    Args:
        text: Input text
        min_length: Minimum word length

    Returns:
        List of keywords
    """
    if not text:
        return []

    # Clean and lowercase
    text = clean_text(text, lowercase=True)

    # Extract words (alphanumeric + hyphens/underscores)
    words = re.findall(r"\b[\w-]+\b", text)

    # Filter by length
    keywords = [w for w in words if len(w) >= min_length]

    return keywords


def extract_state_abbrev(text: str) -> Optional[str]:
    """Extract US state abbreviation from text.

    Args:
        text: Text containing potential state code

    Returns:
        2-letter state code or None
    """
    from .locations_us import US_STATES

    # Look for state abbreviations (e.g., "CA", "NY")
    pattern = r"\b([A-Z]{2})\b"
    matches = re.findall(pattern, text.upper())

    for match in matches:
        if match in US_STATES:
            return match

    return None
