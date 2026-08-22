"""
Resolves, per query clause, WHICH source is authoritative -- reading precedence from the
source_authority_rules TABLE (see db/models.py), not from hardcoded if/else branches. This
is the module that makes "contracts override policy" auditable and testable independent of
any LLM call.
"""
from dataclasses import dataclass
from sqlalchemy.orm import Session
from app.db.models import SourceAuthorityRule, Document, Account


@dataclass
class AuthorityResolution:
    clause: str
    winning_source_type: str
    winning_doc_id: str | None
    precedence_rank: int
    explanation: str


def resolve_authority(db: Session, account_id: str, clause: str) -> AuthorityResolution:
    """Returns the highest-precedence source that actually exists for this account/clause.

    Example: for clause='cancellation_fee' on ACCT-001 (Northstar, has a contract), the
    'agreement' rule (rank 1) wins because Northstar HAS a contract_file. For ACCT-003
    (Beacon Retail, no contract), the 'agreement' rule is skipped (no document exists) and
    falls through to 'sop' (rank 2).
    """
    rules = (
        db.query(SourceAuthorityRule)
        .filter(SourceAuthorityRule.applies_to_clause == clause)
        .filter(SourceAuthorityRule.doc_status.in_(["CURRENT"]))
        .order_by(SourceAuthorityRule.precedence_rank.asc())
        .all()
    )

    account = db.query(Account).filter(Account.account_id == account_id).first()

    for rule in rules:
        if rule.source_type == "agreement":
            if account and account.contract_file:
                doc = db.query(Document).filter(Document.filename == account.contract_file).first()
                return AuthorityResolution(
                    clause=clause,
                    winning_source_type="agreement",
                    winning_doc_id=doc.doc_id if doc else None,
                    precedence_rank=rule.precedence_rank,
                    explanation=f"{account.account_name} has a signed agreement covering '{clause}'; "
                                f"it overrides general policy for this account.",
                )
            continue

        doc = (
            db.query(Document)
            .filter(Document.doc_type == rule.source_type, Document.status == "CURRENT")
            .first()
        )
        if doc:
            return AuthorityResolution(
                clause=clause,
                winning_source_type=rule.source_type,
                winning_doc_id=doc.doc_id,
                precedence_rank=rule.precedence_rank,
                explanation=f"No account-specific override; current '{rule.source_type}' document applies.",
            )

    return AuthorityResolution(
        clause=clause, winning_source_type="none", winning_doc_id=None,
        precedence_rank=9999,
        explanation="No authoritative current source found for this clause -- escalate.",
    )


def label_historical_note(text: str) -> str:
    """Historical ticket resolutions are ALWAYS rendered with this label -- never presented
    as if they were policy. See db/models.py Ticket.historical_resolution docstring."""
    return f"[Unverified historical note -- may be inaccurate, not policy authority] {text}"
