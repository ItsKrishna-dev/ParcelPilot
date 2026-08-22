"""Flags the same known-issue tag appearing across multiple accounts within a rolling
window -- e.g. KI-208 (bulk upload) hitting both Growth and Enterprise customers
simultaneously is a product-wide incident, not four unrelated tickets."""
from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.models import Ticket
from app.domain.known_issues import match_known_issue


@dataclass
class CrossAccountCorrelation:
    issue_id: str
    title: str
    accounts_affected: list[str]
    ticket_ids: list[str]


def find_cross_account_correlations(db: Session, now: datetime, window_hours: int = 48) -> list[CrossAccountCorrelation]:
    window_start = now - timedelta(hours=window_hours)
    tickets = db.query(Ticket).filter(Ticket.created_at >= window_start, Ticket.status == "open").all()

    by_issue: dict[str, list[Ticket]] = {}
    for t in tickets:
        issue = match_known_issue(f"{t.subject or ''} {t.description or ''}")
        if issue:
            by_issue.setdefault(issue.issue_id, []).append(t)

    correlations = []
    for issue_id, matched_tickets in by_issue.items():
        accounts = sorted({t.account_id for t in matched_tickets})
        if len(accounts) > 1:
            issue = match_known_issue(matched_tickets[0].subject or "")
            correlations.append(CrossAccountCorrelation(
                issue_id=issue_id, title=issue.title if issue else issue_id,
                accounts_affected=accounts, ticket_ids=[t.ticket_id for t in matched_tickets],
            ))
    return correlations
