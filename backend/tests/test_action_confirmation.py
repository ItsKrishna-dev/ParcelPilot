"""
Verifies the two-phase confirm-before-act contract: the first call NEVER writes, and the
second call only succeeds with the exact pending_action_id, exactly once (idempotency).
"""
from app.agent.tools.action_engine_tool import run_action_engine
from app.agent.schemas import ActionEngineInput, ToolResultStatus
from app.db.models import Escalation


def test_unconfirmed_call_does_not_create_escalation(db_session):
    before = db_session.query(Escalation).count()
    out = run_action_engine(
        db_session,
        ActionEngineInput(action_type="create_escalation",
                           payload={"account_id": "ACCT-001", "reason": "test", "severity": "P2"},
                           confirmed=False),
        actor_user_id="agent-rohit", actor_role="support_agent",
    )
    after = db_session.query(Escalation).count()
    assert after == before
    assert out.pending_action_id is not None
    assert out.draft is not None


def test_confirmed_call_creates_escalation_exactly_once(db_session):
    draft = run_action_engine(
        db_session,
        ActionEngineInput(action_type="create_escalation",
                           payload={"account_id": "ACCT-001", "reason": "test", "severity": "P1"},
                           confirmed=False),
        actor_user_id="agent-rohit", actor_role="support_agent",
    )
    before = db_session.query(Escalation).count()

    confirm_input = ActionEngineInput(
        action_type="create_escalation",
        payload={"account_id": "ACCT-001", "reason": "test", "severity": "P1"},
        confirmed=True, pending_action_id=draft.pending_action_id,
    )
    out1 = run_action_engine(db_session, confirm_input, actor_user_id="agent-rohit", actor_role="support_agent")
    assert out1.status == ToolResultStatus.OK
    after_first = db_session.query(Escalation).count()
    assert after_first == before + 1

    out2 = run_action_engine(db_session, confirm_input, actor_user_id="agent-rohit", actor_role="support_agent")
    assert out2.status == ToolResultStatus.OUT_OF_SCOPE
    after_second = db_session.query(Escalation).count()
    assert after_second == after_first
