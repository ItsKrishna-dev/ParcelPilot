"""
Comprehensive verification test suite for all 12 Golden Assessment Cases (A through L).
"""

from datetime import datetime, timedelta
from app.agent.schemas import (
    ActionEngineInput,
    DocSearchInput,
    StructuredLookupInput,
    ToolResultStatus,
)
from app.agent.tools.action_engine_tool import run_action_engine
from app.agent.tools.doc_search_tool import run_doc_search
from app.agent.tools.structured_data_tool import run_structured_lookup
from app.db.models import Escalation
from app.domain.cancellation import CancellationDecision
from app.domain.known_issues import KNOWN_ISSUES
from app.domain.service_credit import CreditDecision, calc_service_credit
from app.retrieval.source_authority import resolve_authority

NOW = datetime(2026, 8, 16, 11, 0, 0)


# Case A: Northstar cancellation override
def test_case_a_northstar_cancellation_override(db_session):
    tool_input = StructuredLookupInput(
        entity="cancellation_calc",
        filters={"order_id": "ORD-1001"},
    )
    result = run_structured_lookup(
        db_session, tool_input, role="customer", session_account_id="ACCT-001"
    )
    assert result.status == ToolResultStatus.OK
    assert result.data["decision"] == CancellationDecision.ALLOWED_NO_FEE.value
    assert result.data["fee_inr"] == 0.0
    assert "agreement" in result.authority_source.lower()


# Case B: LumenWorks late cancellation
def test_case_b_lumenworks_late_cancellation(db_session):
    tool_input = StructuredLookupInput(
        entity="cancellation_calc",
        filters={"order_id": "ORD-2001"},
    )
    result = run_structured_lookup(
        db_session, tool_input, role="customer", session_account_id="ACCT-002"
    )
    assert result.status == ToolResultStatus.OK
    assert result.data["decision"] == CancellationDecision.ALLOWED_WITH_FEE.value
    assert result.data["fee_inr"] == 250.0
    assert "03_Cancellation_and_Service_Credit_SOP_v4" in result.authority_source


# Case C: Beacon within cancellation window
def test_case_c_beacon_within_cancellation_window(db_session):
    tool_input = StructuredLookupInput(
        entity="cancellation_calc",
        filters={"order_id": "ORD-3001"},
    )
    result = run_structured_lookup(
        db_session, tool_input, role="customer", session_account_id="ACCT-003"
    )
    assert result.status == ToolResultStatus.OK
    assert result.data["decision"] == CancellationDecision.ALLOWED_NO_FEE.value
    assert result.data["fee_inr"] == 0.0
    assert "03_Cancellation_and_Service_Credit_SOP_v4" in result.authority_source


# Case D: Picked-up cancellation
def test_case_d_picked_up_cancellation(db_session):
    tool_input = StructuredLookupInput(
        entity="cancellation_calc",
        filters={"order_id": "ORD-1002"},
    )
    result = run_structured_lookup(
        db_session, tool_input, role="customer", session_account_id="ACCT-001"
    )
    assert result.status == ToolResultStatus.OK
    assert (
        result.data["decision"]
        == CancellationDecision.NOT_ALLOWED_USE_RETURN_TO_ORIGIN.value
    )
    assert result.data["fee_inr"] == 0.0


# Case E: LumenWorks failed-pickup credit (4.5h delay on BOOKED order with null actual_at)
def test_case_e_lumenworks_failed_pickup_credit(db_session):
    tool_input = StructuredLookupInput(
        entity="service_credit_calc",
        filters={"order_id": "ORD-2002"},
    )
    result = run_structured_lookup(
        db_session, tool_input, role="customer", session_account_id="ACCT-002"
    )
    assert result.status == ToolResultStatus.OK
    assert result.data["decision"] == CreditDecision.ELIGIBLE.value
    assert result.data["credit_inr"] == 300.0
    assert result.data["requires_manager_approval"] is False
    assert "agreement" in result.authority_source.lower()


