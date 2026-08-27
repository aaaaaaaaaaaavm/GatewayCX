# Programmes and prior art map

GatewayCX is connective architecture. It should become useful by joining mature work cleanly, not
by renaming work that already exists.

| Programme or field | Publicly demonstrated or specified | GatewayCX use | Boundary |
|---|---|---|---|
| LunaNet / LNIS V5 | Cooperative lunar communications, PNT and information-service framework | Primary lunar interoperability baseline | GatewayCX does not claim to invent a lunar network |
| LLCD | 40–622 Mbps lunar optical downlink and 10–20 Mbps uplink | Evidence that a high-capacity lunar optical trunk is physically plausible | A 2013–2014 demonstration is not an operational service SLA |
| LLCD + DTN trial | BP/LTP/CFDP traffic over a real lunar optical link and virtual relay topology | Evidence that optical capacity and disruption-aware delivery compose | Does not validate GatewayCX service semantics |
| DSOC | Optical data delivery from deep-space distances, including 267 Mbps at 31 million km | Evidence that optical communications can augment RF far beyond lunar distance | A technology demonstration is not a general-purpose network |
| CCSDS / IETF DTN | BPv7, security and schedule-aware routing foundations | Delayed and disrupted traffic plane | Not assumed suitable for interactive traffic |
| 3GPP NTN | Standardised cellular non-terrestrial access work | Candidate surface/orbital access and mobility patterns | Access network, not the full Earth–Moon Internet |
| Terrestrial CDNs and edge clouds | Service replication and latency-aware placement | Starting pattern for lunar regional services | Lunar power, thermal, radiation and contact constraints differ |
| Commercial optical terminals | Replaceable space and ground bearer implementations | Candidate adapters beneath a capability interface | Marketing claims do not establish profile conformance |
| Orbital compute programmes | Emerging in-space processing and storage demonstrations | Evidence source for deployment trade studies | No assumed lunar availability, economics or durability |

## The integration gap I am testing

The unresolved work is between the layers:

- how a browser keeps the same name and trust relationship when the useful service instance is on
  the Moon;
- how authoritative and replicated state reconcile after an Earth-link interruption;
- which traffic remains IP-native and which traffic becomes store-and-forward;
- how optical and RF capacity can be scheduled without binding the service plane to one vendor;
- how a lunar regional operator exposes availability, accounting and incident state across
  providers; and
- how success is tested from the application, network and bearer viewpoints at the same time.

Those are the questions this repository can answer without pretending to have built the terminal,
relay constellation or data centre.

## Commercial evidence rule

A commercial supplier is recorded at one of four evidence levels:

1. **Marketed:** a public page describes the capability.
2. **Specified:** a dated, testable public interface or performance envelope exists.
3. **Demonstrated:** a traceable test report shows the capability under stated conditions.
4. **Qualified:** the capability passes a published GatewayCX profile and conformance suite.

No company moves between levels because its technology appears to fit the architecture. Astrogate
and similar optical-terminal companies are possible implementations of an open bearer interface,
not dependencies of the project.
