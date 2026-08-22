-- ParcelPilot PostgreSQL Row-Level Security
--
-- Custom transaction settings:
--   parcelpilot.user_role
--   parcelpilot.account_id
--
-- These names deliberately avoid PostgreSQL reserved keywords such as
-- current_role.

ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE escalations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS internal_full_access_accounts ON accounts;
DROP POLICY IF EXISTS internal_full_access_orders ON orders;
DROP POLICY IF EXISTS internal_full_access_tickets ON tickets;
DROP POLICY IF EXISTS internal_full_access_escalations ON escalations;

DROP POLICY IF EXISTS customer_scoped_accounts ON accounts;
DROP POLICY IF EXISTS customer_scoped_orders ON orders;
DROP POLICY IF EXISTS customer_scoped_tickets ON tickets;
DROP POLICY IF EXISTS customer_scoped_escalations ON escalations;

CREATE POLICY internal_full_access_accounts
ON accounts
USING (
    current_setting(
        'parcelpilot.user_role',
        true
    ) IN ('support_agent', 'manager')
);

CREATE POLICY internal_full_access_orders
ON orders
USING (
    current_setting(
        'parcelpilot.user_role',
        true
    ) IN ('support_agent', 'manager')
);

CREATE POLICY internal_full_access_tickets
ON tickets
USING (
    current_setting(
        'parcelpilot.user_role',
        true
    ) IN ('support_agent', 'manager')
);

CREATE POLICY internal_full_access_escalations
ON escalations
USING (
    current_setting(
        'parcelpilot.user_role',
        true
    ) IN ('support_agent', 'manager')
);

CREATE POLICY customer_scoped_accounts
ON accounts
USING (
    current_setting(
        'parcelpilot.user_role',
        true
    ) = 'customer'
    AND account_id = current_setting(
        'parcelpilot.account_id',
        true
    )
);

CREATE POLICY customer_scoped_orders
ON orders
USING (
    current_setting(
        'parcelpilot.user_role',
        true
    ) = 'customer'
    AND account_id = current_setting(
        'parcelpilot.account_id',
        true
    )
);

CREATE POLICY customer_scoped_tickets
ON tickets
USING (
    current_setting(
        'parcelpilot.user_role',
        true
    ) = 'customer'
    AND account_id = current_setting(
        'parcelpilot.account_id',
        true
    )
);

CREATE POLICY customer_scoped_escalations
ON escalations
USING (
    current_setting(
        'parcelpilot.user_role',
        true
    ) = 'customer'
    AND account_id = current_setting(
        'parcelpilot.account_id',
        true
    )
);