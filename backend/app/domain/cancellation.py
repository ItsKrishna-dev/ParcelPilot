"""
Deterministic cancellation-fee calculation. The LLM decides WHICH rule applies (via
doc_search + source_authority resolution); this module does the ARITHMETIC. Keeping the
math in tested Python -- not model-generated -- is the guardrail against a confidently
wrong number.

Rules (see docs/03_Cancellation_and_Service_Credit_SOP_v4 + per-account agreements):
  DRAFT               -> free, always
  BOOKED, not PICKED_UP:
      contract explicitly waives fee (e.g. Northstar) -> free, regardless of elapsed time
      within 30 minutes of booking                     -> free
      after 30 minutes                                  -> INR 250 fee
  PICKED_UP           -> cannot cancel; use return-to-origin workflow instead
  DELIVERED           -> cannot cancel
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class CancellationDecision(str, Enum):
    ALLOWED_NO_FEE = "ALLOWED_NO_FEE"
    ALLOWED_WITH_FEE = "ALLOWED_WITH_FEE"
    NOT_ALLOWED_USE_RETURN_TO_ORIGIN = "NOT_ALLOWED_USE_RETURN_TO_ORIGIN"
    NOT_ALLOWED_DELIVERED = "NOT_ALLOWED_DELIVERED"
    NEEDS_VERIFICATION = "NEEDS_VERIFICATION"


@dataclass
class CancellationResult:
    decision: CancellationDecision
    fee_inr: float
    reason: str
    authority_source: str


DEFAULT_FREE_WINDOW_MINUTES = 30
DEFAULT_LATE_CANCELLATION_FEE_INR = 250.0


def calc_cancellation_fee(
    order_status: str,
    booked_at: datetime | None,
    now: datetime,
    contract_waives_fee: bool = False,
    contract_free_window_minutes: int | None = None,
    contract_fee_inr: float | None = None,
    cancellation_requested_at: datetime | None = None,
) -> CancellationResult:
    status = (order_status or "").upper()
    if now.tzinfo is not None:
        now = now.replace(tzinfo=None)
    if booked_at is not None and booked_at.tzinfo is not None:
        booked_at = booked_at.replace(tzinfo=None)
    if cancellation_requested_at is not None and cancellation_requested_at.tzinfo is not None:
        cancellation_requested_at = cancellation_requested_at.replace(tzinfo=None)

    if status == "DRAFT":
        return CancellationResult(
            CancellationDecision.ALLOWED_NO_FEE, 0.0,
            "DRAFT orders may be cancelled with no fee.",
            "03_Cancellation_and_Service_Credit_SOP_v4 s1",
        )

    if status == "DELIVERED":
        return CancellationResult(
            CancellationDecision.NOT_ALLOWED_DELIVERED, 0.0,
            "DELIVERED orders cannot be cancelled.",
            "03_Cancellation_and_Service_Credit_SOP_v4 s1",
        )

    if status == "PICKED_UP":
        return CancellationResult(
            CancellationDecision.NOT_ALLOWED_USE_RETURN_TO_ORIGIN, 0.0,
            "PICKED_UP orders cannot be cancelled; use the return-to-origin workflow.",
            "03_Cancellation_and_Service_Credit_SOP_v4 s1",
        )

    if status == "BOOKED":
        if booked_at is None:
            return CancellationResult(
                CancellationDecision.NEEDS_VERIFICATION, 0.0,
                "booked_at is missing; cannot determine elapsed time for the cancellation window.",
                "n/a",
            )

        if contract_waives_fee:
            return CancellationResult(
                CancellationDecision.ALLOWED_NO_FEE, 0.0,
                "Signed customer agreement waives the cancellation fee for BOOKED orders "
                "regardless of elapsed time; this overrides the default SOP window/fee.",
                "signed customer agreement (overrides SOP)",
            )

        free_window = contract_free_window_minutes or DEFAULT_FREE_WINDOW_MINUTES
        fee = contract_fee_inr if contract_fee_inr is not None else DEFAULT_LATE_CANCELLATION_FEE_INR
        reference_time = cancellation_requested_at or now
        elapsed = reference_time - booked_at

        if elapsed <= timedelta(minutes=free_window):
            return CancellationResult(
                CancellationDecision.ALLOWED_NO_FEE, 0.0,
                f"Cancelled within {free_window} minutes of booking -- no fee.",
                "03_Cancellation_and_Service_Credit_SOP_v4 s1",
            )
        return CancellationResult(
            CancellationDecision.ALLOWED_WITH_FEE, fee,
            f"Cancelled {elapsed.total_seconds()/60:.0f} minutes after booking, "
            f"beyond the {free_window}-minute free window -- INR {fee:.0f} fee applies.",
            "03_Cancellation_and_Service_Credit_SOP_v4 s1",
        )

    return CancellationResult(
        CancellationDecision.NEEDS_VERIFICATION, 0.0,
        f"Unrecognized order status '{order_status}'; escalate for manual review.",
        "n/a",
    )
