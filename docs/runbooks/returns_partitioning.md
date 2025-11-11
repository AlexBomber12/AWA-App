# Returns Raw Partitioning Scaffold

This runbook documents the scaffold shipped with migration
`6ea19ad3bc8a_pr_opt_5_indexes_cache_mv`. The revision introduces an optional,
opt-in partitioned copy of `returns_raw` so the table can be converted to
monthly range partitions during a later maintenance window without blocking
the current deploy.

## When to enable

Set `RETURNS_PARTITION_SCAFFOLD=1` in the migration environment **only** during
the maintenance window where you plan to copy/attach the data. With the flag
unset (default) the upgrade behaves as a no-op beyond the new indexes, so the
scaffold never touches production tables accidentally.

## High-level flow

1. **Prep:** enable the env var and rerun the migration:
   ```bash
   RETURNS_PARTITION_SCAFFOLD=1 alembic -c services/api/alembic.ini upgrade head
   ```
   This creates a partitioned staging table `returns_raw_partitioned` plus
   child partitions such as `returns_raw_2025_11` built with `LIKE returns_raw
   INCLUDING ALL`, so constraints and indexes mirror the primary table.
2. **Copy:** insert data into the partitioned table in bounded batches. For
   example, to move November 2025 returns:
   ```sql
   INSERT INTO returns_raw_partitioned
   SELECT *
   FROM returns_raw
   WHERE return_date >= '2025-11-01' AND return_date < '2025-12-01';
   ```
   Repeat per month or drive the process with `COPY` from the archival table.
3. **Validate:** compare row counts and spot-check aggregates before cutting
   traffic over:
   ```sql
   SELECT COUNT(*) FROM returns_raw WHERE return_date BETWEEN '2025-11-01' AND '2025-11-30';
   SELECT COUNT(*) FROM returns_raw_partitioned WHERE return_date BETWEEN '2025-11-01' AND '2025-11-30';
   ```
4. **Attach:** once the backfill completes, atomically swap the tables:
   ```sql
   ALTER TABLE returns_raw RENAME TO returns_raw_legacy;
   ALTER TABLE returns_raw_partitioned RENAME TO returns_raw;
   ```
   Existing partitions (e.g. `returns_raw_2025_11`) remain attached and future
   partitions can be created with the same `CREATE TABLE ... PARTITION OF`
   pattern from the migration.
5. **Analyze & cleanup:** run `ANALYZE returns_raw;` so the planner knows about
   the new partitions, then drop `returns_raw_legacy` once verification and
   fallback windows expire.

## Notes

- The scaffold seeds partitions for the previous month, the current month, and
  the next five months. Create additional partitions as needed:
  ```sql
  CREATE TABLE returns_raw_2026_01
    PARTITION OF returns_raw
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
  ```
- Because each partition inherits the indexes from `returns_raw`, queries using
  `vendor`, `return_date`, or `asin` automatically benefit from the new
  `btree` indexes added in this PR.
- Keep the maintenance log updated with the copy/attach/rename timestamps so
  cache invalidation and ETL teams know when to resume normal imports.
