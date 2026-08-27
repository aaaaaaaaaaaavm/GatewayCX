# ADR-0002: Native IP when continuous, disruption tolerance when required

- **Status:** provisional
- **Date:** 2026-08-27

## Context

Using DTN everywhere would make existing applications unnecessarily foreign. Pretending a
continuous IP path always exists would make interruption handling somebody else's outage.

## Decision

GatewayCX will preserve native IP end to end during continuous operation. A resilience service may
use BPv7 or another explicitly specified store-and-forward mechanism for traffic that accepts
deferred semantics. Gateways shall expose the transition rather than silently changing delivery
guarantees.

S005 refines the boundary:

- native HTTPS retains its original application TLS endpoints and fails honestly through an
  arbitrary partition;
- a service-owner terminating proxy may durably accept work, but it creates a new TLS and trust
  boundary;
- an opaque deferred object may retain application-to-application payload confidentiality, but it
  requires a delay-aware object contract; and
- local durable acceptance, BP adapter delivery and remote application completion are separate
  states. Remote completion requires an application receipt bound to an idempotency key.

## Consequences

- Existing clients have a direct compatibility path.
- Delay-aware applications can request durable delivery.
- The semantic boundary is modelled in S005. Gateway software, security profiles and fault-injected
  protocol evidence remain open under P02.
- The decision may change after packet-level and fault-injection evidence.
