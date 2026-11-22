CREATE TABLE notifications (id bigserial PRIMARY KEY, recipient text NOT NULL, body text NOT NULL, created_at timestamptz NOT NULL DEFAULT now());
