# ADR-0004: Local-first lunar service placement

- **Status:** accepted
- **Date:** 2026-08-27

## Context

The 2.565-second mean-distance vacuum RTT is paid for every sequential dependency that crosses the
backbone. Adding capacity does not remove it.

## Decision

GatewayCX will treat lunar compute, caching and replication as part of the network architecture.
Services shall state which data and functions must be local, may be cached, may be eventually
consistent, or must remain authoritative on Earth.

## Consequences

- Surface and orbital data centres become explicit trade spaces.
- Service owners must define conflict and recovery behaviour.
- Encrypted content cannot be cached by an untrusted network intermediary; service-provider
  participation or content-addressed distribution is required.
- The baseline model measures avoided dependency RTTs and backbone bytes.

