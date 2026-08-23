"""
Unit tests for deterministic calculation requirement detection.
"""

import pytest
from app.domain.calculation_requirements import (
    CalculationRequirement,
    detect_calculation_requirement,
)


@pytest.mark.parametrize(
    "query,expected",
    [
        ("Can Northstar cancel ORD-1001 without a cancellation fee?", CalculationRequirement.CANCELLATION),
        ("Can LumenWorks cancel ORD-2001?", CalculationRequirement.CANCELLATION),
        ("What is the fee if I cancel order ORD-3001?", CalculationRequirement.CANCELLATION),
        ("I need to cancel my shipment", CalculationRequirement.CANCELLATION),
        ("Is ORD-2002 eligible for a failed-pickup service credit?", CalculationRequirement.SERVICE_CREDIT),
        ("We had a failed pickup for ORD-1001, are we due a service credit?", CalculationRequirement.SERVICE_CREDIT),
        ("Can we claim a credit for the pickup delay?", CalculationRequirement.SERVICE_CREDIT),
        ("Check credit eligibility for ORD-2002", CalculationRequirement.SERVICE_CREDIT),
        ("What is the SLA target for ticket TKT-501?", CalculationRequirement.SLA),
        ("Has ticket TKT-502 breached its response target?", CalculationRequirement.SLA),
        ("What are the current SLA targets according to Support Policy v3?", CalculationRequirement.SLA),
        ("Is TKT-504 breached?", CalculationRequirement.SLA),
    ],
)
def test_calculation_requirement_detected(query, expected):
    assert detect_calculation_requirement(query) == expected


@pytest.mark.parametrize(
    "query",
    [
        "Why is my 4,200-row Growth CSV upload failing?",
        "Why does the SwiftShip shipment still show BOOKED after the driver picked it up?",
        "How do we change our billing contact email?",
        "Show me all open tickets for Northstar",
        "We want to update our credit card on file",  # False positive protection
        "What is our current line of credit?",        # False positive protection
    ],
)
def test_non_calculation_queries_not_flagged(query):
    assert detect_calculation_requirement(query) is None
