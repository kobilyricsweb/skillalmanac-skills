-- sqlcheck: ignore-file non-transactional-migration
SELECT * FROM lookup_codes; -- sqlcheck: ignore select-star, missing-limit
-- sqlcheck: ignore delete-without-where
DELETE FROM scratch_tmp;
DELETE FROM scratch_two;
