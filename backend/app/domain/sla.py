"""
SLA target lookup and breach checking.

Contract SLA values are passed in by the structured contract-rule resolver.
This domain module does not know customer/account-specific IDs.
"""

from dataclasses import dataclass
from datetime import datetime


DEFAULT_SLA_MINUTES = {
    "Enterprise": {
        "P1": 30,
        "P2": 120,
        "P3": 8 * 60,
    },
    "Growth": {
        "P1": 120,
        "P2": 240,
        "P3": 2 * 8 * 60,
    },
    "Standard": {
        "P1": 240,
        "P2": 24 * 60,
        "P3": 2 * 8 * 60,
    },
}


@dataclass
class SlaResult:
    target_minutes: int
    elapsed_minutes: float
    breached: bool
    minutes_to_breach: float
    authority_source: str


def get_sla_target_minutes(
    plan: str,
    severity: str,
    contract_sla_minutes: dict[str, int | None] | None = None,
) -> tuple[int, str]:
    contract_sla_minutes = contract_sla_minutes or {}

    contract_target = contract_sla_minutes.get(severity)

    if contract_target is not None:
        return (
            int(contract_target),
            "signed customer agreement "
            "(overrides default SLA)",
        )

    plan_targets = DEFAULT_SLA_MINUTES.get(
        plan,
        DEFAULT_SLA_MINUTES["Standard"],
    )

    return (
        int(plan_targets.get(severity, plan_targets["P3"])),
        "01_Support_Policy_v3_CURRENT s3",
    )


def check_sla_breach(
    account_id: str,
    plan: str,
    severity: str,
    ticket_created_at: datetime,
    now: datetime,
    contract_sla_minutes: dict[str, int | None] | None = None,
) -> SlaResult:
    target_minutes, source = get_sla_target_minutes(
        plan=plan,
        severity=severity,
        contract_sla_minutes=contract_sla_minutes,
    )

    elapsed = (
        now - ticket_created_at
    ).total_seconds() / 60

    return SlaResult(
        target_minutes=target_minutes,
        elapsed_minutes=round(elapsed, 1),
        breached=elapsed > target_minutes,
        minutes_to_breach=round(target_minutes - elapsed, 1),
        authority_source=source,
    )