"""
Single chokepoint for all data access. Access control is enforced HERE -- in code, and
independently again by Postgres RLS (rls_policies.sql) -- never relying on model/prompt
instructions to keep a customer within their own account.
"""
from contextlib import contextmanager
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.models import Account, Order, Ticket, Escalation


class AccessDeniedError(Exception):
    pass


@contextmanager
def scoped_session(db: Session, role: str, account_id: str | None):
    """Sets Postgres session variables so RLS policies can enforce scoping at the DB engine
    level, as a second independent layer beneath the Python-level filters below."""
    db.execute(text("SET LOCAL app.current_role = :role"), {"role": role})
    db.execute(text("SET LOCAL app.current_account_id = :acct"), {"acct": account_id or ""})
    try:
        yield db
    finally:
        pass


def _assert_scope(role: str, session_account_id: str | None, requested_account_id: str | None):
    if role == "customer":
        if not session_account_id:
            raise AccessDeniedError("Customer session missing account_id.")
        if requested_account_id and requested_account_id != session_account_id:
            raise AccessDeniedError(
                f"Customer session for {session_account_id} may not access {requested_account_id}."
            )


def get_account(db: Session, role: str, session_account_id: str | None, account_id: str) -> Account | None:
    _assert_scope(role, session_account_id, account_id)
    with scoped_session(db, role, session_account_id):
        return db.query(Account).filter(Account.account_id == account_id).first()


def list_orders(db: Session, role: str, session_account_id: str | None,
                 account_id: str | None = None, order_id: str | None = None) -> list[Order]:
    effective_account_id = account_id or (session_account_id if role == "customer" else None)
    _assert_scope(role, session_account_id, effective_account_id)
    with scoped_session(db, role, session_account_id):
        q = db.query(Order)
        if effective_account_id:
            q = q.filter(Order.account_id == effective_account_id)
        if order_id:
            q = q.filter(Order.order_id == order_id)
        return q.all()


def list_tickets(db: Session, role: str, session_account_id: str | None,
                  account_id: str | None = None, ticket_id: str | None = None,
                  status: str | None = None) -> list[Ticket]:
    effective_account_id = account_id or (session_account_id if role == "customer" else None)
    _assert_scope(role, session_account_id, effective_account_id)
    with scoped_session(db, role, session_account_id):
        q = db.query(Ticket)
        if effective_account_id:
            q = q.filter(Ticket.account_id == effective_account_id)
        if ticket_id:
            q = q.filter(Ticket.ticket_id == ticket_id)
        if status:
            q = q.filter(Ticket.status == status)
        return q.all()


def create_escalation(db: Session, role: str, session_account_id: str | None,
                       escalation: Escalation) -> Escalation:
    _assert_scope(role, session_account_id, escalation.account_id)
    with scoped_session(db, role, session_account_id):
        db.add(escalation)
        db.commit()
        db.refresh(escalation)
        return escalation
