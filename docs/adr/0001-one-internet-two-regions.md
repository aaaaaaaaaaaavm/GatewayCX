# ADR-0001: One logical Internet, two autonomous regions

- **Status:** accepted
- **Date:** 2026-08-27

## Context

A transparent extension of the terrestrial Internet is the user goal. An Earth-dependent lunar
LAN is nevertheless unsafe and unpleasant because every service dependency pays cislunar delay
and the entire region fails when the backbone does.

## Decision

GatewayCX will model Earth and the Moon as autonomous Internet regions joined by a cislunar
interconnect. They share compatible addressing, naming, identity, trust and service interfaces.
Each region can host services and route local traffic without the other.

## Consequences

- "One Internet" means interoperability and common user-facing semantics, not one failure domain.
- Lunar DNS, identity, storage and compute are architecture components, not optional accelerators.
- Data placement and consistency become network-design questions.
- A later planetary region can join through the same federation model.

