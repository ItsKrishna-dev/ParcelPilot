"""
Seed data mirroring ParcelPilot_Assessment_Data.xlsx (accounts, orders, tickets sheets) and
the 6 supplied documents' metadata (status/effective_date), so `init_db.py` can stand the
system up without needing the original files re-parsed on every fresh clone.

Overwritten by ingestion/load_workbook.py and ingestion/pdf_loader.py when run against the
real source files.
"""

ACCOUNTS = [
    dict(account_id="ACCT-001", account_name="Northstar Logistics", plan="Enterprise", status="active",
         csm="Priya Mehta", contract_file="05_Northstar_Logistics_Enterprise_Agreement.pdf",
         premium_support=True, notes="Strategic account. Contract contains custom SLA and cancellation terms."),
    dict(account_id="ACCT-002", account_name="LumenWorks", plan="Growth", status="active",
         csm="Arjun Rao", contract_file="06_LumenWorks_Service_Agreement.pdf",
         premium_support=False, notes="Growth customer with contract-specific service credit terms."),
    dict(account_id="ACCT-003", account_name="Beacon Retail", plan="Standard", status="active",
         csm="Neha Kapoor", contract_file=None,
         premium_support=False, notes="No custom agreement in the supplied pack; standard policies apply."),
    dict(account_id="ACCT-004", account_name="Axis Labs", plan="Enterprise", status="active",
         csm="Priya Mehta", contract_file=None,
         premium_support=False, notes="Enterprise plan; standard Enterprise support policy applies."),
]

ORDERS = [
    dict(order_id="ORD-1001", account_id="ACCT-001", carrier="SwiftShip", status="BOOKED",
         booked_at="2026-08-16T09:00:00", pickup_window_start="2026-08-16T10:30:00",
         pickup_window_end="2026-08-16T11:30:00", pickup_actual_at=None, shipment_fee_inr=4200,
         carrier_fault=False, customer_fault=False, cancellation_requested_at="2026-08-16T11:00:00",
         notes="Customer asks to cancel. Shipment has not been picked up."),
    dict(order_id="ORD-1002", account_id="ACCT-001", carrier="BlueDart Pro", status="PICKED_UP",
         booked_at="2026-08-16T08:10:00", pickup_window_start="2026-08-16T09:00:00",
         pickup_window_end="2026-08-16T10:00:00", pickup_actual_at="2026-08-16T09:35:00", shipment_fee_inr=5100,
         carrier_fault=False, customer_fault=False, cancellation_requested_at="2026-08-16T10:20:00",
         notes="Customer later asked to cancel after pickup."),
    dict(order_id="ORD-2001", account_id="ACCT-002", carrier="SwiftShip", status="BOOKED",
         booked_at="2026-08-16T09:00:00", pickup_window_start="2026-08-16T11:00:00",
         pickup_window_end="2026-08-16T12:00:00", pickup_actual_at=None, shipment_fee_inr=1800,
         carrier_fault=False, customer_fault=False, cancellation_requested_at="2026-08-16T10:15:00",
         notes="Cancellation requested 75 minutes after booking; not yet picked up."),
    dict(order_id="ORD-2002", account_id="ACCT-002", carrier="RoadRunner", status="BOOKED",
         booked_at="2026-08-16T04:30:00", pickup_window_start="2026-08-16T05:30:00",
         pickup_window_end="2026-08-16T06:30:00", pickup_actual_at=None, shipment_fee_inr=2400,
         carrier_fault=True, customer_fault=False, cancellation_requested_at=None,
         notes="Pickup missed. Carrier accepted fault. Still not picked up at dataset snapshot."),
    dict(order_id="ORD-3001", account_id="ACCT-003", carrier="RoadRunner", status="BOOKED",
         booked_at="2026-08-16T10:25:00", pickup_window_start="2026-08-16T12:00:00",
         pickup_window_end="2026-08-16T13:00:00", pickup_actual_at=None, shipment_fee_inr=1200,
         carrier_fault=False, customer_fault=False, cancellation_requested_at="2026-08-16T10:40:00",
         notes="Cancellation requested within 30 minutes of booking."),
    dict(order_id="ORD-4001", account_id="ACCT-004", carrier="SwiftShip", status="DELIVERED",
         booked_at="2026-08-14T14:00:00", pickup_window_start="2026-08-15T09:00:00",
         pickup_window_end="2026-08-15T10:00:00", pickup_actual_at="2026-08-15T09:20:00", shipment_fee_inr=3600,
         carrier_fault=False, customer_fault=False, cancellation_requested_at=None,
         notes="Completed delivery."),
]

