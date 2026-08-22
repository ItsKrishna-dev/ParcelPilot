from datetime import datetime, timedelta
from app.domain.service_credit import calc_service_credit, CreditDecision

NOW = datetime(2026, 8, 16, 11, 0, 0)


def test_unknown_fault_needs_verification():
    r = calc_service_credit(
        pickup_window_end=NOW - timedelta(hours=3), pickup_actual_at=None, now=NOW,
        carrier_fault=None, customer_fault=False, shipment_fee_inr=2400,
    )
    assert r.decision == CreditDecision.NEEDS_VERIFICATION


def test_carrier_not_at_fault_not_eligible():
    r = calc_service_credit(
        pickup_window_end=NOW - timedelta(hours=3), pickup_actual_at=None, now=NOW,
        carrier_fault=False, customer_fault=False, shipment_fee_inr=2400,
    )
    assert r.decision == CreditDecision.NOT_ELIGIBLE


def test_default_credit_capped_at_500():
    r = calc_service_credit(
        pickup_window_end=NOW - timedelta(hours=3), pickup_actual_at=None, now=NOW,
        carrier_fault=True, customer_fault=False, shipment_fee_inr=10000,
    )
    assert r.decision == CreditDecision.ELIGIBLE
    assert r.credit_inr == 500.0


def test_lumenworks_fixed_credit_overrides_default():
    """LumenWorks contract: >4h threshold, fixed INR 300 credit."""
    r = calc_service_credit(
        pickup_window_end=NOW - timedelta(hours=5), pickup_actual_at=None, now=NOW,
        carrier_fault=True, customer_fault=False, shipment_fee_inr=2400,
        contract_delay_threshold_hours=4.0, contract_fixed_credit_inr=300.0,
    )
    assert r.decision == CreditDecision.ELIGIBLE
    assert r.credit_inr == 300.0


def test_below_contract_threshold_not_eligible():
    r = calc_service_credit(
        pickup_window_end=NOW - timedelta(hours=3), pickup_actual_at=None, now=NOW,
        carrier_fault=True, customer_fault=False, shipment_fee_inr=2400,
        contract_delay_threshold_hours=4.0, contract_fixed_credit_inr=300.0,
    )
    assert r.decision == CreditDecision.NOT_ELIGIBLE


def test_credit_above_threshold_requires_manager_approval():
    r = calc_service_credit(
        pickup_window_end=NOW - timedelta(hours=3), pickup_actual_at=None, now=NOW,
        carrier_fault=True, customer_fault=False, shipment_fee_inr=50000,
        contract_credit_cap_inr=5000,
    )
    assert r.requires_manager_approval is True
