# Roadmap

The roadmap is gated by evidence, not file count. A phase closes when its exit criteria are met.

## Programme boundary

M0–M5 drive GatewayCX to the ceiling of repeatable software, emulation and simulation evidence.
LNIS V5, Internet standards and BPv7 are inherited; GatewayCX implements and tests the service,
regional, bearer, operational and commercial profile around them. M6 remains a deliberate hardware
boundary and is not part of the current build push.

## M0: Foundation record

**Purpose:** make the idea inspectable.

- Origin, scope, requirements, claims and open problems are version controlled.
- A deterministic baseline reproduces the Earth–Moon light-time calculation.
- Direct, edge-assisted and partitioned service scenarios run in CI.
- No simulated result is presented as measured performance.

**Status:** active.

## M1: Native Internet baseline

**Purpose:** determine what the existing Internet does before designing replacements.

- Run unmodified DNS, IPv6, TLS, HTTP/2, HTTP/3, email and file-transfer clients through an
  emulated cislunar path.
- Record handshakes, dependency chains, throughput, timeout behaviour and recovery.
- Separate correctness failures from merely bad user experience.
- Publish packet captures, configurations and repeatable run sheets.

**Exit:** at least two independent emulation methods reproduce the critical observations.

**Current executable gate:** S029 runs the same DNS/IPv6, TLS 1.3, HTTP/2, HTTP/3, SMTP and file
matrix through a userspace TCP/UDP impairment engine and an independently configured Linux netem
qdisc. GitHub run 33221887795 passed both methods at 25 ms and 1,282 ms one-way delay, captured the
four runs into one artifact and uploaded four measurement records. This closes the requested
dual-method fixed-delay packet gate; loss/reordering, ordinary GUI clients and capture review remain
follow-on evidence before M1 exit.

## M2: Resilient cislunar interconnect

**Purpose:** retain native IP where possible and add disruption tolerance where necessary.

- Define continuous, degraded and disconnected operating modes.
- Evaluate BPv7/DTN gateways, contact-plan routing, queues and custody policy.
- Preserve end-to-end security or state explicitly where a gateway terminates it.
- Model optical weather outages and RF fallback.
- Implement the S005 `accepted_pending`, `bp_delivered` and `remote_completed` state contract.
- Integrate the S016 adapter seam and S017 durable ledger into one fault-injected link process.

**Exit:** a reference interconnect survives scheduled and unscheduled link loss without corrupting
or silently dropping committed traffic classes.

**Current executable gate:** S030 fetches pinned `dtn7-go` and `bp7-rs` revisions without vendoring
them and passes both RFC 9171 bundle wire images through the existing GX-A1 adapter, SQLite byte
ledger and S019 HMAC/replay mechanism. Run 33294426808 proves exact `dtn7-go` to `bp7-rs` payload
transfer after an injected truncation and retry. The reciprocal `bp7-rs` image self-decodes but the
pinned `dtn7-go` parser rejects it with `EOF`; that measured incompatibility keeps bidirectional
wire interoperability open. Full daemons, convergence layers, BPSec and contact routing also remain
outside this gate.

## M3: Lunar regional Internet and compute

**Purpose:** make the lunar experience local-first.

- Place DNS, identity, CDN, object storage, databases and application services in a lunar region.
- Compare surface, orbital and hybrid data-centre placement.
- Define replication, consistency, conflict and recovery policies.
- Size power, thermal rejection, storage and backbone demand for settlement scenarios.

**Exit:** essential services remain operational through a defined Earth-link outage and reconcile
within bounded time after recovery.

## M4: Multi-bearer backbone

**Purpose:** make hardware replaceable beneath the service.

- Define optical, RF and hybrid bearer capability profiles.
- Model link acquisition, pointing, weather, handover, capacity and failure.
- Connect at least two independently implemented bearer adapters to the reference service plane.
- Mature the S019 authenticated process boundary into a reviewed confidential transport with key
  lifecycle, role policy and operation-reconciliation semantics.
- Extend the S021 separate code path into a complete conformance target and connect an externally
  implemented adapter through the versioned binding.

**Exit:** a traffic session changes bearer or provider without changing the user application.

## M5: Interoperability profile

**Purpose:** make GatewayCX useful beyond one company.

- Publish stable interface, telemetry, security and conformance profiles.
- Build a conformance test kit and reference gateway.
- Exercise multi-operator routing, identity federation, accounting and incident handling.

**Exit:** an external implementation passes the public conformance suite without private
integration knowledge.

## M6: Cislunar deployment path

**Purpose:** move from architecture to infrastructure.

- Ground and hardware-in-the-loop trials
- Hosted-payload or terrestrial analogue demonstration
- Lunar mission gateway pilot
- Lunar regional ISP and data-centre services
- Federated Earth–Moon production network

Each transition requires an owner, partner data, cost model, safety case and regulatory path.

## M7: Solar System Internet

Generalise the regional architecture for orbital settlements, Mars and deep-space missions.
Earth–Moon is the first deployment problem, not the last boundary.
