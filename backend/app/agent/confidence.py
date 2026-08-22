"""
Confidence scoring + escalation gate. A confidently wrong answer is explicitly called out
in the assessment brief as the #1 trust risk -- this module is what converts "low signal"
into "escalate" rather than "guess and answer anyway".
"""
from dataclasses import dataclass

LOW_CONFIDENCE_THRESHOLD = 0.55


@dataclass
class ConfidenceAssessment:
    score: float
    should_escalate: bool
    reason: str


def assess_confidence(
    retrieval_hit: bool,
    authority_resolved: bool,
    tool_returned_needs_verification: bool,
    conflicting_sources: bool,
) -> ConfidenceAssessment:
    score = 1.0

    if not retrieval_hit:
        score -= 0.4
    if not authority_resolved:
        score -= 0.3
    if tool_returned_needs_verification:
        score -= 0.5
    if conflicting_sources:
        score -= 0.3

    score = max(0.0, min(1.0, score))
    should_escalate = (
        score < LOW_CONFIDENCE_THRESHOLD
        or tool_returned_needs_verification
        or conflicting_sources
    )

    reason_bits = []
    if not retrieval_hit:
        reason_bits.append("no matching document found")
    if not authority_resolved:
        reason_bits.append("no authoritative current source for this clause")
    if tool_returned_needs_verification:
        reason_bits.append("required data point is unknown/unverified")
    if conflicting_sources:
        reason_bits.append("sources disagree and precedence could not fully resolve it")

    reason = "; ".join(reason_bits) if reason_bits else "sufficient authoritative evidence found"
    return ConfidenceAssessment(score=round(score, 2), should_escalate=should_escalate, reason=reason)
