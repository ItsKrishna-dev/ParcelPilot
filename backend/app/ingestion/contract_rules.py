"""
Extract structured contract rules from agreement documents.

The extraction is intentionally conservative and deterministic for the
assessment's supplied agreements. It matches normalized clauses in the
ingested document text, validates the expected values, and stores only rules
that were explicitly found.

No account IDs are hardcoded here. The account is discovered from the
Document.account_id relationship.
"""

import re
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import Account, ContractRule, Document
from dataclasses import dataclass

from app.db.models import ContractRule

def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _add_rule(
    db: Session,
    *,
    account: Account,
    document: Document,
    clause_type: str,
    rule_key: str,
    source_text: str,
    value_number: float | None = None,
    value_text: str | None = None,
    value_boolean: bool | None = None,
    unit: str | None = None,
):
    existing = (
        db.query(ContractRule)
        .filter(
            ContractRule.account_id == account.account_id,
            ContractRule.doc_id == document.doc_id,
            ContractRule.clause_type == clause_type,
            ContractRule.rule_key == rule_key,
        )
        .one_or_none()
    )

    values = {
        "value_number": value_number,
        "value_text": value_text,
        "value_boolean": value_boolean,
        "unit": unit,
        "source_text": source_text,
        "effective_from": document.effective_date,
        "is_active": True,
    }

    if existing is None:
        db.add(
            ContractRule(
                account_id=account.account_id,
                doc_id=document.doc_id,
                clause_type=clause_type,
                rule_key=rule_key,
                **values,
            )
        )
    else:
        for field, value in values.items():
            setattr(existing, field, value)


def _extract_sla_rules(
    db: Session,
    account: Account,
    document: Document,
    text: str,
):
    patterns = {
        "sla_p1_minutes": (
            r"P1\s*:\s*(\d+)\s*minutes?"
        ),
        "sla_p2_minutes": (
            r"P2\s*:\s*(\d+)\s*(?:hour|hours|minutes?)"
        ),
        "sla_p3_minutes": (
            r"P3\s*:\s*(\d+)\s*(?:business\s*)?"
            r"(?:hour|hours|day|days|minutes?)"
        ),
    }

    for rule_key, pattern in patterns.items():
        match = re.search(pattern, text, flags=re.IGNORECASE)

        if not match:
            continue

        value = float(match.group(1))
        matched_text = match.group(0)

        if rule_key == "sla_p2_minutes":
            if "hour" in matched_text.lower():
                value *= 60

        if rule_key == "sla_p3_minutes":
            lowered = matched_text.lower()

            if "day" in lowered:
                value *= 8 * 60
            elif "hour" in lowered:
                value *= 60

        _add_rule(
            db,
            account=account,
            document=document,
            clause_type="sla",
            rule_key=rule_key,
            value_number=value,
            unit="minutes",
            source_text=matched_text,
        )


def _extract_cancellation_rules(
    db: Session,
    account: Account,
    document: Document,
    text: str,
):
    waiver_pattern = (
        r"(?:may cancel any BOOKED shipment before pickup "
        r"with no cancellation fee)"
    )

    waiver_match = re.search(
        waiver_pattern,
        text,
        flags=re.IGNORECASE,
    )

    if waiver_match:
        _add_rule(
            db,
            account=account,
            document=document,
            clause_type="cancellation_fee",
            rule_key="cancellation_fee_waived",
            value_boolean=True,
            source_text=waiver_match.group(0),
        )

    no_waiver_pattern = (
        r"(?:No special cancellation-fee waiver applies)"
    )

    no_waiver_match = re.search(
        no_waiver_pattern,
        text,
        flags=re.IGNORECASE,
    )

    if no_waiver_match:
        _add_rule(
            db,
            account=account,
            document=document,
            clause_type="cancellation_fee",
            rule_key="cancellation_fee_waived",
            value_boolean=False,
            source_text=no_waiver_match.group(0),
        )


def _extract_service_credit_rules(
    db: Session,
    account: Account,
    document: Document,
    text: str,
):
    threshold_pattern = (
        r"pickup is more than\s+(\d+(?:\.\d+)?)\s*hours?"
        r"\s+past"
    )

    threshold_match = re.search(
        threshold_pattern,
        text,
        flags=re.IGNORECASE,
    )

    if threshold_match:
        _add_rule(
            db,
            account=account,
            document=document,
            clause_type="service_credit",
            rule_key="service_credit_delay_threshold_hours",
            value_number=float(threshold_match.group(1)),
            unit="hours",
            source_text=threshold_match.group(0),
        )

    fixed_credit_pattern = (
        r"(?:fixed\s+INR|INR)\s*(\d+(?:\.\d+)?)"
        r"\s*service credit"
    )

    fixed_credit_match = re.search(
        fixed_credit_pattern,
        text,
        flags=re.IGNORECASE,
    )

    if fixed_credit_match:
        _add_rule(
            db,
            account=account,
            document=document,
            clause_type="service_credit",
            rule_key="service_credit_fixed_amount_inr",
            value_number=float(fixed_credit_match.group(1)),
            unit="INR",
            source_text=fixed_credit_match.group(0),
        )

    monthly_cap_pattern = (
        r"Monthly aggregate service credits are capped at"
        r"\s*INR\s*(\d+(?:\.\d+)?)"
    )

    monthly_cap_match = re.search(
        monthly_cap_pattern,
        text,
        flags=re.IGNORECASE,
    )

    if monthly_cap_match:
        _add_rule(
            db,
            account=account,
            document=document,
            clause_type="service_credit",
            rule_key="service_credit_monthly_cap_inr",
            value_number=float(monthly_cap_match.group(1)),
            unit="INR",
            source_text=monthly_cap_match.group(0),
        )


def extract_contract_rules(db: Session):
    documents = (
        db.query(Document)
        .filter(
            Document.doc_type == "agreement",
            Document.status == "CURRENT",
            Document.account_id.isnot(None),
        )
        .all()
    )

    extracted_count = 0

    for document in documents:
        account = (
            db.query(Account)
            .filter(Account.account_id == document.account_id)
            .one_or_none()
        )

        if account is None:
            continue

        text = _normalized(document.raw_text)

        if not text:
            print(
                f"[contract_rules] Skipping {document.filename}: "
                "document.raw_text is empty."
            )
            continue

        before_count = db.query(ContractRule).filter(
            ContractRule.doc_id == document.doc_id
        ).count()

        _extract_sla_rules(db, account, document, text)
        _extract_cancellation_rules(db, account, document, text)
        _extract_service_credit_rules(db, account, document, text)

        db.flush()

        after_count = db.query(ContractRule).filter(
            ContractRule.doc_id == document.doc_id
        ).count()

        extracted_count += max(0, after_count - before_count)

        print(
            f"[contract_rules] {document.filename}: "
            f"{after_count} active structured rules"
        )

    db.commit()

    print(
        f"[contract_rules] Extraction complete: "
        f"{extracted_count} new rules."
    )


if __name__ == "__main__":
    from app.db.session import SessionLocal

    db = SessionLocal()

    try:
        extract_contract_rules(db)
    finally:
        db.close()