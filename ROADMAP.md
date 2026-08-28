# Roadmap

The roadmap is gated by evidence, not file count. A phase closes when its exit criteria are met.

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
- Move GX-A1 from its in-process reference class to an authenticated process boundary.

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
