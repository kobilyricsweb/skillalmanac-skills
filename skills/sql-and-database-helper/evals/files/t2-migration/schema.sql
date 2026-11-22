-- PostgreSQL 14, orders has about 40 million rows and takes writes all day
CREATE TABLE orders (
  id bigserial PRIMARY KEY,
  customer_id bigint NOT NULL REFERENCES customers (id),
  total_cents integer NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
