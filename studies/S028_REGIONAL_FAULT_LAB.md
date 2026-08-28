# S028 — Executable lunar-region fault laboratory

## Question

Can the lunar regional service layer demonstrate bounded failure behaviour with actual signatures,
files, databases, transactions and processes rather than architecture intent alone?

## Experiments

`python -m gatewaycx.regional_fault_lab` runs five isolated experiments:

- **X07 identity:** validates an HMAC-signed offline capability during partition, rejects forgery and
  expiry, then applies a serial revocation after reconnection.
- **X08 consistency:** fails a strong command closed without quorum, reconciles concurrent SQLite
  register writes by a declared rule, and preserves a global limit with regional escrow.
- **X14 update:** hashes and signs real payload bytes, rejects corruption, stages a valid B slot,
  preserves A after a failed health check and rolls back an interrupted SQLite schema transaction.
- **X16 black start:** launches five real child processes with Earth unavailable, then records the
  dependency consequences of lost holdover time.
- **X18 recovery:** injects 60 seeded faults around SQLite transactions, corrupts the database header,
  detects the damage and restores the exact committed row count from a verified backup.

The deterministic record is
[`results/S028_regional_fault_lab.json`](../results/S028_regional_fault_lab.json).

## Boundary

These are reference software mechanisms, not production PKI, a distributed database, secure boot,
real lunar daemons, electrical black start or storage qualification. The value is that each open
policy now has executable failure semantics and a replaceable evidence seam.
