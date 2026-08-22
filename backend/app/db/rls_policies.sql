-- Postgres Row-Level Security: second, independent enforcement layer.
-- Even if a bug in the application repository layer forgets to filter by account_id,
-- these policies still block cross-account reads/writes at the database engine itself.
--
-- Session variables are set per-request by app.db.repository.scoped_session() via
-- SET LOCAL app.current_account_id / app.current_role, scoped to the transaction.

ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE escalations ENABLE ROW LEVEL SECURITY;

CREATE POLICY internal_full_access_accounts ON accounts
  USING (current_setting('app.current_role', true) IN ('support_agent', 'manager'));

CREATE POLICY internal_full_access_orders ON orders
  USING (current_setting('app.current_role', true) IN ('support_agent', 'manager'));

CREATE POLICY internal_full_access_tickets ON tickets
  USING (current_setting('app.current_role', true) IN ('support_agent', 'manager'));

CREATE POLICY internal_full_access_escalations ON escalations
  USING (current_setting('app.current_role', true) IN ('support_agent', 'manager'));

CREATE POLICY customer_scoped_accounts ON accounts
  USING (
    current_setting('app.current_role', true) = 'customer'
    AND account_id = current_setting('app.current_account_id', true)
  );

CREATE POLICY customer_scoped_orders ON orders
  USING (
    current_setting('app.current_role', true) = 'customer'
    AND account_id = current_setting('app.current_account_id', true)
  );

CREATE POLICY customer_scoped_tickets ON tickets
  USING (
    current_setting('app.current_role', true) = 'customer'
    AND account_id = current_setting('app.current_account_id', true)
  );

CREATE POLICY customer_scoped_escalations ON escalations
  USING (
    current_setting('app.current_role', true) = 'customer'
    AND account_id = current_setting('app.current_account_id', true)
  );
