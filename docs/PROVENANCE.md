# Provenance

## What is original here

- The GatewayCX system framing and project requirements
- The architecture decisions and interface organisation
- The deterministic baseline model and scenario definitions
- The interpretation and comparison of generated results

## What is inherited

GatewayCX does not invent IP, DNS, TLS, QUIC, DTN, optical communications, lunar relays, edge
computing or content delivery networks. Public standards and programmes are listed in
[`references/SOURCES.md`](../references/SOURCES.md). Their inclusion is research provenance, not
an endorsement of this architecture.

## Current computation

The baseline uses:

- speed of light in vacuum: 299,792.458 km/s;
- scenario distance: 384,400 km;
- path-specific one-way processing delay;
- path bottleneck capacity;
- declared sequential dependency round trips; and
- declared transfer bytes and availability.

It does not presently model orbital geometry, atmospheric optical availability, congestion,
packet loss, transport congestion control, queue discipline, forward-error correction, antenna
pointing, protocol headers, compute time or user demand distributions.

## Validation status

The tests verify equations, parsing, invariants and relative scenario outcomes. They do not
validate the model against a lunar communication link. There are currently:

- no hardware measurements;
- no packet-level network-emulation results;
- no vendor-private performance inputs;
- no flight data; and
- no independent implementation.

That is an ordinary starting point. Concealing it would not improve the engineering.

