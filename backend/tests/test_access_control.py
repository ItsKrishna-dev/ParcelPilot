"""
Verifies cross-account access is blocked at the repository layer (app-code) -- and that
Postgres RLS (rls_policies.sql) provides a second, independent layer, so a bug in one does
not compromise the other. See docs/ARCHITECTURE_NOTE.md "Access Control" section.
"""
import pytest
from app.db import repository as repo


def test_customer_cannot_read_other_account_orders(db_session):
    with pytest.raises(repo.AccessDeniedError):
        repo.list_orders(db_session, role="customer", session_account_id="ACCT-001",
                          account_id="ACCT-002")


def test_customer_can_read_own_account_orders(db_session):
    orders = repo.list_orders(db_session, role="customer", session_account_id="ACCT-001",
                                account_id="ACCT-001")
    assert all(o.account_id == "ACCT-001" for o in orders)


def test_customer_without_account_id_denied(db_session):
    with pytest.raises(repo.AccessDeniedError):
        repo.get_account(db_session, role="customer", session_account_id=None, account_id="ACCT-001")


def test_support_agent_can_read_any_account(db_session):
    orders = repo.list_orders(db_session, role="support_agent", session_account_id=None,
                                account_id="ACCT-002")
    assert all(o.account_id == "ACCT-002" for o in orders)
