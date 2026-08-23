"""API tests for read-only records endpoints verifying access control."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_customer_can_read_own_orders_only():
    resp = client.get(
        "/records/orders",
        headers={"Authorization": "Bearer cust-northstar"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "orders" in data
    assert len(data["orders"]) > 0
    assert all(o["account_id"] == "ACCT-001" for o in data["orders"])


def test_customer_cannot_read_other_account_orders():
    resp = client.get(
        "/records/orders?account_id=ACCT-002",
        headers={"Authorization": "Bearer cust-northstar"},
    )
    assert resp.status_code == 403


def test_support_agent_can_read_all_orders():
    resp = client.get(
        "/records/orders",
        headers={"Authorization": "Bearer agent-rohit"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "orders" in data
    assert len(data["orders"]) >= 3


def test_customer_can_read_own_tickets_only():
    resp = client.get(
        "/records/tickets",
        headers={"Authorization": "Bearer cust-northstar"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "tickets" in data
    assert all(t["account_id"] == "ACCT-001" for t in data["tickets"])
