from datetime import datetime, timedelta
from app.domain.cancellation import calc_cancellation_fee, CancellationDecision


NOW = datetime(2026, 8, 16, 11, 0, 0)


def test_draft_always_free():
    r = calc_cancellation_fee("DRAFT", booked_at=None, now=NOW)
    assert r.decision == CancellationDecision.ALLOWED_NO_FEE
    assert r.fee_inr == 0.0


def test_delivered_cannot_cancel():
    r = calc_cancellation_fee("DELIVERED", booked_at=NOW - timedelta(days=1), now=NOW)
    assert r.decision == CancellationDecision.NOT_ALLOWED_DELIVERED


def test_picked_up_cannot_cancel():
    r = calc_cancellation_fee("PICKED_UP", booked_at=NOW - timedelta(hours=1), now=NOW)
    assert r.decision == CancellationDecision.NOT_ALLOWED_USE_RETURN_TO_ORIGIN


def test_booked_within_free_window():
    r = calc_cancellation_fee("BOOKED", booked_at=NOW - timedelta(minutes=10), now=NOW)
    assert r.decision == CancellationDecision.ALLOWED_NO_FEE
    assert r.fee_inr == 0.0


def test_booked_after_free_window_charges_fee():
    r = calc_cancellation_fee("BOOKED", booked_at=NOW - timedelta(minutes=90), now=NOW)
    assert r.decision == CancellationDecision.ALLOWED_WITH_FEE
    assert r.fee_inr == 250.0


def test_contract_waiver_overrides_fee_even_when_late():
    """Northstar: agreement waives the fee regardless of elapsed time (ORD-1001 style case)."""
    r = calc_cancellation_fee(
        "BOOKED", booked_at=NOW - timedelta(minutes=90), now=NOW, contract_waives_fee=True,
    )
    assert r.decision == CancellationDecision.ALLOWED_NO_FEE
    assert r.fee_inr == 0.0
    assert "agreement" in r.authority_source


def test_missing_booked_at_needs_verification():
    r = calc_cancellation_fee("BOOKED", booked_at=None, now=NOW)
    assert r.decision == CancellationDecision.NEEDS_VERIFICATION


def test_unrecognized_status_needs_verification():
    r = calc_cancellation_fee("UNKNOWN_STATUS", booked_at=NOW, now=NOW)
    assert r.decision == CancellationDecision.NEEDS_VERIFICATION
