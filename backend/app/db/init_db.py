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


def _apply_document_column_migrations():
    new_cols = [
        ("original_filename", "VARCHAR"),
        ("storage_path", "VARCHAR"),
        ("title", "VARCHAR"),
        ("visibility", "VARCHAR DEFAULT 'internal_only'"),
        ("expires_at", "TIMESTAMP"),
        ("authority_rank", "INTEGER"),
        ("supersedes_doc_id", "VARCHAR"),
        ("superseded_by_doc_id", "VARCHAR"),
        ("checksum_sha256", "VARCHAR"),
        ("uploaded_by", "VARCHAR"),
        ("uploaded_at", "TIMESTAMP"),
        ("reviewed_by", "VARCHAR"),
        ("reviewed_at", "TIMESTAMP"),
        ("activated_by", "VARCHAR"),
        ("activated_at", "TIMESTAMP"),
        ("ingestion_error", "TEXT"),
        ("is_user_uploaded", "BOOLEAN DEFAULT FALSE"),
        ("source_origin", "VARCHAR DEFAULT 'assessment_pack'"),
    ]

    with engine.begin() as conn:
        for col_name, col_type in new_cols:
            try:
                conn.execute(
                    text(
                        f"ALTER TABLE documents ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
                    )
                )
            except Exception as e:
                # Fallback for SQLite or already existing columns
                pass


def main():
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    Base.metadata.create_all(engine)
    _apply_document_column_migrations()

    with engine.begin() as conn:
        from pathlib import Path
        rls_path = Path(__file__).resolve().parent / "rls_policies.sql"
        with open(rls_path) as file:
            sql = file.read()

        statements = [
            statement.strip()
            for statement in sql.split(";")
            if statement.strip()
        ]

        for statement in statements:
            conn.execute(text(statement))

        print("[init_db] RLS policies applied.")

    db = SessionLocal()
    try:
        from app.db.models import ContractRule
        from app.db.seed_data import CONTRACT_RULES_SEED

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
            db.commit() # Commit parents first to satisfy contract_rules doc_id foreign key

            for cr in CONTRACT_RULES_SEED:
                db.add(ContractRule(**cr))
            db.commit()
            print("[init_db] Seeded accounts, orders, tickets, documents, authority rules, contract rules.")
        else:
            if db.query(ContractRule).count() == 0:
                for cr in CONTRACT_RULES_SEED:
                    db.add(ContractRule(**cr))
                db.commit()
                print("[init_db] Seeded missing contract rules.")
            print("[init_db] Accounts already present -- skipping base seed.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
