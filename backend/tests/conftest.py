"""
Test fixtures: an isolated Postgres test database seeded with the same
accounts/orders/tickets/authority-rules as production. Requires a running Postgres
instance (docker-compose db service); skips gracefully otherwise.
"""
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.db.models import Base
from app.db.seed_data import ACCOUNTS, ORDERS, TICKETS, DOCUMENTS_META, SOURCE_AUTHORITY_RULES
from app.db.models import Account, Order, Ticket, Document, SourceAuthorityRule
from datetime import datetime
from app.config import settings


def _dt(value):
    return datetime.fromisoformat(value) if value else None


@pytest.fixture(scope="session")
def engine():
    test_url = settings.database_url.replace("/parcelpilot", "/parcelpilot_test")
    eng = create_engine(test_url)
    try:
        with eng.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
    except Exception:
        pytest.skip("Postgres test database not available -- start docker-compose db service.")
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def db_session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()

    session.query(Order).delete()
    session.query(Ticket).delete()
    session.query(Account).delete()
    session.query(Document).delete()
    session.query(SourceAuthorityRule).delete()

    for a in ACCOUNTS:
        session.add(Account(**a))
    for o in ORDERS:
        o = dict(o)
        for k in ["booked_at", "pickup_window_start", "pickup_window_end", "pickup_actual_at", "cancellation_requested_at"]:
            o[k] = _dt(o[k])
        session.add(Order(**o))
    for t in TICKETS:
        t = dict(t)
        for k in ["created_at", "last_customer_message_at"]:
            t[k] = _dt(t[k])
        session.add(Ticket(**t))
    for d in DOCUMENTS_META:
        d = dict(d)
        d["effective_date"] = _dt(d["effective_date"])
        d["raw_text"] = ""
        session.add(Document(**d))
    for r in SOURCE_AUTHORITY_RULES:
        session.add(SourceAuthorityRule(**r))
    session.commit()

    yield session
    session.rollback()
    session.close()
