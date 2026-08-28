# GatewayCX interoperability layering

GatewayCX is a service and operations profile around the lunar communications standards ecosystem.
It is not a competing network architecture, a new Bundle Protocol, or a substitute for LunaNet.

## Baseline boundary

LunaNet Interoperability Specification (LNIS) V5 is the current programme baseline. GatewayCX
inherits its network-of-networks model and treats these LNIS V5 interfaces as upstream constraints:

| LNIS V5 surface | GatewayCX treatment |
|---|---|
| §3.1.1.2 real-time IP service | Inherit IPv4/IPv6 forwarding for continuous paths. |
| §3.1.2 DTN service | Inherit BPv7 and the applicable convergence-layer choices; do not redefine bundle semantics. |
| §3.1.3 address and ID registration | Use IANA/SANA registration processes where applicable. |
| §4.5 LNSP-user network interfaces | Present ordinary regional IP and BPv7 service over compliant or bilaterally defined links. |
| §5.1 inter-provider communications | Add testable scheduling, availability, accounting and incident semantics. |
| §6.1 and §6.4 provider crosslinks | Keep GX-B1 bearer-neutral while passing LNIS-compatible IP packets or BPv7 bundles. |

LNIS V5 deliberately allows LNSPs to offer services beyond the common baseline, while warning that
those additions are not automatically interoperable. GatewayCX therefore profiles additions only at
named seams and supplies conformance tests for them. A GatewayCX implementation must still claim
LNIS conformance at the individual service or interface level, exactly as LNIS defines it; passing a
GatewayCX test must never be presented as blanket LunaNet compliance.

## Where GatewayCX adds value

| Layer | Inherited mechanism | GatewayCX work product |
|---|---|---|
| User experience | DNS, IPv4/IPv6, TLS, HTTP, email and file protocols | Measure correctness and usability at lunar delay; keep one namespace and ordinary clients. |
| Lunar region | IP-capable local links and provider networks | Local DNS, identity, cache, compute and essential-service autonomy. |
| Disrupted delivery | BPv7, BPSec and convergence layers | Map application acceptance, bundle delivery and remote completion into an explicit durable ledger. |
| Bearers | LNIS links plus permitted external connectivity | GX-B1 capability, contact, acquisition, capacity, failure and fallback abstraction. |
| Operations | Provider scheduling and health exchange | GX-O1 traces, fault taxonomy, reconciliation, black start and recovery experiments. |
| Federation | Multiple public and private LNSPs | Identity federation, policy, accounting, settlement, incident and service-level semantics. |
| Commercial service | Provider-specific offerings | Cost per delivered bit, retained bit, availability class and regional-compute trade models. |

The invention target is the composition: an Earth-like service experience across an autonomous
lunar region and a disruption-aware, multi-provider backbone. Each underlying protocol remains
owned and evolved by its standards community.

## Operational DTN changes the starting point

NASA states that completion of its multi-centre DTN Project in January 2026 made DTN an operational
service in both the Near Space Network and Deep Space Network. GatewayCX therefore treats DTN as
deployed infrastructure to interoperate with, not an unproven protocol concept to recreate.

This does not prove a GatewayCX gateway interoperates with NASA, nor does it remove the need to test
specific BPv7 implementations, BPSec profiles, endpoint identifiers, convergence layers, contact
plans and operational policy. It raises the evidence bar: M2 must cross a real BPv7 implementation
boundary and preserve the GX-A1 ledger and authentication invariants under injected faults.

## Conformance claim grammar

Every future claim should use one of these bounded forms:

- **LNIS-mapped:** the GatewayCX interface has an explicit mapping to an LNIS V5 service or
  interface, but has not been tested for conformance.
- **GatewayCX-conformant:** an implementation passes the stated GatewayCX profile tests; this is not
  an LNIS certification.
- **BPv7-interoperated:** two named BPv7 implementations exchanged bundles under a recorded test
  configuration.
- **provider-interoperated:** an independently controlled implementation passed the named seam.
- **hardware-validated:** physical hardware and test conditions are identified.

“LunaNet compliant” is reserved for evidence against the appropriate LNIS specification and
applicable documents. “Operational DTN” describes NASA's network service, not this repository.
