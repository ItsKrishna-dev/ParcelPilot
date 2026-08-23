"""
Deterministic failed-pickup service-credit calculation.

Default policy (03_Cancellation_and_Service_Credit_SOP_v4 s2):
  Eligible when pickup is >2 hours past the scheduled pickup-window END, carrier is at
  fault, and customer is NOT at fault. Default credit = min(INR 500, 10% of shipment fee).
  A signed agreement may replace the delay threshold and/or credit amount/cap
  (e.g. LumenWorks: >4 hours, fixed INR 300; Northstar: default rule but capped at
  INR 5,000 aggregate per month).

Critical edge case (SOP s3): "Do not promise a credit when carrier fault, pickup timing,
or customer fault is unknown." -> returns NEEDS_VERIFICATION rather than guessing.
Credits above the manager-approval threshold must be routed for confirmation, never
auto-approved.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from app.config import settings


class CreditDecision(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    NEEDS_VERIFICATION = "NEEDS_VERIFICATION"


@dataclass
class ServiceCreditResult:
    decision: CreditDecision
    credit_inr: float
    requires_manager_approval: bool
    reason: str
    authority_source: str


DEFAULT_DELAY_THRESHOLD_HOURS = 2
DEFAULT_CREDIT_CAP_INR = 500.0
DEFAULT_CREDIT_PCT_OF_FEE = 0.10


def calc_service_credit(
    pickup_window_end: datetime | None,
    pickup_actual_at: datetime | None,
    now: datetime,
    carrier_fault: bool | None,
    customer_fault: bool | None,
    shipment_fee_inr: float,
    contract_delay_threshold_hours: float | None = None,
    contract_fixed_credit_inr: float | None = None,
    contract_credit_cap_inr: float | None = None,
) -> ServiceCreditResult:
    if now.tzinfo is not None:
        now = now.replace(tzinfo=None)
    if pickup_window_end is not None and pickup_window_end.tzinfo is not None:
        pickup_window_end = pickup_window_end.replace(tzinfo=None)
    if pickup_actual_at is not None and pickup_actual_at.tzinfo is not None:
        pickup_actual_at = pickup_actual_at.replace(tzinfo=None)

    if carrier_fault is None or customer_fault is None:
        return ServiceCreditResult(
            CreditDecision.NEEDS_VERIFICATION, 0.0, False,
            "Carrier fault / customer fault is unknown. Per SOP, do not promise a credit "
            "until fault is verified.",
            "03_Cancellation_and_Service_Credit_SOP_v4 s3",
        )

    if not carrier_fault or customer_fault:
        return ServiceCreditResult(
            CreditDecision.NOT_ELIGIBLE, 0.0, False,
            "Not eligible: carrier is not at fault, or customer is at fault.",
            "03_Cancellation_and_Service_Credit_SOP_v4 s2",
        )

    if pickup_window_end is None:
        return ServiceCreditResult(
            CreditDecision.NEEDS_VERIFICATION, 0.0, False,
            "pickup_window_end is missing; cannot compute delay against the threshold.",
            "n/a",
        )

    reference_pickup_time = pickup_actual_at or now
    delay = reference_pickup_time - pickup_window_end
    threshold_hours = contract_delay_threshold_hours if contract_delay_threshold_hours is not None \
        else DEFAULT_DELAY_THRESHOLD_HOURS

    if delay < timedelta(hours=threshold_hours):
        return ServiceCreditResult(
            CreditDecision.NOT_ELIGIBLE, 0.0, False,
            f"Delay of {delay.total_seconds()/3600:.1f}h is below the "
            f"{threshold_hours}h eligibility threshold.",
            "signed customer agreement" if contract_delay_threshold_hours is not None
            else "03_Cancellation_and_Service_Credit_SOP_v4 s2",
        )

    if contract_fixed_credit_inr is not None:
        credit = contract_fixed_credit_inr
        source = "signed customer agreement (overrides default credit amount)"
        if contract_credit_cap_inr is not None:
            credit = min(credit, contract_credit_cap_inr)
    else:
        effective_cap = (
            contract_credit_cap_inr
            if contract_credit_cap_inr is not None
            else DEFAULT_CREDIT_CAP_INR
        )
        credit = min(effective_cap, shipment_fee_inr * DEFAULT_CREDIT_PCT_OF_FEE)
        source = (
            "signed customer agreement (overrides default credit cap)"
            if contract_credit_cap_inr is not None
            else "03_Cancellation_and_Service_Credit_SOP_v4 s2"
        )

    requires_approval = credit > settings.manager_approval_threshold_inr

    return ServiceCreditResult(
        CreditDecision.ELIGIBLE, round(credit, 2), requires_approval,
        f"Delay of {delay.total_seconds()/3600:.1f}h exceeds the {threshold_hours}h threshold, "
        f"carrier at fault, customer not at fault -> INR {credit:.0f} credit.",
        source,
    )
