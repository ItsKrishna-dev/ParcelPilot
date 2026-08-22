"""
Statistical anomaly detection for Problem 1 (Proactive Issue Detection) -- a rolling
z-score/EWMA spike detector on ticket volume per product-area/time-bucket, NOT keyword
clustering. This is a scheduled/batch computation, not an LLM call: cheaper, deterministic,
and auditable.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
import statistics
from sqlalchemy.orm import Session
from app.db.models import Ticket

PRODUCT_AREA_KEYWORDS = {
    "bulk_upload": ["bulk upload", "csv", "upload fails"],
    "shipment_status": ["still shows booked", "status", "webhook", "pickup"],
    "billing": ["billing", "invoice", "payment"],
    "security": ["api key", "security", "credential", "exposure"],
    "outage": ["500", "failing", "down", "outage"],
}


def _tag_area(ticket: Ticket) -> str:
    text = f"{ticket.subject or ''} {ticket.description or ''}".lower()
    for area, kws in PRODUCT_AREA_KEYWORDS.items():
        if any(kw in text for kw in kws):
            return area
    return "other"


@dataclass
class AnomalyFlag:
    product_area: str
    window_count: int
    baseline_mean: float
    baseline_stdev: float
    z_score: float
    accounts_affected: list[str]
    severity: str   # info | warning | critical


def detect_ticket_spikes(
    db: Session, now: datetime, window_hours: int = 24, baseline_days: int = 14, z_threshold: float = 2.0,
) -> list[AnomalyFlag]:
    """Rolling z-score: compares ticket count per product-area in the last `window_hours`
    against the mean/stdev of daily counts over the prior `baseline_days`."""
    window_start = now - timedelta(hours=window_hours)
    baseline_start = now - timedelta(days=baseline_days)

    all_tickets = db.query(Ticket).filter(Ticket.created_at >= baseline_start).all()

    by_area: dict[str, list[Ticket]] = {}
    for t in all_tickets:
        by_area.setdefault(_tag_area(t), []).append(t)

    flags = []
    for area, tickets in by_area.items():
        recent = [t for t in tickets if t.created_at >= window_start]
        if not recent:
            continue

        daily_counts: dict[str, int] = {}
        for t in tickets:
            day_key = t.created_at.strftime("%Y-%m-%d")
            daily_counts[day_key] = daily_counts.get(day_key, 0) + 1
        counts = list(daily_counts.values())

        if len(counts) < 2:
            mean, stdev = (counts[0] if counts else 0.0), 1.0
        else:
            mean, stdev = statistics.mean(counts), statistics.stdev(counts) or 1.0

        window_count = len(recent)
        z = (window_count - mean) / stdev if stdev else 0.0

        if z >= z_threshold:
            severity = "critical" if z >= 3.0 else "warning"
            flags.append(AnomalyFlag(
                product_area=area, window_count=window_count, baseline_mean=round(mean, 2),
                baseline_stdev=round(stdev, 2), z_score=round(z, 2),
                accounts_affected=sorted({t.account_id for t in recent}), severity=severity,
            ))

    return sorted(flags, key=lambda f: f.z_score, reverse=True)
