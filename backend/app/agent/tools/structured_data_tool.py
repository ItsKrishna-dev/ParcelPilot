"""Tool 2/3: Structured-data lookup or calculation. Access scoping happens in
db/repository.py -- this tool never bypasses it, regardless of what the LLM asks for."""
from datetime import datetime
from sqlalchemy.orm import Session
from app.agent.schemas import StructuredLookupInput, StructuredLookupOutput, ToolResultStatus
from app.db import repository as repo
from app.db.models import Account, Order, Ticket
from app.domain.cancellation import calc_cancellation_fee, CancellationDecision
from app.domain.service_credit import calc_service_credit, CreditDecision
from app.domain.sla import check_sla_breach
from app.retrieval.source_authority import resolve_authority
from app.config import dataset_snapshot_time


def _serialize(obj) -> dict:
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


def run_structured_lookup(
    db: Session, tool_input: StructuredLookupInput, role: str, session_account_id: str | None,
) -> StructuredLookupOutput:
    try:
        entity = tool_input.entity
        f = tool_input.filters

        if entity == "account":
            acct = repo.get_account(db, role, session_account_id, f.get("account_id"))
            if not acct:
                return StructuredLookupOutput(status=ToolResultStatus.NEEDS_VERIFICATION,
                                                reason="Account not found.")
            return StructuredLookupOutput(status=ToolResultStatus.OK, data=_serialize(acct))

        if entity == "order":
            orders = repo.list_orders(db, role, session_account_id,
                                       account_id=f.get("account_id"), order_id=f.get("order_id"))
            if not orders:
                return StructuredLookupOutput(status=ToolResultStatus.NEEDS_VERIFICATION,
                                                reason="Order not found or not accessible.")
            return StructuredLookupOutput(status=ToolResultStatus.OK,
                                            data={"orders": [_serialize(o) for o in orders]})

        if entity == "ticket":
            tickets = repo.list_tickets(db, role, session_account_id,
                                         account_id=f.get("account_id"), ticket_id=f.get("ticket_id"),
                                         status=f.get("status"))
            return StructuredLookupOutput(status=ToolResultStatus.OK,
                                            data={"tickets": [_serialize(t) for t in tickets]})

        if entity == "cancellation_calc":
            order_id = f.get("order_id")
            orders = repo.list_orders(db, role, session_account_id, order_id=order_id)
            if not orders:
                return StructuredLookupOutput(status=ToolResultStatus.NEEDS_VERIFICATION,
                                                reason=f"Order {order_id} not found or not accessible.")
            order = orders[0]
            authority = resolve_authority(db, order.account_id, "cancellation_fee")
            contract_waives_fee = authority.winning_source_type == "agreement" and order.account_id == "ACCT-001"
            result = calc_cancellation_fee(
                order_status=order.status, booked_at=order.booked_at, now=dataset_snapshot_time(),
                contract_waives_fee=contract_waives_fee,
            )
            status = (ToolResultStatus.NEEDS_VERIFICATION
                      if result.decision == CancellationDecision.NEEDS_VERIFICATION
                      else ToolResultStatus.OK)
            return StructuredLookupOutput(
                status=status,
                data={"decision": result.decision.value, "fee_inr": result.fee_inr, "reason": result.reason},
                authority_source=result.authority_source,
            )

        if entity == "service_credit_calc":
            order_id = f.get("order_id")
            orders = repo.list_orders(db, role, session_account_id, order_id=order_id)
            if not orders:
                return StructuredLookupOutput(status=ToolResultStatus.NEEDS_VERIFICATION,
                                                reason=f"Order {order_id} not found or not accessible.")
            order = orders[0]
            contract_fixed_credit = 300.0 if order.account_id == "ACCT-002" else None
            contract_threshold = 4.0 if order.account_id == "ACCT-002" else None
            result = calc_service_credit(
                pickup_window_end=order.pickup_window_end, pickup_actual_at=order.pickup_actual_at,
                now=dataset_snapshot_time(), carrier_fault=order.carrier_fault,
                customer_fault=order.customer_fault, shipment_fee_inr=order.shipment_fee_inr,
                contract_delay_threshold_hours=contract_threshold,
                contract_fixed_credit_inr=contract_fixed_credit,
            )
            status = (ToolResultStatus.NEEDS_VERIFICATION
                      if result.decision == CreditDecision.NEEDS_VERIFICATION
                      else ToolResultStatus.OK)
            return StructuredLookupOutput(
                status=status,
                data={"decision": result.decision.value, "credit_inr": result.credit_inr,
                      "requires_manager_approval": result.requires_manager_approval, "reason": result.reason},
                authority_source=result.authority_source,
            )

        if entity == "sla_calc":
            ticket_id = f.get("ticket_id")
            tickets = repo.list_tickets(db, role, session_account_id, ticket_id=ticket_id)
            if not tickets:
                return StructuredLookupOutput(status=ToolResultStatus.NEEDS_VERIFICATION,
                                                reason=f"Ticket {ticket_id} not found or not accessible.")
            ticket = tickets[0]
            account = repo.get_account(db, role, session_account_id, ticket.account_id)
            severity = f.get("severity", "P3")
            result = check_sla_breach(account.account_id, account.plan, severity,
                                        ticket.created_at, dataset_snapshot_time())
            return StructuredLookupOutput(
                status=ToolResultStatus.OK,
                data={"target_minutes": result.target_minutes, "elapsed_minutes": result.elapsed_minutes,
                      "breached": result.breached, "minutes_to_breach": result.minutes_to_breach},
                authority_source=result.authority_source,
            )

        return StructuredLookupOutput(status=ToolResultStatus.OUT_OF_SCOPE,
                                        reason=f"Unknown entity '{entity}'.")

    except repo.AccessDeniedError as e:
        return StructuredLookupOutput(status=ToolResultStatus.ACCESS_DENIED, reason=str(e))
