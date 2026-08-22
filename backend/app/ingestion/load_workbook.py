"""
Reload accounts, orders, and tickets from the assessment workbook.

Accounts are upserted rather than deleted because agreement documents reference
account rows through documents.account_id. Orders and tickets are replaced because
they are direct workbook snapshots.
"""

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy.exc import SQLAlchemyError

from app.db.models import Account, Order, Ticket
from app.db.session import SessionLocal


def _parse_dt(value):
    if value is None:
        return None

    if pd.isna(value):
        return None

    if isinstance(value, datetime):
        return value

    return pd.to_datetime(value).to_pydatetime()


def _clean_text(value):
    if value is None or pd.isna(value):
        return None

    return str(value)


def _clean_bool(value, default=False):
    if value is None or pd.isna(value):
        return default

    if isinstance(value, str):
        value = value.strip().lower()

        if value in {"true", "1", "yes", "y"}:
            return True

        if value in {"false", "0", "no", "n"}:
            return False

    return bool(value)


def _required_text(row, column_name, row_number):
    value = _clean_text(row.get(column_name))

    if not value:
        raise ValueError(
            f"Row {row_number} is missing required column '{column_name}'."
        )

    return value


def load_workbook(path: str):
    workbook_path = Path(path).expanduser().resolve()

    if not workbook_path.exists():
        raise FileNotFoundError(
            f"Workbook does not exist: {workbook_path}"
        )

    workbook = pd.ExcelFile(workbook_path)

    required_sheets = {"README", "accounts", "orders", "tickets"}
    missing_sheets = required_sheets.difference(workbook.sheet_names)

    if missing_sheets:
        raise ValueError(
            "Workbook is missing required sheets: "
            + ", ".join(sorted(missing_sheets))
        )

    readme_df = workbook.parse("README")
    accounts_df = workbook.parse("accounts")
    orders_df = workbook.parse("orders")
    tickets_df = workbook.parse("tickets")

    print("[load_workbook] README sheet loaded:")
    print(readme_df.to_string(index=False))

    db = SessionLocal()

    try:
        # Delete dependent workbook snapshot rows first.
        db.query(Ticket).delete(synchronize_session=False)
        db.query(Order).delete(synchronize_session=False)

        # Do not delete accounts. Contract documents reference them.
        for index, row in accounts_df.iterrows():
            row_number = index + 2
            account_id = _required_text(row, "account_id", row_number)

            account_values = {
                "account_name": _required_text(
                    row,
                    "account_name",
                    row_number,
                ),
                "plan": _required_text(row, "plan", row_number),
                "status": _required_text(row, "status", row_number),
                "csm": _clean_text(row.get("csm")),
                "contract_file": _clean_text(
                    row.get("contract_file")
                ),
                "premium_support": _clean_bool(
                    row.get("premium_support"),
                    default=False,
                ),
                "notes": _clean_text(row.get("notes")),
            }

            account = (
                db.query(Account)
                .filter(Account.account_id == account_id)
                .one_or_none()
            )

            if account is None:
                db.add(
                    Account(
                        account_id=account_id,
                        **account_values,
                    )
                )
            else:
                for field, value in account_values.items():
                    setattr(account, field, value)

        db.flush()

        for index, row in orders_df.iterrows():
            row_number = index + 2
            order_id = _required_text(row, "order_id", row_number)
            account_id = _required_text(row, "account_id", row_number)

            db.add(
                Order(
                    order_id=order_id,
                    account_id=account_id,
                    carrier=_clean_text(row.get("carrier")),
                    status=_required_text(row, "status", row_number),
                    booked_at=_parse_dt(row.get("booked_at")),
                    pickup_window_start=_parse_dt(
                        row.get("pickup_window_start")
                    ),
                    pickup_window_end=_parse_dt(
                        row.get("pickup_window_end")
                    ),
                    pickup_actual_at=_parse_dt(
                        row.get("pickup_actual_at")
                    ),
                    shipment_fee_inr=float(
                        row.get("shipment_fee_inr") or 0
                    ),
                    carrier_fault=_clean_bool(
                        row.get("carrier_fault"),
                        default=False,
                    ),
                    customer_fault=_clean_bool(
                        row.get("customer_fault"),
                        default=False,
                    ),
                    cancellation_requested_at=_parse_dt(
                        row.get("cancellation_requested_at")
                    ),
                    notes=_clean_text(row.get("notes")),
                )
            )

        for index, row in tickets_df.iterrows():
            row_number = index + 2
            ticket_id = _required_text(row, "ticket_id", row_number)
            account_id = _required_text(row, "account_id", row_number)

            db.add(
                Ticket(
                    ticket_id=ticket_id,
                    account_id=account_id,
                    created_at=_parse_dt(row.get("created_at")),
                    status=_required_text(row, "status", row_number),
                    subject=_clean_text(row.get("subject")),
                    description=_clean_text(row.get("description")),
                    channel=_clean_text(row.get("channel")),
                    assigned_to=_clean_text(row.get("assigned_to")),
                    last_customer_message_at=_parse_dt(
                        row.get("last_customer_message_at")
                    ),
                    historical_resolution=_clean_text(
                        row.get("historical_resolution")
                    ),
                )
            )

        db.commit()

        print(
            "[load_workbook] Successfully reloaded "
            f"{len(accounts_df)} accounts, "
            f"{len(orders_df)} orders, "
            f"{len(tickets_df)} tickets."
        )

    except (SQLAlchemyError, ValueError, TypeError):
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Load ParcelPilot workbook data."
    )
    parser.add_argument(
        "--path",
        required=True,
        help="Path to ParcelPilot_Assessment_Data.xlsx",
    )

    args = parser.parse_args()
    load_workbook(args.path)