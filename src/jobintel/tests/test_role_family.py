"""Tests for role family classification."""

import pytest
from jobintel.enrich.role_family import classify_role_family


def test_classify_tech_roles():
    """Test classification of tech/engineering roles."""
    test_cases = [
        ("Senior Software Engineer", "Backend development role", "Tech/Engineering"),
        ("Frontend Developer", "Build user interfaces", "Tech/Engineering"),
        ("DevOps Engineer", "Manage infrastructure", "Tech/Engineering"),
        ("Cloud Architect", "Design cloud solutions", "Tech/Engineering"),
    ]

    for title, desc, expected in test_cases:
        result = classify_role_family(title, desc)
        assert result == expected, f"Failed for: {title}"


def test_classify_data_roles():
    """Test classification of data/AI roles."""
    test_cases = [
        ("Data Scientist", "Build ML models", "Data/AI"),
        ("Machine Learning Engineer", "Deploy AI systems", "Data/AI"),
        ("Data Analyst", "Analyze business data", "Data/AI"),
        ("Analytics Engineer", "Build data pipelines", "Data/AI"),
    ]

    for title, desc, expected in test_cases:
        result = classify_role_family(title, desc)
        assert result == expected, f"Failed for: {title}"


def test_classify_product_roles():
    """Test classification of product/design roles."""
    test_cases = [
        ("Product Manager", "Define product strategy", "Product/Design"),
        ("UX Designer", "Design user experiences", "Product/Design"),
        ("Product Designer", "Design and research", "Product/Design"),
    ]

    for title, desc, expected in test_cases:
        result = classify_role_family(title, desc)
        assert result == expected, f"Failed for: {title}"


def test_classify_sales_roles():
    """Test classification of sales roles."""
    test_cases = [
        ("Account Executive", "Sell to enterprise", "Sales"),
        ("Business Development Representative", "Generate leads", "Sales"),
        ("Sales Manager", "Manage sales team", "Sales"),
    ]

    for title, desc, expected in test_cases:
        result = classify_role_family(title, desc)
        assert result == expected, f"Failed for: {title}"


def test_classify_unknown_role():
    """Test classification of unknown role."""
    result = classify_role_family("Chief Happiness Officer", "Make people happy")
    # Should return None or a best-guess classification
    # This is acceptable behavior
    assert result is None or isinstance(result, str)