TICKETS = [
    dict(ticket_id="TKT-501", account_id="ACCT-001", created_at="2026-08-16T10:30:00", status="open",
         subject="All shipment creation is failing",
         description="Every user at Northstar gets HTTP 500 when creating any shipment. Existing shipments can still be viewed.",
         channel="email", assigned_to="Rohit", last_customer_message_at="2026-08-16T10:52:00",
         historical_resolution=None),
    dict(ticket_id="TKT-502", account_id="ACCT-002", created_at="2026-08-16T09:45:00", status="open",
         subject="Bulk upload fails for 4,200-row CSV",
         description="The CSV reaches roughly 70% and fails. Creating shipments one-by-one still works.",
         channel="chat", assigned_to="Maya", last_customer_message_at="2026-08-16T10:40:00",
         historical_resolution=None),
    dict(ticket_id="TKT-503", account_id="ACCT-003", created_at="2026-08-16T10:05:00", status="open",
         subject="How do we change the billing contact?",
         description="Customer wants to replace the billing-contact email on their account.",
         channel="email", assigned_to="Rohit", last_customer_message_at="2026-08-16T10:05:00",
         historical_resolution=None),
    dict(ticket_id="TKT-504", account_id="ACCT-001", created_at="2026-08-16T10:50:00", status="open",
         subject="SwiftShip order still shows BOOKED after driver pickup",
         description="Driver collected the parcel around 10 minutes ago, but ParcelPilot still shows BOOKED.",
         channel="chat", assigned_to="Maya", last_customer_message_at="2026-08-16T10:58:00",
         historical_resolution=None),
    dict(ticket_id="TKT-505", account_id="ACCT-004", created_at="2026-08-16T08:30:00", status="open",
         subject="Possible API key exposure",
         description="An employee accidentally posted a screenshot containing a production API key in a public channel. They are asking what to do.",
         channel="email", assigned_to="Rohit", last_customer_message_at="2026-08-16T09:10:00",
         historical_resolution=None),
    dict(ticket_id="TKT-450", account_id="ACCT-001", created_at="2026-07-12T14:10:00", status="closed",
         subject="Cancellation fee after 30 minutes",
         description="Northstar asked whether a BOOKED shipment could be cancelled 90 minutes after booking before pickup.",
         channel="email", assigned_to="Maya", last_customer_message_at="2026-07-12T15:00:00",
         historical_resolution="Agent told customer a INR 250 cancellation fee applied after 30 minutes."),
    dict(ticket_id="TKT-451", account_id="ACCT-002", created_at="2026-08-11T11:20:00", status="closed",
         subject="Bulk upload fails for large CSV",
         description="LumenWorks reported failures when uploading 3,500-row CSV files.",
         channel="chat", assigned_to="Rohit", last_customer_message_at="2026-08-11T12:10:00",
         historical_resolution="Agent told customer Growth plan only supports 3,000 rows."),
]

DOCUMENTS_META = [
    dict(doc_id="DOC-01", filename="01_Support_Policy_v3_CURRENT.pdf", doc_type="support_policy",
         status="CURRENT", effective_date="2026-05-01", account_id=None),
    dict(doc_id="DOC-02", filename="02_Support_Policy_v2_DEPRECATED.pdf", doc_type="support_policy",
         status="DEPRECATED", effective_date="2025-01-01", account_id=None),
    dict(doc_id="DOC-03", filename="03_Cancellation_and_Service_Credit_SOP_v4.pdf", doc_type="sop",
         status="CURRENT", effective_date="2026-06-15", account_id=None),
    dict(doc_id="DOC-04", filename="04_Product_Operations_Guide_and_Known_Issues.pdf", doc_type="product_ops",
         status="CURRENT", effective_date="2026-08-14", account_id=None),
    dict(doc_id="DOC-05", filename="05_Northstar_Logistics_Enterprise_Agreement.pdf", doc_type="agreement",
         status="CURRENT", effective_date="2026-01-01", account_id="ACCT-001"),
    dict(doc_id="DOC-06", filename="06_LumenWorks_Service_Agreement.pdf", doc_type="agreement",
         status="CURRENT", effective_date="2026-03-01", account_id="ACCT-002"),
]

