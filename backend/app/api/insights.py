"""Internal-only proactive insights dashboard endpoint (Problem 1)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.auth.dependencies import get_current_session, require_role
from app.auth.mock_auth import Session as UserSession
from app.config import dataset_snapshot_time
from app.proactive.anomaly_detection import detect_ticket_spikes
from app.proactive.sla_predictor import predict_sla_risk
from app.proactive.cross_account_correlator import find_cross_account_correlations

router = APIRouter(prefix="/internal/insights", tags=["insights"])


@router.get("")
def get_insights(db: Session = Depends(get_db), session: UserSession = Depends(get_current_session)):
    require_role(session, ["support_agent", "manager"])
    now = dataset_snapshot_time()
    return {
        "ticket_volume_anomalies": [a.__dict__ for a in detect_ticket_spikes(db, now)],
        "sla_risk": [e.__dict__ for e in predict_sla_risk(db, now)],
        "cross_account_correlations": [c.__dict__ for c in find_cross_account_correlations(db, now)],
        "as_of": str(now),
    }
