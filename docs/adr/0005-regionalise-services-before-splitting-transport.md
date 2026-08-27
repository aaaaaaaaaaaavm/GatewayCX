# ADR-0005: Regionalise services before splitting transport

- **Status:** accepted
- **Date:** 2026-08-27

## Context

Long-delay links create large bandwidth-delay products and slow feedback. A performance-enhancing
proxy can improve some transport behaviour, but it can also terminate end-to-end state, complicate
encryption and introduce failure semantics that the application cannot see.

Most user-perceived delay in the S001 baseline comes from sequential cross-region dependencies. A
transport proxy cannot remove the speed-of-light delay from those dependencies.

## Decision

GatewayCX will first reduce cislunar dependency crossings through explicit service placement,
caching, replication and asynchronous work. It will preserve end-to-end transport and security
where a continuous path exists.

Transport splitting or acceleration remains permitted only as a declared profile with:

- an explicit trust boundary;
- named protocol and traffic scope;
- observable failure and recovery semantics;
- no silent weakening of end-to-end security; and
- a measured benefit over the unsplit baseline.

## Consequences

- “Faster Internet” cannot be claimed from a proxy benchmark alone.
- Lunar data centres and edge services are first-class network components.
- Some applications will remain slow until their dependency graphs are regionalised.
- A provider may implement acceleration, but the open service interface does not require it.
