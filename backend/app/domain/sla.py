"""
SLA target lookup + breach checking. Default targets from 01_Support_Policy_v3_CURRENT;
a signed agreement may replace these per-account (Northstar, LumenWorks both do).
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Severity(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


DEFAULT_SLA_MINUTES = {
    "Enterprise": {"P1": 30, "P2": 120, "P3": 8 * 60},
    "Growth": {"P1": 120, "P2": 240, "P3": 2 * 8 * 60},
    "Standard": {"P1": 240, "P2": 24 * 60, "P3": 2 * 8 * 60},
}

CONTRACT_SLA_MINUTES = {
    "ACCT-001": {"P1": 15, "P2": 60, "P3": 8 * 60},        # Northstar Enterprise Agreement s1
    "ACCT-002": {"P1": 120, "P2": 240, "P3": 2 * 8 * 60},  # LumenWorks Service Agreement s1
}


@dataclass
class SlaResult:
    target_minutes: int
    elapsed_minutes: float
    breached: bool
    minutes_to_breach: float
    authority_source: str


def get_sla_target_minutes(account_id: str, plan: str, severity: str) -> tuple[int, str]:
    if account_id in CONTRACT_SLA_MINUTES and severity in CONTRACT_SLA_MINUTES[account_id]:
        return CONTRACT_SLA_MINUTES[account_id][severity], "signed customer agreement (overrides default SLA)"
    plan_targets = DEFAULT_SLA_MINUTES.get(plan, DEFAULT_SLA_MINUTES["Standard"])
    return plan_targets.get(severity, plan_targets["P3"]), "01_Support_Policy_v3_CURRENT s3"


def check_sla_breach(account_id: str, plan: str, severity: str,
                      ticket_created_at: datetime, now: datetime) -> SlaResult:
    target_minutes, source = get_sla_target_minutes(account_id, plan, severity)
    elapsed = (now - ticket_created_at).total_seconds() / 60
    return SlaResult(
        target_minutes=target_minutes,
        elapsed_minutes=round(elapsed, 1),
        breached=elapsed > target_minutes,
        minutes_to_breach=round(target_minutes - elapsed, 1),
        authority_source=source,
    )
