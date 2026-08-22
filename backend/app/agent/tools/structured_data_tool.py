"""
Tool 2/3: Structured-data lookup or calculation.

Access scoping happens in db/repository.py and is never bypassed here.
Contract overrides are loaded from structured ContractRule rows extracted
from signed agreement documents. No account ID is hardcoded.
"""

from sqlalchemy.orm import Session

from app.agent.schemas import (
    StructuredLookupInput,
    StructuredLookupOutput,
    ToolResultStatus,
)
from app.config import dataset_snapshot_time
from app.db import repository as repo
from app.domain.cancellation import (
    CancellationDecision,
    calc_cancellation_fee,
)
from app.domain.contract_rules import resolve_contract_overrides
from app.domain.service_credit import (
    CreditDecision,
    calc_service_credit,
)
from app.domain.sla import check_sla_breach


def _serialize(obj) -> dict:
    return {
        column.name: getattr(obj, column.name)
        for column in obj.__table__.columns
    }


def _get_order_for_request(
    db: Session,
    *,
    role: str,
    session_account_id: str | None,
    order_id: str | None,
):
    if not order_id:
        return None

    orders = repo.list_orders(
        db,
        role,
        session_account_id,
        order_id=order_id,
    )

    if not orders:
        return None

    return orders[0]


def _get_ticket_for_request(
    db: Session,
    *,
    role: str,
    session_account_id: str | None,
    ticket_id: str | None,
):
    if not ticket_id:
        return None

    tickets = repo.list_tickets(
        db,
        role,
        session_account_id,
        ticket_id=ticket_id,
    )

    if not tickets:
        return None

    return tickets[0]


def _contract_overrides(
    db: Session,
    *,
    role: str,
    session_account_id: str | None,
    account_id: str,
    clause_type: str,
):
    rules = repo.get_contract_rules(
        db,
        role=role,
        session_account_id=session_account_id,
        account_id=account_id,
        clause_type=clause_type,
    )

    return resolve_contract_overrides(rules)