SOURCE_AUTHORITY_RULES = [
    dict(source_type="agreement", doc_status="CURRENT", precedence_rank=1, applies_to_clause="cancellation_fee", notes=None),
    dict(source_type="agreement", doc_status="CURRENT", precedence_rank=1, applies_to_clause="service_credit", notes=None),
    dict(source_type="agreement", doc_status="CURRENT", precedence_rank=1, applies_to_clause="sla", notes=None),
    dict(source_type="sop", doc_status="CURRENT", precedence_rank=2, applies_to_clause="cancellation_fee", notes=None),
    dict(source_type="sop", doc_status="CURRENT", precedence_rank=2, applies_to_clause="service_credit", notes=None),
    dict(source_type="support_policy", doc_status="CURRENT", precedence_rank=3, applies_to_clause="sla", notes=None),
    dict(source_type="support_policy", doc_status="CURRENT", precedence_rank=3, applies_to_clause="severity", notes=None),
    dict(source_type="product_ops", doc_status="CURRENT", precedence_rank=4, applies_to_clause="product_defect", notes=None),
    dict(source_type="support_policy", doc_status="DEPRECATED", precedence_rank=99, applies_to_clause="general",
         notes="Never used for current answers; explicit-history-request only, always labeled DEPRECATED."),
    dict(source_type="historical_ticket", doc_status="ADVISORY_ONLY", precedence_rank=999, applies_to_clause="general",
         notes="Context only. May contain incorrect guidance. Never used to compute a fee/credit/SLA number."),
]

CONTRACT_RULES_SEED = [
    # Northstar (ACCT-001, DOC-05)
    dict(
        account_id="ACCT-001", doc_id="DOC-05", clause_type="cancellation_fee",
        rule_key="cancellation_fee_waived", value_boolean=True, value_number=None,
        value_text=None, unit=None,
        source_text="may cancel any BOOKED shipment before pickup with no cancellation fee",
        is_active=True,
    ),
    dict(
        account_id="ACCT-001", doc_id="DOC-05", clause_type="service_credit",
        rule_key="service_credit_monthly_cap_inr", value_boolean=None, value_number=5000.0,
        value_text=None, unit="INR",
        source_text="Monthly aggregate service credits are capped at INR 5,000",
        is_active=True,
    ),
    dict(
        account_id="ACCT-001", doc_id="DOC-05", clause_type="sla",
        rule_key="sla_p1_minutes", value_boolean=None, value_number=15.0,
        value_text=None, unit="minutes", source_text="P1: 15 minutes", is_active=True,
    ),
    dict(
        account_id="ACCT-001", doc_id="DOC-05", clause_type="sla",
        rule_key="sla_p2_minutes", value_boolean=None, value_number=60.0,
        value_text=None, unit="minutes", source_text="P2: 1 hour", is_active=True,
    ),
    dict(
        account_id="ACCT-001", doc_id="DOC-05", clause_type="sla",
        rule_key="sla_p3_minutes", value_boolean=None, value_number=480.0,
        value_text=None, unit="minutes", source_text="P3: 8 business hours", is_active=True,
    ),
    # LumenWorks (ACCT-002, DOC-06)
    dict(
        account_id="ACCT-002", doc_id="DOC-06", clause_type="cancellation_fee",
        rule_key="cancellation_fee_waived", value_boolean=False, value_number=None,
        value_text=None, unit=None,
        source_text="No special cancellation-fee waiver applies", is_active=True,
    ),
    dict(
        account_id="ACCT-002", doc_id="DOC-06", clause_type="service_credit",
        rule_key="service_credit_delay_threshold_hours", value_boolean=None, value_number=4.0,
        value_text=None, unit="hours", source_text="pickup is more than 4 hours past", is_active=True,
    ),
    dict(
        account_id="ACCT-002", doc_id="DOC-06", clause_type="service_credit",
        rule_key="service_credit_fixed_amount_inr", value_boolean=None, value_number=300.0,
        value_text=None, unit="INR", source_text="fixed INR 300 service credit", is_active=True,
    ),
    dict(
        account_id="ACCT-002", doc_id="DOC-06", clause_type="sla",
        rule_key="sla_p1_minutes", value_boolean=None, value_number=120.0,
        value_text=None, unit="minutes", source_text="P1: 2 business hours", is_active=True,
    ),
    dict(
        account_id="ACCT-002", doc_id="DOC-06", clause_type="sla",
        rule_key="sla_p2_minutes", value_boolean=None, value_number=240.0,
        value_text=None, unit="minutes", source_text="P2: 4 business hours", is_active=True,
    ),
    dict(
        account_id="ACCT-002", doc_id="DOC-06", clause_type="sla",
        rule_key="sla_p3_minutes", value_boolean=None, value_number=960.0,
        value_text=None, unit="minutes", source_text="P3: 2 business days", is_active=True,
    ),
]
