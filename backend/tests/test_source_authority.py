"""
Property-based tests over the source_authority_rules table -- proves the resolver picks
contract > SOP > policy correctly for accounts that HAVE a contract, and falls through
cleanly to standard policy for accounts that don't (Beacon Retail, Axis Labs), without
needing an LLM call.
"""
import pytest
from app.retrieval.source_authority import resolve_authority


@pytest.mark.parametrize("account_id,clause,expected_source", [
    ("ACCT-001", "cancellation_fee", "agreement"),   # Northstar has a contract -> wins
    ("ACCT-002", "service_credit", "agreement"),      # LumenWorks has a contract -> wins
    ("ACCT-003", "cancellation_fee", "sop"),          # Beacon Retail: no contract -> falls to SOP
    ("ACCT-004", "sla", "support_policy"),            # Axis Labs: no contract -> falls to policy
])
def test_authority_resolution(db_session, account_id, clause, expected_source):
    resolution = resolve_authority(db_session, account_id, clause)
    assert resolution.winning_source_type == expected_source


def test_deprecated_policy_never_wins(db_session):
    """DEPRECATED support policy must never be returned as the winning current source."""
    resolution = resolve_authority(db_session, "ACCT-003", "sla")
    assert resolution.winning_source_type != "deprecated"
