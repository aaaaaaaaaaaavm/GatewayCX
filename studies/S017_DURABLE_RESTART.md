# S017 — cross-process durable traffic-ledger restart

## Question

Can accepted traffic-unit state and partial transmission progress survive a gateway-process restart
without payload storage, duplicate admission or byte-ledger divergence?

## Method

The deterministic driver creates a temporary SQLite ledger and starts two separate Python worker
processes.

The seed process loads the illustrative RF GX-B1 profile through GX-A1, accepts 122 units of
65,536 bytes, acquires the link and transmits for 100 ms. It closes the adapter with 1,250,000 bytes
transmitted and 6,745,392 bytes queued.

The recovery process opens the same file. Before reacquisition, it records the recovered counters,
submits one matching duplicate and one conflicting duplicate, reacquires, drains the remainder and
closes. The parent opens the ledger a third time to verify the final state. The driver also reads
back the active SQLite WAL and FULL-synchronous modes and inspects the public schema-column list.

## Result

| Checkpoint | Accepted | Transmitted | Queued |
|---|---:|---:|---:|
| Before seed transmission | 7,995,392 B | 0 B | 7,995,392 B |
| Seed process exit | 7,995,392 B | 1,250,000 B | 6,745,392 B |
| Recovery process entry | 7,995,392 B | 1,250,000 B | 6,745,392 B |
| Recovery process exit | 7,995,392 B | 7,995,392 B | 0 B |
| Third open | 7,995,392 B | 7,995,392 B | 0 B |

The matching repeat returns `duplicate_known`; the changed-size repeat returns
`duplicate_conflict`. All thirteen restart, configuration, schema, idempotency and conservation
checks pass. No payload content is supplied to either worker.

The deterministic record is [`results/S017_durable_restart.json`](../results/S017_durable_restart.json).

## Boundary

This is a clean process restart over a local temporary filesystem. It is not an abrupt kill or a
power-loss test, and it does not qualify SQLite, the host filesystem or storage hardware for space.
The database still contains potentially sensitive metadata. A transmitted counter is local adapter
progress, not evidence that a BPv7 destination or application received anything. The RF capacity
remains an illustrative profile input; no modem or physical link participates.
