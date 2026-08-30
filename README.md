# GatewayCX

**One Internet across Earth and the Moon.**

[![verify](https://github.com/aaaaaaaaaaaavm/GatewayCX/actions/workflows/verify.yml/badge.svg)](https://github.com/aaaaaaaaaaaavm/GatewayCX/actions/workflows/verify.yml)
[![License: Proprietary](https://img.shields.io/badge/license-proprietary-red.svg)](LICENSE)
[![Maturity: architecture study](https://img.shields.io/badge/maturity-architecture%20study-orange.svg)](OPEN_PROBLEMS.md)
[![Validation: model only](https://img.shields.io/badge/validation-model%20only%2C%20unverified-red.svg)](docs/PROVENANCE.md)

The Internet should not stop being the Internet because its next user is 384,400 km away.

GatewayCX is an exploratory cislunar telecommunications architecture and interoperability study that I initiated at
Avisys Services in April 2026. I am working out what it takes for an ordinary terrestrial Internet
client to operate natively across an Earth–Moon network: the same browser, domain names, accounts,
certificates and encrypted services, with no mission-specific application required merely to get
online.

The unavoidable difference is light time. At the mean Earth–Moon separation, ideal propagation is
about 1.282 seconds one way and 2.565 seconds round trip. Relays, queues and processing add to it.
Optical communications can move more bits; they cannot make those bits outrun light.

<p align="center">
  <img src="figures/architecture-overview.svg" alt="GatewayCX Earth, cislunar backbone and lunar regional architecture" width="100%">
</p>

GatewayCX is explicitly a service and operations profile around the existing standards ecosystem.
LunaNet Interoperability Specification V5 is the baseline; IPv4/IPv6 and BPv7 remain the network
mechanisms it defines. NASA's DTN service is operational in the Near Space Network and Deep Space
Network. GatewayCX does not reinvent Bundle Protocol. It makes the remaining product problem
executable: an Earth-like service experience, lunar regional autonomy, bearer abstraction,
multi-provider operations, recovery and commercial service architecture.

The system therefore cannot be a long cable with better marketing. GatewayCX treats Earth and the
Moon as two autonomous Internet regions joined by a resilient cislunar backbone. Ordinary IP runs
where continuity permits. Local lunar compute keeps local work local. Caches and replicas remove
avoidable Earth round trips. Delay-tolerant delivery carries data through interruptions. RF and
optical links are interchangeable bearers beneath an open service interface.

> **Current state, 2026-08-30:** architecture, deterministic models, local fault probes, a
> dual-method native protocol packet matrix at short and mean lunar delay, and one exact external
> BPv7 implementation crossing with a recorded reciprocal parser incompatibility. No flight
> hardware has been built, no optical terminal has been tested, and no lunar network has been
> demonstrated. Every result is labelled as model, test, measurement or external evidence pointer.

## The requirement

The terrestrial Internet must work natively across the Earth–Moon network.

In this repository, *natively* has a testable meaning:

1. An unmodified standards-based client can use ordinary DNS, IP, TLS and HTTPS to reach a service
   in the other region when a continuous path exists.
2. The same names, identities and trust relationships remain valid in both regions.
3. Lunar-local traffic does not travel to Earth merely because Earth operates the service.
4. A lunar region retains essential local service during a cislunar partition.
5. Applications may adopt delay-aware features, but basic connectivity does not depend on them.

Native compatibility is not the same as native performance. A handshake-heavy Earth-hosted page
can work correctly and still feel awful over a 2.6-second baseline round trip. The architecture has
three increasingly difficult success levels:

| Level | Meaning |
|---|---|
| Compatibility | Existing Internet clients and services function across the link. |
| Usability | Lunar caches, replicas and compute remove most avoidable cislunar round trips. |
| Resilience | Essential lunar services continue through backbone outages and reconcile later. |

## Architecture

```mermaid
flowchart LR
    E["Earth region\nInternet + cloud"]
    B["Cislunar backbone\noptical + RF + DTN"]
    L["Lunar region\naccess + routing"]
    C["Lunar compute\ncache + data centres"]
    E <--> B
    B <--> L
    L <--> C
```

The complete system includes the physical bearers, lunar access networks, IP and disruption-aware
networking, naming and identity, distributed compute, applications, service operations and
governance. CRM, BSS and OSS belong in the operations plane. They are useful, but they are not the
project's centre of gravity.

The first deployment domain is cislunar. The final roadmap extends the same regional model to
orbital settlements, Mars and other planetary networks.

## What runs today

The baseline model is deliberately small. It calculates propagation and serialization time,
executes dependency phases, distinguishes local and cislunar paths, and records whether work
completes or queues during a partition.

```bash
python -m gatewaycx.cli run-all
python -m unittest discover -s tests -v
```

The study register establishes the starting point:

| Study | Question |
|---|---|
| S001 | What does an ordinary Earth-hosted web transaction pay across a continuous lunar link? |
| S002 | How much latency and backbone traffic disappear when static and identity services are local? |
| S003 | Which services remain available when the Earth–Moon backbone is down? |
| S004 | Can an unmodified HTTPS client operate through a mean-distance delayed byte path? |
| S005 | What does an application, gateway and remote service know during interruption and recovery? |
| S006 | What in-flight window and outage storage are implied by advertised backbone capacity? |
| S007 | Where should services run under lunar storage, compute and partition constraints? |
| S008 | Can optical and RF bearers expose one vendor-neutral capability contract? |
| S009 | How does RF fallback protect safety traffic without silently starving science? |
| S010 | What continuity is gained by keeping RF warm around an optical outage? |
| S011 | Can lunar services update through interruption without overwriting the working version? |
| S012 | Can forecast-driven prepositioning beat a simple cache baseline without risking essential content? |
| S013 | Can the lunar network restart its essential services without Earth? |
| S014 | Can one provider-neutral flight record reconstruct an interrupted delivery without payload access? |
| S015 | Do bearer handover, durable recovery and diagnostics agree on one traffic ledger? |
| S016 | Can one executable runtime seam apply optical and RF profiles through fault and recovery? |
| S017 | Does accepted partial-transfer state survive a clean gateway-process restart? |
| S018 | Can the GX-A1 adapter run across a process boundary and reject malformed traffic safely? |
| S019 | Can the process boundary authenticate a client and reject replay across restart? |
| S020 | Does the durable ledger recover around a `SIGKILL` at transaction boundaries? |
| S021 | Can the authenticated client operate a separately implemented adapter code path? |
| S022 | Does a lunar-GSO analogue survive a first physics screen, and how do relay shells trade coverage for range? |
| S023 | What lunar demand can a separate ground network keep off the deep-space pool, and where do optical ISLs stop helping? |
| S024 | How do time-sampled lunar relay candidates trade site contact, capacity and one-node failure? |
| S025 | Which RF/optical architecture classes close on paper, and how sensitive are they to pointing, loss, weather and fallback? |
| S026 | How do surface, orbital and hybrid lunar compute classes trade power, heat rejection, radiation, mass and storage? |
| S027 | What do declared utilisation and availability do to cost per delivered and retained bit? |
| S028 | Do lunar identity, consistency, updates, black start and storage recovery fail safely in executable software? |
| S029 | Do DNS/IPv6, TLS 1.3, HTTP/2, HTTP/3, SMTP and file transfer complete under two independent impairment methods? |
| S030 | Can two independent BPv7 implementations preserve exact payloads through authenticated GatewayCX truncation/retry and ledger recovery? |

The current declared inputs produce:

| Study | User path | Modelled elapsed time | Completed cislunar data | Result |
|---|---|---:|---:|---|
| S001 | Direct Earth service | 16.05 s | 5.25 MB | Completed |
| S002 | Lunar edge-assisted | 5.26 s | 50 kB | Completed |
| S003 | Partitioned lunar region | 0.009 s local work | 0 B | Local completion; 10 MB queued |

Those figures compare architecture assumptions. They do not predict a particular website, terminal
or network.

<p align="center">
  <img src="figures/baseline-latency.svg" alt="GatewayCX baseline elapsed-time comparison" width="100%">
</p>

<p align="center">
  <img src="figures/s016-bearer-window.svg" alt="S016 optical and RF profile capacity comparison" width="49%">
  <img src="figures/s017-durable-restart.svg" alt="S017 traffic-ledger state across process restart" width="49%">
</p>

<p align="center">
  <img src="figures/s019-authenticated-binding.svg" alt="S019 authenticated request and durable replay-state boundary" width="100%">
</p>

<p align="center">
  <img src="figures/s020-transaction-recovery.svg" alt="S020 SQLite transaction recovery before and after commit" width="100%">
</p>

<p align="center">
  <img src="figures/s021-independent-adapter.svg" alt="S021 GatewayCX client and standalone adapter interoperability boundary" width="100%">
</p>

<p align="center">
  <img src="figures/s022-lunar-orbit-envelope.svg" alt="S022 lunar relay shell coverage and Moon-synchronous Hill-radius screen" width="100%">
</p>

<p align="center"><img src="figures/s023-ground-offload.svg" alt="S023 shared versus separated ground pools and optical relay pipeline" width="100%"></p>

<p align="center"><img src="figures/s024-s027-simulation-ceiling.svg" alt="S024 to S027 ephemeris, link, data-centre and economics simulation summary" width="100%"></p>

<p align="center"><img src="figures/s028-regional-fault-lab.svg" alt="S028 executable lunar regional identity, consistency, update, black-start and recovery fault laboratory" width="100%"></p>

<p align="center"><sub>All three charts are generated from committed model or test results. They
are not terminal measurements or flight evidence.</sub></p>

The generated record is [`results/baseline.json`](results/baseline.json). Its checks are tested in
CI. It is not a network simulator, a link-budget tool or evidence of hardware performance yet.

S004 adds the first socket measurement with an unmodified client. Its
[`method and limitations`](studies/S004_NATIVE_HTTPS.md) are deliberately separate from the
deterministic model.

## Engineering record

- [`ORIGIN.md`](ORIGIN.md) separates the April 2026 origin from the public record.
- [`VISION.md`](VISION.md) defines the end state.
- [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md) turns the idea into verifiable requirements.
- [`docs/architecture/SYSTEM_ARCHITECTURE.md`](docs/architecture/SYSTEM_ARCHITECTURE.md) defines the
  initial system boundary and planes.
- [`docs/architecture/INTEROPERABILITY_LAYERING.md`](docs/architecture/INTEROPERABILITY_LAYERING.md)
  fixes the LNIS/DTN boundary and the claim grammar for GatewayCX additions.
- [`docs/CLAIM_LEDGER.md`](docs/CLAIM_LEDGER.md) labels every material claim by evidence class.
- [`docs/PROVENANCE.md`](docs/PROVENANCE.md) says what the present results are and are not.
- [`research/STANDARDS_BASELINE.md`](research/STANDARDS_BASELINE.md) records which public
  standards are inherited, profiled or still untested.
- [`docs/architecture/BEARER_CONTRACT.md`](docs/architecture/BEARER_CONTRACT.md) defines the first
  machine-readable GX-B1 hardware/service seam.
- [`docs/architecture/ADAPTER_RUNTIME.md`](docs/architecture/ADAPTER_RUNTIME.md) defines the GX-A1
  executable runtime seam beneath the service plane.
- [`docs/architecture/DURABLE_TRAFFIC_LEDGER.md`](docs/architecture/DURABLE_TRAFFIC_LEDGER.md)
  defines the payload-blind persistent queue and byte-ledger invariants.
- [`docs/architecture/ADAPTER_PROCESS_BINDING.md`](docs/architecture/ADAPTER_PROCESS_BINDING.md)
  defines the local GX-A1 JSONL process boundary and its unfinished security requirements.
- [`docs/architecture/AUTHENTICATED_ADAPTER_BINDING.md`](docs/architecture/AUTHENTICATED_ADAPTER_BINDING.md)
  defines the S019 pre-shared-key integrity and durable replay-rejection boundary.
- [`adapters/README.md`](adapters/README.md) defines why the S021 standalone adapter is a separate
  code path without presenting it as supplier validation.
- [`docs/architecture/RELAY_ORBIT_ENVELOPE.md`](docs/architecture/RELAY_ORBIT_ENVELOPE.md) rejects
  a simple lunar-GSO layer and defines the geometry questions that precede constellation choice.
- [`docs/FIGURE_INDEX.md`](docs/FIGURE_INDEX.md) maps generated visuals back to their sources and
  evidence limits.
- [`docs/architecture/OPERATIONS_DIAGNOSTICS.md`](docs/architecture/OPERATIONS_DIAGNOSTICS.md)
  defines the GX-O1 portable fault-code and network flight-recorder seam.
- [`research/TRAFFIC_AND_DSN_BOUNDARY.md`](research/TRAFFIC_AND_DSN_BOUNDARY.md) separates a lunar
  regional Internet from the already oversubscribed deep-space antenna network.
- [`docs/INNOVATION_METHOD.md`](docs/INNOVATION_METHOD.md) turns cross-industry inspiration into
  falsifiable mechanism transfers rather than loose analogy.
- [`OPEN_PROBLEMS.md`](OPEN_PROBLEMS.md) keeps unresolved engineering visible.
- [`ROADMAP.md`](ROADMAP.md) gives the build order and exit criteria.

## Vendor position

GatewayCX specifies capabilities and interfaces, not a preferred terminal manufacturer. An
optical terminal from Astrogate or another supplier may satisfy a bearer profile; an RF provider
may satisfy another. No vendor is a dependency, partner or endorsed supplier unless a later public
record says so explicitly.

## Licence

GatewayCX is proprietary intellectual property of Avisys Services and is published under the
[GatewayCX Proprietary Licence](LICENSE). All rights are reserved. Public visibility is not
permission to copy, implement, modify, deploy, redistribute or commercialise the code, protocols,
models, specifications, documentation or figures.

Earlier repository versions were published under Apache License 2.0. Rights already granted for
those earlier versions cannot be retroactively revoked; the proprietary licence applies from the
commit that introduces it onward. See [`NOTICE`](NOTICE) and [`CONTRIBUTING.md`](CONTRIBUTING.md).
