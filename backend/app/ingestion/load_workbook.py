"""
Loads accounts/orders/tickets directly from ParcelPilot_Assessment_Data.xlsx, overwriting
the hardcoded seed_data.py rows with the real source-of-truth file. Run this if you replace
the workbook with a different/extended dataset for grading.

Usage:
    python -m app.ingestion.load_workbook --path ../data_pack/ParcelPilot_Assessment_Data.xlsx
"""
import argparse
from datetime import datetime
import pandas as pd
from app.db.session import SessionLocal
from app.db.models import Account, Order, Ticket


def _parse_dt(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, datetime):
        return value
    return pd.to_datetime(value).to_pydatetime()


def load_workbook(path: str):
    xls = pd.ExcelFile(path)
    db = SessionLocal()
    try:
        readme = xls.parse("README")
        print("[load_workbook] README sheet loaded (dataset snapshot / notes):")
        print(readme.to_string(index=False))

        accounts_df = xls.parse("accounts")
        orders_df = xls.parse("orders")
        tickets_df = xls.parse("tickets")

        db.query(Ticket).delete()
        db.query(Order).delete()
        db.query(Account).delete()
        db.commit()

        for _, row in accounts_df.iterrows():
            db.add(Account(
                account_id=row["account_id"], account_name=row["account_name"],
                plan=row["plan"], status=row["status"], csm=row.get("csm"),
                contract_file=row.get("contract_file") if pd.notna(row.get("contract_file")) else None,
                premium_support=bool(row.get("premium_support", False)),
                notes=row.get("notes"),
            ))

        for _, row in orders_df.iterrows():
            db.add(Order(
                order_id=row["order_id"], account_id=row["account_id"], carrier=row.get("carrier"),
                status=row["status"], booked_at=_parse_dt(row.get("booked_at")),
                pickup_window_start=_parse_dt(row.get("pickup_window_start")),
                pickup_window_end=_parse_dt(row.get("pickup_window_end")),
                pickup_actual_at=_parse_dt(row.get("pickup_actual_at")),
                shipment_fee_inr=float(row.get("shipment_fee_inr", 0) or 0),
                carrier_fault=bool(row.get("carrier_fault", False)),
                customer_fault=bool(row.get("customer_fault", False)),
                cancellation_requested_at=_parse_dt(row.get("cancellation_requested_at")),
                notes=row.get("notes"),
            ))

        for _, row in tickets_df.iterrows():
            db.add(Ticket(
                ticket_id=row["ticket_id"], account_id=row["account_id"],
                created_at=_parse_dt(row.get("created_at")), status=row["status"],
                subject=row.get("subject"), description=row.get("description"),
                channel=row.get("channel"), assigned_to=row.get("assigned_to"),
                last_customer_message_at=_parse_dt(row.get("last_customer_message_at")),
                historical_resolution=row.get("historical_resolution")
                if pd.notna(row.get("historical_resolution")) else None,
            ))

        db.commit()
        print("[load_workbook] accounts/orders/tickets reloaded from workbook.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True)
    args = parser.parse_args()
    load_workbook(args.path)
