"""Read-only records API endpoint for orders, tickets, and account coverage.

Enforces exact repository and PostgreSQL RLS access control boundaries.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_session
from app.auth.mock_auth import Session as UserSession
from app.db import repository as repo
from app.db.session import get_db

router = APIRouter(prefix="/records", tags=["records"])


def _serialize_model(obj) -> dict:
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


@router.get("/orders")
def get_orders(
    account_id: str | None = None,
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_current_session),
):
    try:
        orders = repo.list_orders(
            db,
            role=session.role,
            session_account_id=session.account_id,
            account_id=account_id,
        )
        return {"orders": [_serialize_model(o) for o in orders]}
    except repo.AccessDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/tickets")
def get_tickets(
    account_id: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_current_session),
):
    try:
        tickets = repo.list_tickets(
            db,
            role=session.role,
            session_account_id=session.account_id,
            account_id=account_id,
            status=status,
        )
        return {"tickets": [_serialize_model(t) for t in tickets]}
    except repo.AccessDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/account")
def get_account(
    account_id: str | None = None,
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_current_session),
):
    target_account_id = account_id or session.account_id
    if not target_account_id:
        return {"account": None}
    try:
        acc = repo.get_account(
            db,
            role=session.role,
            session_account_id=session.account_id,
            account_id=target_account_id,
        )
        return {"account": _serialize_model(acc) if acc else None}
    except repo.AccessDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
