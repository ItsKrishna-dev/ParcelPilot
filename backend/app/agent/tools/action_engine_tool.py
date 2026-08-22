"""
Tool 3/3: State-changing action (mocked locally). Enforces the "confirmation before
action" requirement structurally: `confirmed=False` (the default) NEVER writes anything --
it only returns a draft + a single-use, TTL-bound pending_action_id. The write only happens
on a second call carrying that exact pending_action_id with confirmed=True. This means a
prompt-injection attempt or model hallucination cannot cause a real write on the first pass.
"""
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.agent.schemas import ActionEngineInput, ActionEngineOutput, ToolResultStatus
from app.db.models import PendingAction, Escalation, AuditLog, Ticket
from app.config import settings, dataset_snapshot_time


def _draft_description(action_type: str, payload: dict) -> str:
    if action_type == "create_escalation":
        return (f"Escalate {payload.get('ticket_id', payload.get('account_id'))} "
                f"(severity={payload.get('severity', 'unspecified')}): {payload.get('reason', '')}")
    if action_type == "update_ticket_status":
        return f"Update {payload.get('ticket_id')} status to '{payload.get('new_status')}'."
    if action_type == "create_follow_up_task":
        return f"Create follow-up task for {payload.get('account_id')}: {payload.get('description', '')}"
    return "Unknown action."


def run_action_engine(
    db: Session, tool_input: ActionEngineInput, actor_user_id: str, actor_role: str,
) -> ActionEngineOutput:
    if not tool_input.confirmed:
        pending_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(seconds=settings.pending_action_ttl_seconds)
        pending = PendingAction(
            pending_action_id=pending_id, action_type=tool_input.action_type,
            payload=tool_input.payload, created_by=actor_user_id, expires_at=expires_at,
        )
        db.add(pending)
        db.commit()
        return ActionEngineOutput(
            status=ToolResultStatus.OK,
            pending_action_id=pending_id,
            draft={"action_type": tool_input.action_type, "payload": tool_input.payload,
                   "description": _draft_description(tool_input.action_type, tool_input.payload)},
            message="Draft prepared. Explicit user confirmation is required before this action executes.",
        )

    pending = db.query(PendingAction).filter(
        PendingAction.pending_action_id == tool_input.pending_action_id
    ).first()

    if pending is None:
        return ActionEngineOutput(status=ToolResultStatus.OUT_OF_SCOPE,
                                    message="No matching pending action found.")
    if pending.consumed:
        return ActionEngineOutput(status=ToolResultStatus.OUT_OF_SCOPE,
                                    message="This pending action was already executed (idempotency guard).")
    if pending.expires_at < datetime.utcnow():
        return ActionEngineOutput(status=ToolResultStatus.OUT_OF_SCOPE,
                                    message="Pending action expired; please re-issue the request.")

    payload = pending.payload
    result_payload = {}

    if pending.action_type == "create_escalation":
        esc = Escalation(
            escalation_id=str(uuid.uuid4()), ticket_id=payload.get("ticket_id"),
            account_id=payload["account_id"], reason=payload.get("reason", ""),
            severity=payload.get("severity"), created_by=actor_user_id,
        )
        db.add(esc)
        result_payload = {"escalation_id": esc.escalation_id}

    elif pending.action_type == "update_ticket_status":
        ticket = db.query(Ticket).filter(Ticket.ticket_id == payload["ticket_id"]).first()
        if ticket is None:
            return ActionEngineOutput(status=ToolResultStatus.NEEDS_VERIFICATION,
                                        message="Ticket not found.")
        ticket.status = payload["new_status"]
        result_payload = {"ticket_id": ticket.ticket_id, "new_status": ticket.status}

    elif pending.action_type == "create_follow_up_task":
        result_payload = {"task": payload.get("description"), "account_id": payload.get("account_id")}

    pending.consumed = True
    db.add(AuditLog(
        actor_user_id=actor_user_id, actor_role=actor_role, action_type=pending.action_type,
        target_account_id=payload.get("account_id"), payload=payload, result="executed",
    ))
    db.commit()

    return ActionEngineOutput(
        status=ToolResultStatus.OK, result=result_payload,
        message=f"{pending.action_type} executed and logged to audit_log.",
    )
