"""
Confidence scoring + escalation gate. A confidently wrong answer is explicitly called out
in the assessment brief as the #1 trust risk -- this module is what converts "low signal"
into "escalate" rather than "guess and answer anyway".
"""

from dataclasses import dataclass
from typing import Tuple

LOW_CONFIDENCE_THRESHOLD = 0.55


@dataclass
class ConfidenceAssessment:
    score: float
    should_escalate: bool
    reason: str


def calculate_confidence(
    *,
    has_evidence: bool,
    required_calculation_called: bool,
    has_verification_issue: bool,
    has_access_issue: bool,
    has_conflict: bool,
    final_answer_available: bool = True,
) -> Tuple[float, bool]:
    if not final_answer_available:
        return 0.0, True

    if has_access_issue:
        return 0.0, True

    if has_verification_issue:
        return 0.2, True

    if not required_calculation_called:
        return 0.25, True

    if has_conflict:
        return 0.35, True

    if not has_evidence:
        return 0.55, True

    return 0.95, False


def assess_confidence(
    retrieval_hit: bool,
    authority_resolved: bool,
    tool_returned_needs_verification: bool,
    conflicting_sources: bool,
    required_calc_performed: bool = True,
    access_denied: bool = False,
) -> ConfidenceAssessment:
    score, should_escalate = calculate_confidence(
        has_evidence=retrieval_hit or authority_resolved,
        required_calculation_called=required_calc_performed,
        has_verification_issue=tool_returned_needs_verification,
        has_access_issue=access_denied,
        has_conflict=conflicting_sources,
        final_answer_available=True,
    )

    reason_bits = []
    if access_denied:
        reason_bits.append("Access denied by security policy")
    if not required_calc_performed:
        reason_bits.append("required deterministic calculation was not executed")
    if tool_returned_needs_verification:
        reason_bits.append("required data point is unknown/unverified")
    if not retrieval_hit and not authority_resolved:
        reason_bits.append("no matching document found")
    if not authority_resolved and not retrieval_hit:
        reason_bits.append("no authoritative current source for this clause")
    if conflicting_sources:
        reason_bits.append("sources disagree and precedence could not fully resolve it")

    reason = "; ".join(reason_bits) if reason_bits else "sufficient authoritative evidence found"
    return ConfidenceAssessment(
        score=score,
        should_escalate=should_escalate,
        reason=reason,
    )