# Case F: Missing fault data returns NEEDS_VERIFICATION
def test_case_f_missing_fault_data():
    r = calc_service_credit(
        pickup_window_end=NOW - timedelta(hours=3),
        pickup_actual_at=None,
        now=NOW,
        carrier_fault=None,
        customer_fault=False,
        shipment_fee_inr=2400,
    )
    assert r.decision == CreditDecision.NEEDS_VERIFICATION


# Case G: SwiftShip KI-211 known issue
def test_case_g_swiftship_ki211():
    issue = next((i for i in KNOWN_ISSUES if i.issue_id == "KI-211"), None)
    assert issue is not None
    assert "20 minutes" in issue.guidance or "delay" in issue.guidance.lower()


# Case H: Bulk upload KI-208 known issue
def test_case_h_bulk_upload_ki208():
    issue = next((i for i in KNOWN_ISSUES if i.issue_id == "KI-208"), None)
    assert issue is not None
    assert "3,000" in issue.guidance or "3000" in issue.guidance


# Case I: Deprecated policy v2 is never authoritative current source
def test_case_i_deprecated_policy(db_session):
    resolution = resolve_authority(db_session, account_id="ACCT-003", clause="sla")
    assert resolution.winning_source_type != "deprecated"
    assert resolution.winning_source_type == "support_policy"


# Case J: Cross-account security isolation
def test_case_j_cross_account_security(db_session):
    tool_input = StructuredLookupInput(
        entity="order",
        filters={"account_id": "ACCT-002"},
    )
    # ACCT-001 (Northstar) customer asking for ACCT-002 (LumenWorks) data
    result = run_structured_lookup(
        db_session, tool_input, role="customer", session_account_id="ACCT-001"
    )
    assert result.status == ToolResultStatus.ACCESS_DENIED
    assert "not access" in result.reason.lower() or "denied" in result.reason.lower()


# Case K: Unknown record handling
def test_case_k_unknown_record(db_session):
    tool_input = StructuredLookupInput(
        entity="cancellation_calc",
        filters={"order_id": "ORD-9999"},
    )
    result = run_structured_lookup(
        db_session, tool_input, role="customer", session_account_id="ACCT-001"
    )
    assert result.status == ToolResultStatus.NEEDS_VERIFICATION
    assert "not found" in result.reason.lower()


# Case L: Action confirmation two-phase commit and idempotency
def test_case_l_action_confirmation(db_session):
    before_count = db_session.query(Escalation).count()

    # Step 1: Draft only (confirmed=False)
    draft_out = run_action_engine(
        db_session,
        ActionEngineInput(
            action_type="create_escalation",
            payload={"account_id": "ACCT-001", "ticket_id": "TKT-501", "reason": "System down", "severity": "P1"},
            confirmed=False,
        ),
        actor_user_id="agent-rohit",
        actor_role="support_agent",
    )
    assert draft_out.status == ToolResultStatus.OK
    assert draft_out.pending_action_id is not None
    assert db_session.query(Escalation).count() == before_count

    # Step 2: Confirmation with exact pending_action_id (confirmed=True)
    confirm_out = run_action_engine(
        db_session,
        ActionEngineInput(
            action_type="create_escalation",
            payload={"account_id": "ACCT-001", "ticket_id": "TKT-501", "reason": "System down", "severity": "P1"},
            confirmed=True,
            pending_action_id=draft_out.pending_action_id,
        ),
        actor_user_id="agent-rohit",
        actor_role="support_agent",
    )
    assert confirm_out.status == ToolResultStatus.OK
    assert db_session.query(Escalation).count() == before_count + 1

    # Step 3: Replay with consumed pending_action_id is rejected
    replay_out = run_action_engine(
        db_session,
        ActionEngineInput(
            action_type="create_escalation",
            payload={"account_id": "ACCT-001", "ticket_id": "TKT-501", "reason": "System down", "severity": "P1"},
            confirmed=True,
            pending_action_id=draft_out.pending_action_id,
        ),
        actor_user_id="agent-rohit",
        actor_role="support_agent",
    )
    assert replay_out.status == ToolResultStatus.OUT_OF_SCOPE
    assert db_session.query(Escalation).count() == before_count + 1
