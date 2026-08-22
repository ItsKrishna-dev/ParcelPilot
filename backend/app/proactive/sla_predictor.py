"""SLA breach prediction: for every open ticket, compute minutes-to-breach using the
same contract-aware domain.sla logic the chatbot uses, so the dashboard and the chatbot
can never disagree about what the SLA target is."""
from dataclasses import dataclass
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models import Ticket, Account
from app.domain.sla import check_sla_breach


@dataclass
class SlaRiskEntry:
    ticket_id: str
    account_id: str
    account_name: str
    severity_guess: str
    minutes_to_breach: float
    breached: bool


def _guess_severity(ticket: Ticket) -> str:
    text = f"{ticket.subject or ''} {ticket.description or ''}".lower()
    if any(k in text for k in ["outage", "down", "500", "all shipment", "security", "exposure"]):
        return "P1"
    if any(k in text for k in ["fails", "degraded", "cannot", "unable"]):
        return "P2"
    return "P3"


def predict_sla_risk(db: Session, now: datetime, breach_soon_minutes: float = 60.0) -> list[SlaRiskEntry]:
    open_tickets = db.query(Ticket).filter(Ticket.status == "open").all()
    entries = []
    for t in open_tickets:
        account = db.query(Account).filter(Account.account_id == t.account_id).first()
        if not account:
            continue
        severity = _guess_severity(t)
        result = check_sla_breach(account.account_id, account.plan, severity, t.created_at, now)
        if result.breached or result.minutes_to_breach <= breach_soon_minutes:
            entries.append(SlaRiskEntry(
                ticket_id=t.ticket_id, account_id=account.account_id, account_name=account.account_name,
                severity_guess=severity, minutes_to_breach=result.minutes_to_breach, breached=result.breached,
            ))
    return sorted(entries, key=lambda e: e.minutes_to_breach)
