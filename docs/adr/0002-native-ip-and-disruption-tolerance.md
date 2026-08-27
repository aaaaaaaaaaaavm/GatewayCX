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

## Consequences

- Existing clients have a direct compatibility path.
- Delay-aware applications can request durable delivery.
- The IP/DTN boundary, security termination and acknowledgement mapping remain open engineering
  work under P02.
- The decision may change after packet-level and fault-injection evidence.

