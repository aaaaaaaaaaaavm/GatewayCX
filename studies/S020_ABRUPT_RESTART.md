# S020 — Abrupt transaction-boundary restart

## Question

Does the S017 SQLite traffic ledger recover to a valid committed state when its writer is killed
without closing the database, both before and after a transaction commit?

## Method

`python -m gatewaycx.abrupt_restart` seeds one committed traffic unit, then starts two distinct
writer processes over the same temporary WAL-mode database:

1. the first begins an immediate transaction, inserts a unit, reports that it is still before
   commit and is terminated with `SIGKILL`;
2. the database is reopened and checked;
3. the second inserts another unit, commits, reports that it has not closed the connection and is
   terminated with `SIGKILL`; and
4. the database is reopened, checked and given one new recovery unit.

The worker-ready files coordinate deterministic fault boundaries. They contain process metadata
only and are excluded from the committed result.

## Result

[`results/S020_abrupt_restart.json`](../results/S020_abrupt_restart.json) records that:

- the pre-commit unit is absent while the earlier stable unit remains;
- the committed unit remains after kill-before-close;
- SQLite `integrity_check` returns `ok` after both terminations;
- the byte ledger remains conserved; and
- the recovered store accepts new work.

This closes a narrow abrupt-process fault at two coordinated transaction boundaries. It does not
exercise arbitrary instruction timing, kernel failure, filesystem corruption, storage-device
cache loss or electrical power removal. It therefore does not qualify SQLite, the filesystem,
storage hardware or a flight computer for lunar service.
