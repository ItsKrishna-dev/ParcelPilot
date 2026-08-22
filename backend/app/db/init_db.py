"""
Creates all tables, enables pgvector + RLS, and seeds accounts/orders/tickets/documents/
authority-rules. Run once against a fresh Postgres instance:

    python -m app.db.init_db
"""
from datetime import datetime
from sqlalchemy import text
from app.db.session import engine, SessionLocal
from app.db.models import (
    Base, Account, Order, Ticket, Document, SourceAuthorityRule
)
from app.db.seed_data import ACCOUNTS, ORDERS, TICKETS, DOCUMENTS_META, SOURCE_AUTHORITY_RULES


def _dt(value):
    return datetime.fromisoformat(value) if value else None


def main():
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    Base.metadata.create_all(engine)

    with engine.begin() as conn:
        try:
            with open("app/db/rls_policies.sql") as f:
                sql = f.read()
            for stmt in sql.split(";"):
                stmt = stmt.strip()
                if stmt:
                    conn.execute(text(stmt))
        except Exception as e:
            print(f"[init_db] RLS setup skipped/already applied: {e}")

    db = SessionLocal()
    try:
        if db.query(Account).count() == 0:
            for a in ACCOUNTS:
                db.add(Account(**a))
            for o in ORDERS:
                o = dict(o)
                for k in ["booked_at", "pickup_window_start", "pickup_window_end",
                          "pickup_actual_at", "cancellation_requested_at"]:
                    o[k] = _dt(o[k])
                db.add(Order(**o))
            for t in TICKETS:
                t = dict(t)
                for k in ["created_at", "last_customer_message_at"]:
                    t[k] = _dt(t[k])
                db.add(Ticket(**t))
            for d in DOCUMENTS_META:
                d = dict(d)
                d["effective_date"] = _dt(d["effective_date"])
                d["raw_text"] = ""  # populated by ingestion/pdf_loader.py
                db.add(Document(**d))
            for r in SOURCE_AUTHORITY_RULES:
                db.add(SourceAuthorityRule(**r))
            db.commit()
            print("[init_db] Seeded accounts, orders, tickets, documents, authority rules.")
        else:
            print("[init_db] Accounts already present -- skipping seed.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
