# Programme method

GatewayCX borrows VOLLEY's useful discipline without copying the size it accumulated.

## One repository until the interfaces stabilise

Architecture, source, scenarios, results and conformance work stay together during the exploratory
phase. A paper or laboratory repository is created only when it has a genuinely different release
cycle. Splitting early would manufacture coordination work before there is an implementation to
coordinate.

## Four records

1. A **requirement** says what the system must do and how it will be verified.
2. An **ADR** records a durable choice and its consequences.
3. A **study** answers one bounded question from committed inputs.
4. A **claim** states what the present evidence permits me to say publicly.

Most work should change one or more of those records. Notes that change none of them probably do
not need a permanent file.

## Evidence before polish

- Models write deterministic machine-readable results.
- CI regenerates them and rejects drift.
- Measurements retain raw configuration and instrument context.
- Independent methods are added where a result controls an architecture decision.
- Failed approaches stay in the record when they explain a decision.

## Office-work discipline

- Decisions name their owner and status.
- Public sources, company decisions and partner-confidential data remain distinct.
- A vendor is described by a capability matrix, not familiarity.
- Legal ownership and publication authority are resolved before proprietary data enter the record.
- Release notes state the actual maturity rather than the hoped-for product.

## Release gate

A tagged baseline requires:

- clean `make verify` output;
- no unsupported headline claim;
- requirements and claim ledger reconciled;
- generated results committed;
- open problems updated; and
- origin, vendor and validation language reviewed.

