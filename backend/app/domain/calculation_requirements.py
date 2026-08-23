"""
Detection of required deterministic calculations from user queries.

This module acts as a guardrail to ensure that requests involving financial numbers,
cancellation fees, service credits, time elapsed, and SLA thresholds are routed
to deterministic Python domain calculators rather than letting an LLM perform
arithmetic or policy calculations in prose.
"""

import re
from enum import Enum


class CalculationRequirement(str, Enum):
    CANCELLATION = "cancellation_calc"
    SERVICE_CREDIT = "service_credit_calc"
    SLA = "sla_calc"


# Patterns that strongly indicate a deterministic calculation is needed
_CANCELLATION_PATTERNS = [
    r"\bcanc(?:el|elling|ellation|elled|els)\b",
]

_SERVICE_CREDIT_PATTERNS = [
    r"\bservice[\s_-]*credits?\b",
    r"\bfailed[\s_-]*pickups?\b",
    r"\bpickup[\s_-]*delay\b",
    r"\bcredit[\s_-]*eligib(?:le|ility)\b",
    r"\bclaim(?:ing)?[\s_-]*(?:a\s+)?credit\b",
    r"\beligible\s+for\s+(?:a\s+)?credit\b",
    r"\beligibility\s+for\s+(?:a\s+)?credit\b",
]

# Avoid false positives for unrelated uses of "credit" (e.g., credit card)
_CREDIT_FALSE_POSITIVE_PATTERNS = [
    r"\bcredit[\s_-]*cards?\b",
    r"\bline\s+of\s+credit\b",
    r"\bcredit\s+score\b",
]

_SLA_PATTERNS = [
    r"\bsla\b",
    r"\bslas\b",
    r"\bservice[\s_-]*level[\s_-]*agreement\b",
    r"\bresponse[\s_-]*targets?\b",
    r"\bresolution[\s_-]*targets?\b",
    r"\bbreach(?:ed|ing|es)?\b",
    r"\btarget[\s_-]*times?\b",
    r"\bresponse[\s_-]*times?\b",
]


def detect_calculation_requirement(user_message: str) -> CalculationRequirement | None:
    """
    Analyze the user query to detect if a deterministic calculation tool is required.

    Returns:
        CalculationRequirement or None if no calculation is required.
    """
    if not user_message:
        return None

    cleaned = user_message.lower().strip()

    # 1. Service Credit Check (check first as it might contain specific credit phrases)
    has_credit_false_positive = any(
        re.search(pattern, cleaned) for pattern in _CREDIT_FALSE_POSITIVE_PATTERNS
    )

    if not has_credit_false_positive:
        for pattern in _SERVICE_CREDIT_PATTERNS:
            if re.search(pattern, cleaned):
                return CalculationRequirement.SERVICE_CREDIT

    # 2. Cancellation Check
    for pattern in _CANCELLATION_PATTERNS:
        if re.search(pattern, cleaned):
            return CalculationRequirement.CANCELLATION

    # 3. SLA / Breach Check
    for pattern in _SLA_PATTERNS:
        if re.search(pattern, cleaned):
            return CalculationRequirement.SLA

    return None
