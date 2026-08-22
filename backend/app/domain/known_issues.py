"""
Known-issue matcher. Before the agent concludes a real product defect exists (e.g. "status
still shows BOOKED after pickup"), it must check whether a known issue already explains the
symptom (04_Product_Operations_Guide_and_Known_Issues) -- otherwise it will confidently
misdiagnose a webhook delay (KI-211) as a data-integrity bug, or a plan limitation (KI-208)
as a policy violation.
"""
from dataclasses import dataclass


@dataclass
class KnownIssue:
    issue_id: str
    title: str
    status: str
    keywords: list[str]
    guidance: str


KNOWN_ISSUES: list[KnownIssue] = [
    KnownIssue(
        issue_id="KI-208",
        title="Bulk Upload failures on large CSVs",
        status="Investigating",
        keywords=["bulk upload", "csv", "upload fails", "row", "rows"],
        guidance=(
            "Some Growth/Enterprise customers see intermittent failures on CSV uploads above "
            "~3,000 rows even though the supported product limit is 5,000 rows. This is a "
            "known bug, not a plan-capability limit. Workaround: split uploads below 3,000 rows; "
            "individual shipment creation is unaffected."
        ),
    ),
    KnownIssue(
        issue_id="KI-211",
        title="SwiftShip pickup webhook delay",
        status="Monitoring",
        keywords=["still shows booked", "swiftship", "webhook", "pickup delay", "status not updated"],
        guidance=(
            "SwiftShip pickup-confirmation webhooks can arrive up to 20 minutes late. A parcel "
            "may be physically collected while ParcelPilot still shows BOOKED. Verify carrier "
            "status or wait through the delay window before declaring a pickup did not occur."
        ),
    ),
    KnownIssue(
        issue_id="KI-176",
        title="Address validation",
        status="Resolved",
        keywords=["address validation"],
        guidance=(
            "Resolved 18 July 2026. Do not use this resolved issue to explain new incidents "
            "unless evidence specifically matches it."
        ),
    ),
]


def match_known_issue(ticket_text: str) -> KnownIssue | None:
    text_lower = (ticket_text or "").lower()
    for issue in KNOWN_ISSUES:
        if any(kw in text_lower for kw in issue.keywords):
            return issue
    return None
