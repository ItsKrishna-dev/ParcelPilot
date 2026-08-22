"""
SQLAlchemy models for ParcelPilot.

Design note: `source_authority_rules` encodes the authority precedence (contract > SOP >
policy > product docs > deprecated > historical) as DATA, not as if/else branches in Python.
This means the precedence can be audited, versioned, and unit-tested independently of any
LLM call, and updated by a policy admin without a code deploy.
"""
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Boolean, DateTime, Integer, ForeignKey, Text, JSON
)
from sqlalchemy.orm import declarative_base, relationship
from pgvector.sqlalchemy import Vector
from sqlalchemy import UniqueConstraint
Base = declarative_base()


class Account(Base):
    __tablename__ = "accounts"
    account_id = Column(String, primary_key=True)
    account_name = Column(String, nullable=False)
    plan = Column(String, nullable=False)          # Enterprise | Growth | Standard
    status = Column(String, nullable=False)
    csm = Column(String)
    contract_file = Column(String, nullable=True)   # filename of signed agreement, or NULL
    premium_support = Column(Boolean, default=False)
    notes = Column(Text)

    orders = relationship("Order", back_populates="account")
    tickets = relationship("Ticket", back_populates="account")


class Order(Base):
    __tablename__ = "orders"
    order_id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.account_id"), nullable=False, index=True)
    carrier = Column(String)
    status = Column(String, nullable=False)   # DRAFT | BOOKED | PICKED_UP | DELIVERED
    booked_at = Column(DateTime)
    pickup_window_start = Column(DateTime)
    pickup_window_end = Column(DateTime)
    pickup_actual_at = Column(DateTime, nullable=True)
    shipment_fee_inr = Column(Float)
    carrier_fault = Column(Boolean, default=False)
    customer_fault = Column(Boolean, default=False)
    cancellation_requested_at = Column(DateTime, nullable=True)
    notes = Column(Text)

    account = relationship("Account", back_populates="orders")


class Ticket(Base):
    __tablename__ = "tickets"
    ticket_id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.account_id"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False)
    status = Column(String, nullable=False)   # open | closed
    subject = Column(Text)
    description = Column(Text)
    channel = Column(String)
    assigned_to = Column(String)
    last_customer_message_at = Column(DateTime, nullable=True)
    # Historical guidance is CONTEXT ONLY and may be WRONG -- never treated as authority.
    # See retrieval/source_authority.py: this field is always rendered with an
    # "unverified historical note" label and never used to compute a fee/credit/SLA number.
    historical_resolution = Column(Text, nullable=True)

    account = relationship("Account", back_populates="tickets")


class Document(Base):
    __tablename__ = "documents"
    doc_id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    doc_type = Column(String, nullable=False)     # support_policy | sop | product_ops | agreement
    status = Column(String, nullable=False)        # CURRENT | DEPRECATED
    effective_date = Column(DateTime, nullable=True)
    account_id = Column(String, ForeignKey("accounts.account_id"), nullable=True)  # set for contracts
    raw_text = Column(Text)


class DocChunk(Base):
    __tablename__ = "doc_chunks"
    chunk_id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(String, ForeignKey("documents.doc_id"), nullable=False, index=True)
    page = Column(Integer)
    text = Column(Text, nullable=False)
    embedding = Column(Vector(384))   # all-MiniLM-L6-v2 dimension


class SourceAuthorityRule(Base):
    """Authority precedence encoded as data. Lower precedence_rank = higher authority."""
    __tablename__ = "source_authority_rules"
    rule_id = Column(Integer, primary_key=True, autoincrement=True)
    source_type = Column(String, nullable=False)     # agreement | sop | support_policy | product_ops | deprecated | historical_ticket
    doc_status = Column(String, nullable=False)       # CURRENT | DEPRECATED | ADVISORY_ONLY
    precedence_rank = Column(Integer, nullable=False)  # 1 = highest authority
    applies_to_clause = Column(String, nullable=False)  # cancellation_fee | service_credit | sla | severity | product_defect | general
    effective_from = Column(DateTime, nullable=True)
    effective_to = Column(DateTime, nullable=True)
    notes = Column(Text)

class ContractRule(Base):
    """
    Structured representation of an agreement clause extracted from a signed
    customer agreement.

    This table prevents business logic from depending on hardcoded account IDs.
    The account is identified through the agreement document's account_id, and
    the actual rule values are extracted from document content.
    """

    __tablename__ = "contract_rules"

    rule_id = Column(Integer, primary_key=True, autoincrement=True)

    account_id = Column(
        String,
        ForeignKey("accounts.account_id"),
        nullable=False,
        index=True,
    )

    doc_id = Column(
        String,
        ForeignKey("documents.doc_id"),
        nullable=False,
        index=True,
    )

    clause_type = Column(
        String,
        nullable=False,
        index=True,
    )
    # Supported values:
    # cancellation_fee
    # service_credit
    # sla

    rule_key = Column(String, nullable=False)
    # Examples:
    # cancellation_fee_waived
    # cancellation_free_window_minutes
    # cancellation_fee_inr
    # service_credit_delay_threshold_hours
    # service_credit_fixed_amount_inr
    # service_credit_monthly_cap_inr
    # sla_p1_minutes
    # sla_p2_minutes
    # sla_p3_minutes
    # support_after_hours

    value_number = Column(Float, nullable=True)
    value_text = Column(Text, nullable=True)
    value_boolean = Column(Boolean, nullable=True)

    unit = Column(String, nullable=True)
    source_text = Column(Text, nullable=False)

    effective_from = Column(DateTime, nullable=True)
    effective_to = Column(DateTime, nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint(
            "account_id",
            "doc_id",
            "clause_type",
            "rule_key",
            name="uq_contract_rule",
        ),
    )
    
class Escalation(Base):
    __tablename__ = "escalations"
    escalation_id = Column(String, primary_key=True)
    ticket_id = Column(String, ForeignKey("tickets.ticket_id"), nullable=True)
    account_id = Column(String, ForeignKey("accounts.account_id"), nullable=False)
    reason = Column(Text, nullable=False)
    severity = Column(String)
    created_by = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="open")


class PendingAction(Base):
    """Draft of a state-changing action awaiting explicit user confirmation (2-phase commit)."""
    __tablename__ = "pending_actions"
    pending_action_id = Column(String, primary_key=True)
    action_type = Column(String, nullable=False)   # create_escalation | update_ticket | create_task
    payload = Column(JSON, nullable=False)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    consumed = Column(Boolean, default=False)


class AuditLog(Base):
    __tablename__ = "audit_log"
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    actor_user_id = Column(String, nullable=False)
    actor_role = Column(String, nullable=False)
    action_type = Column(String, nullable=False)
    target_account_id = Column(String, nullable=True)
    payload = Column(JSON)
    result = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
