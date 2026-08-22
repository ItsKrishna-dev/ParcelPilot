"""
Mock authentication -- explicitly permitted by the assessment brief ("you may mock
authentication, account context, and user roles"). Real auth would swap this module for
JWT/OAuth verification without touching any downstream tool/orchestrator code, since every
caller only ever sees a `Session` object.
"""
from dataclasses import dataclass


@dataclass
class Session:
    user_id: str
    role: str            # customer | support_agent | manager
    account_id: str | None   # required for role=customer, None for internal roles


MOCK_USERS: dict[str, Session] = {
    "cust-northstar": Session(user_id="cust-northstar", role="customer", account_id="ACCT-001"),
    "cust-lumenworks": Session(user_id="cust-lumenworks", role="customer", account_id="ACCT-002"),
    "cust-beacon": Session(user_id="cust-beacon", role="customer", account_id="ACCT-003"),
    "cust-axislabs": Session(user_id="cust-axislabs", role="customer", account_id="ACCT-004"),
    "agent-rohit": Session(user_id="agent-rohit", role="support_agent", account_id=None),
    "agent-maya": Session(user_id="agent-maya", role="support_agent", account_id=None),
    "manager-priya": Session(user_id="manager-priya", role="manager", account_id=None),
}


def authenticate(token: str) -> Session:
    """Token here is just the mock user_id, sent as a bearer token by the frontend's
    session picker. Raises KeyError for unknown tokens (caught in dependencies.py)."""
    return MOCK_USERS[token]
