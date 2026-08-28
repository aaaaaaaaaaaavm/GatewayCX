# Durable traffic ledger

## Purpose

An adapter cannot truthfully return `accepted_pending` for disconnected delivery unless the
accepted state outlives the transient link state—and, for operational use, the gateway process.
GatewayCX therefore separates bearer control from a traffic ledger. GX-A1 can use an in-memory
ledger for deterministic interface tests or a SQLite-backed ledger for restart tests.

The SQLite binding is a reference implementation, not a required flight database.

## Stored state

Each row contains only:

- a stable traffic-unit identifier;
- declared byte count and traffic class;
- the deferred-delivery flag;
- remaining and transmitted byte counts; and
- an insertion sequence used for deterministic FIFO drain.

There is no payload-content column. This makes the store payload-blind, not metadata-free. Traffic
identifiers, timing, classes and sizes can still be sensitive and require access control, retention
policy and encryption decisions in a deployment.

## Invariants

1. `remaining_bytes + transmitted_bytes = payload_bytes` for every accepted traffic unit.
2. A matching repeat of an accepted identifier is `duplicate_known` and changes no counters.
3. A repeat with different size, class or deferred semantics is `duplicate_conflict`.
4. Admission is rejected when current remaining bytes plus the new unit exceed configured capacity.
5. Transmission updates are committed atomically in insertion order.
6. Adapter restart resets link/acquisition state but must not reset traffic progress.

## Current binding

`SQLiteTrafficStore` uses WAL journalling and `synchronous=FULL`; S017 reads both active settings
back from SQLite. The study closes and reopens the file from separate Python processes, then opens
it a third time after recovery.

This does not establish survival through sudden power loss, radiation upset, filesystem failure,
media corruption or concurrent multi-node access. It also does not equate adapter-ledger progress
with BPv7 delivery or remote application completion. Those acknowledgement levels remain separate.
