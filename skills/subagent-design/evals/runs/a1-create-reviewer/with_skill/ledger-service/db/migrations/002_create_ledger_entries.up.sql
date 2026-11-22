SET lock_timeout = '5s';
CREATE TABLE ledger_entries (id bigserial PRIMARY KEY, account_id bigint NOT NULL REFERENCES accounts(id), amount_cents bigint NOT NULL, created_at timestamptz NOT NULL DEFAULT now());
