"""Tests for industry tagging."""

import pytest
from jobintel.enrich.industry import tag_industry


def test_tag_technology_industry():
    """Test technology industry tagging."""
    industry, confidence = tag_industry(
        "Acme Software",
        "acme.com",
        "We build cloud-based SaaS solutions using AI and machine learning",
    )
    assert industry == "Technology"
    assert confidence > 0.5


def test_tag_fintech_industry():
    """Test fintech industry tagging."""
    industry, confidence = tag_industry(
        "PayCorp",
        "paycorp.com",
        "Leading fintech company providing payment processing and banking solutions",
    )
    assert industry == "Financial Services"
    assert confidence > 0.5


def test_tag_healthcare_industry():
    """Test healthcare industry tagging."""
    industry, confidence = tag_industry(
        "HealthTech Inc",
        "healthtech.com",
        "Healthcare platform for patient management and medical records",
    )
    assert industry == "Healthcare"
    assert confidence > 0.5


def test_tag_ecommerce_industry():
    """Test e-commerce industry tagging."""
    industry, confidence = tag_industry(
        "ShopCo",
        "shopco.com",
        "E-commerce marketplace connecting buyers and sellers",
    )
    assert industry == "E-commerce/Retail"
    assert confidence > 0.5


def test_tag_unknown_industry():
    """Test tagging with minimal information."""
    industry, confidence = tag_industry(
        "Generic Corp",
        "generic.com",
        "We do business things",
    )
    # Should return None or low confidence
    if industry:
        assert confidence < 0.7
    else:
        assert confidence == 0.0