def run_structured_lookup(
    db: Session,
    tool_input: StructuredLookupInput,
    role: str,
    session_account_id: str | None,
) -> StructuredLookupOutput:
    try:
        entity = tool_input.entity
        filters = tool_input.filters

        if entity == "account":
            account_id = filters.get("account_id")

            if not account_id:
                return StructuredLookupOutput(
                    status=ToolResultStatus.NEEDS_VERIFICATION,
                    reason="account_id is required.",
                )

            account = repo.get_account(
                db,
                role,
                session_account_id,
                account_id,
            )

            if not account:
                return StructuredLookupOutput(
                    status=ToolResultStatus.NEEDS_VERIFICATION,
                    reason="Account not found.",
                )

            return StructuredLookupOutput(
                status=ToolResultStatus.OK,
                data=_serialize(account),
            )

        if entity == "order":
            orders = repo.list_orders(
                db,
                role,
                session_account_id,
                account_id=filters.get("account_id"),
                order_id=filters.get("order_id"),
            )

            if not orders:
                return StructuredLookupOutput(
                    status=ToolResultStatus.NEEDS_VERIFICATION,
                    reason="Order not found or not accessible.",
                )

            return StructuredLookupOutput(
                status=ToolResultStatus.OK,
                data={
                    "orders": [
                        _serialize(order)
                        for order in orders
                    ]
                },
            )

        if entity == "ticket":
            tickets = repo.list_tickets(
                db,
                role,
                session_account_id,
                account_id=filters.get("account_id"),
                ticket_id=filters.get("ticket_id"),
                status=filters.get("status"),
            )

            return StructuredLookupOutput(
                status=ToolResultStatus.OK,
                data={
                    "tickets": [
                        _serialize(ticket)
                        for ticket in tickets
                    ]
                },
            )

        if entity == "cancellation_calc":
            order = _get_order_for_request(
                db,
                role=role,
                session_account_id=session_account_id,
                order_id=filters.get("order_id"),
            )

            if order is None:
                return StructuredLookupOutput(
                    status=ToolResultStatus.NEEDS_VERIFICATION,
                    reason=(
                        f"Order {filters.get('order_id')} "
                        "not found or not accessible."
                    ),
                )

            overrides = _contract_overrides(
                db,
                role=role,
                session_account_id=session_account_id,
                account_id=order.account_id,
                clause_type="cancellation_fee",
            )

            result = calc_cancellation_fee(
                order_status=order.status,
                booked_at=order.booked_at,
                now=dataset_snapshot_time(),
                contract_waives_fee=(
                    overrides.cancellation_fee_waived is True
                ),
                contract_free_window_minutes=(
                    overrides.cancellation_free_window_minutes
                ),
                contract_fee_inr=overrides.cancellation_fee_inr,
            )

            status = (
                ToolResultStatus.NEEDS_VERIFICATION
                if result.decision == CancellationDecision.NEEDS_VERIFICATION
                else ToolResultStatus.OK
            )

            return StructuredLookupOutput(
                status=status,
                data={
                    "decision": result.decision.value,
                    "fee_inr": result.fee_inr,
                    "reason": result.reason,
                    "contract_sources": overrides.sources,
                },
                authority_source=result.authority_source,
            )

        if entity == "service_credit_calc":
            order = _get_order_for_request(
                db,
                role=role,
                session_account_id=session_account_id,
                order_id=filters.get("order_id"),
            )

            if order is None:
                return StructuredLookupOutput(
                    status=ToolResultStatus.NEEDS_VERIFICATION,
                    reason=(
                        f"Order {filters.get('order_id')} "
                        "not found or not accessible."
                    ),
                )

            overrides = _contract_overrides(
                db,
                role=role,
                session_account_id=session_account_id,
                account_id=order.account_id,
                clause_type="service_credit",
            )

            result = calc_service_credit(
                pickup_window_end=order.pickup_window_end,
                pickup_actual_at=order.pickup_actual_at,
                now=dataset_snapshot_time(),
                carrier_fault=order.carrier_fault,
                customer_fault=order.customer_fault,
                shipment_fee_inr=order.shipment_fee_inr,
                contract_delay_threshold_hours=(
                    overrides.service_credit_delay_threshold_hours
                ),
                contract_fixed_credit_inr=(
                    overrides.service_credit_fixed_amount_inr
                ),
                contract_credit_cap_inr=(
                    overrides.service_credit_monthly_cap_inr
                ),
            )

            status = (
                ToolResultStatus.NEEDS_VERIFICATION
                if result.decision == CreditDecision.NEEDS_VERIFICATION
                else ToolResultStatus.OK
            )

            return StructuredLookupOutput(
                status=status,
                data={
                    "decision": result.decision.value,
                    "credit_inr": result.credit_inr,
                    "requires_manager_approval": (
                        result.requires_manager_approval
                    ),
                    "reason": result.reason,
                    "contract_sources": overrides.sources,
                },
                authority_source=result.authority_source,
            )

        if entity == "sla_calc":
            ticket = _get_ticket_for_request(
                db,
                role=role,
                session_account_id=session_account_id,
                ticket_id=filters.get("ticket_id"),
            )

            if ticket is None:
                return StructuredLookupOutput(
                    status=ToolResultStatus.NEEDS_VERIFICATION,
                    reason=(
                        f"Ticket {filters.get('ticket_id')} "
                        "not found or not accessible."
                    ),
                )

            account = repo.get_account(
                db,
                role,
                session_account_id,
                ticket.account_id,
            )

            if account is None:
                return StructuredLookupOutput(
                    status=ToolResultStatus.NEEDS_VERIFICATION,
                    reason="Ticket account could not be resolved.",
                )

            overrides = _contract_overrides(
                db,
                role=role,
                session_account_id=session_account_id,
                account_id=account.account_id,
                clause_type="sla",
            )

            severity = filters.get("severity", "P3")

            contract_targets = {
                "P1": overrides.sla_p1_minutes,
                "P2": overrides.sla_p2_minutes,
                "P3": overrides.sla_p3_minutes,
            }

            result = check_sla_breach(
                account_id=account.account_id,
                plan=account.plan,
                severity=severity,
                ticket_created_at=ticket.created_at,
                now=dataset_snapshot_time(),
                contract_sla_minutes=contract_targets,
            )

            return StructuredLookupOutput(
                status=ToolResultStatus.OK,
                data={
                    "target_minutes": result.target_minutes,
                    "elapsed_minutes": result.elapsed_minutes,
                    "breached": result.breached,
                    "minutes_to_breach": result.minutes_to_breach,
                    "contract_sources": overrides.sources,
                },
                authority_source=result.authority_source,
            )

        return StructuredLookupOutput(
            status=ToolResultStatus.OUT_OF_SCOPE,
            reason=f"Unknown entity '{entity}'.",
        )

    except repo.AccessDeniedError as error:
        return StructuredLookupOutput(
            status=ToolResultStatus.ACCESS_DENIED,
            reason=str(error),
        )