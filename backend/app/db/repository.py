"""
Single data-access chokepoint.

Customer account isolation is enforced twice:

1. Application-level filtering in every repository method.
2. PostgreSQL RLS using transaction-local custom settings.

The custom settings intentionally use names that cannot collide with
PostgreSQL reserved keywords:
    parcelpilot.user_role
    parcelpilot.account_id
"""

from contextlib import contextmanager

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.models import Account, Escalation, Order, Ticket


class AccessDeniedError(Exception):
    """Raised when a session attempts to access another account."""


@contextmanager
def scoped_session(
    db: Session,
    role: str,
    account_id: str | None,
):
    """
    Set RLS context for the current transaction.

    `set_config(name, value, true)` is equivalent to SET LOCAL but safely
    parameterizes both the setting name and value. The third argument `true`
    makes the setting transaction-local.
    """
    db.execute(
        text(
            "SELECT set_config("
            "'parcelpilot.user_role', "
            ":role, "
            "true"
            ")"
        ),
        {"role": role},
    )

    db.execute(
        text(
            "SELECT set_config("
            "'parcelpilot.account_id', "
            ":account_id, "
            "true"
            ")"
        ),
        {"account_id": account_id or ""},
    )

    try:
        yield db
    finally:
        # The values are transaction-local and automatically disappear when
        # the surrounding transaction commits or rolls back.
        pass


def _assert_scope(
    role: str,
    session_account_id: str | None,
    requested_account_id: str | None,
):
    """
    Enforce application-level account isolation before querying PostgreSQL.
    """
    if role != "customer":
        return

    if not session_account_id:
        raise AccessDeniedError(
            "Customer session is missing account_id."
        )

    if (
        requested_account_id
        and requested_account_id != session_account_id
    ):
        raise AccessDeniedError(
            f"Customer session for {session_account_id} "
            f"may not access {requested_account_id}."
        )


def get_account(
    db: Session,
    role: str,
    session_account_id: str | None,
    account_id: str,
) -> Account | None:
    _assert_scope(
        role,
        session_account_id,
        account_id,
    )

    with scoped_session(
        db,
        role,
        session_account_id,
    ):
        query = db.query(Account).filter(
            Account.account_id == account_id
        )

        return query.first()


def list_orders(
    db: Session,
    role: str,
    session_account_id: str | None,
    account_id: str | None = None,
    order_id: str | None = None,
) -> list[Order]:
    effective_account_id = (
        account_id
        if account_id is not None
        else (
            session_account_id
            if role == "customer"
            else None
        )
    )

    _assert_scope(
        role,
        session_account_id,
        effective_account_id,
    )

    with scoped_session(
        db,
        role,
        session_account_id,
    ):
        query = db.query(Order)

        if effective_account_id:
            query = query.filter(
                Order.account_id == effective_account_id
            )

        if order_id:
            query = query.filter(
                Order.order_id == order_id
            )

        return query.all()


def list_tickets(
    db: Session,
    role: str,
    session_account_id: str | None,
    account_id: str | None = None,
    ticket_id: str | None = None,
    status: str | None = None,
) -> list[Ticket]:
    effective_account_id = (
        account_id
        if account_id is not None
        else (
            session_account_id
            if role == "customer"
            else None
        )
    )

    _assert_scope(
        role,
        session_account_id,
        effective_account_id,
    )

    with scoped_session(
        db,
        role,
        session_account_id,
    ):
        query = db.query(Ticket)

        if effective_account_id:
            query = query.filter(
                Ticket.account_id == effective_account_id
            )

        if ticket_id:
            query = query.filter(
                Ticket.ticket_id == ticket_id
            )

        if status:
            query = query.filter(
                Ticket.status == status
            )

        return query.all()


def get_contract_rules(
    db: Session,
    role: str,
    session_account_id: str | None,
    account_id: str,
    clause_type: str,
):
    """
    Return active contract rules for one account.

    The customer can only read rules belonging to their own account.
    Internal roles can read contract rules across accounts.
    """
    from app.db.models import ContractRule

    _assert_scope(
        role,
        session_account_id,
        account_id,
    )

    with scoped_session(
        db,
        role,
        session_account_id,
    ):
        return (
            db.query(ContractRule)
            .filter(
                ContractRule.account_id == account_id,
                ContractRule.clause_type == clause_type,
                ContractRule.is_active.is_(True),
            )
            .order_by(ContractRule.rule_id.asc())
            .all()
        )


def create_escalation(
    db: Session,
    role: str,
    session_account_id: str | None,
    escalation: Escalation,
) -> Escalation:
    _assert_scope(
        role,
        session_account_id,
        escalation.account_id,
    )

    with scoped_session(
        db,
        role,
        session_account_id,
    ):
        db.add(escalation)
        db.commit()
        db.refresh(escalation)
        return escalation