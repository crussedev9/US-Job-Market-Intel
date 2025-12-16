"""Tests for US location filtering."""

import pytest
from jobintel.utils.locations_us import (
    parse_us_location,
    validate_us_location,
    is_remote,
    extract_state_code,
)


def test_parse_us_location_valid(us_locations):
    """Test parsing valid US locations."""
    for location in us_locations:
        result = parse_us_location(location, strict=True)
        assert result.is_us, f"Failed to detect US location: {location}"
        if "CA" in location or "NY" in location:
            assert result.state in ["CA", "NY"]


def test_parse_us_location_invalid(non_us_locations):
    """Test parsing non-US locations."""
    for location in non_us_locations:
        result = parse_us_location(location, strict=True)
        assert not result.is_us, f"Incorrectly detected US location: {location}"


def test_parse_us_location_ambiguous(ambiguous_locations):
    """Test parsing ambiguous locations."""
    for location in ambiguous_locations:
        result = parse_us_location(location, strict=True)
        # Strict mode should reject ambiguous
        assert not result.is_us or result.confidence < 0.7


def test_is_remote():
    """Test remote detection."""
    assert is_remote("Remote, United States") == True
    assert is_remote("San Francisco, CA (Remote)") == True
    assert is_remote("Work from home") == True
    assert is_remote("San Francisco, CA") == False


def test_extract_state_code():
    """Test state code extraction."""
    assert extract_state_code("San Francisco, CA") == "CA"
    assert extract_state_code("New York, NY 10001") == "NY"
    assert extract_state_code("Boston, Massachusetts") == "MA"
    assert extract_state_code("London, UK") is None


def test_validate_us_location():
    """Test US location validation."""
    assert validate_us_location("San Francisco, CA", strict=True) == True
    assert validate_us_location("London, UK", strict=True) == False
    assert validate_us_location("Remote, US", strict=True) == True
