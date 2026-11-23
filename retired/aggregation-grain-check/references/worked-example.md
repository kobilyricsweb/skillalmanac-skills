Synthetic input: orders has one row per order with order_id, customer_id, and total. Items has many rows per order. The proposed computation joins orders to items and sums orders.total by customer_id. No deduplication rule is supplied.

Artifact: orders grain is one row per order; total is additive at order grain. Items has many rows per order. The proposed join can repeat an order row for each item. For total, overall status is `unsafe` and hazards contains `duplication`; no non-additivity hazard is recorded because none was supplied.

Supported alternative: form a distinct set of qualifying order_id values through a semi-join, then aggregate orders.total by customer_id. Do not re-sum a customer aggregate after a one-to-many join.

Verification: the warning follows from the supplied one-to-many relationship and absence of a deduplication rule. No overcount amount is estimated. If the measure were also a non-additive snapshot aggregated across dates, hazards would contain both `duplication` and `non_additivity`.
