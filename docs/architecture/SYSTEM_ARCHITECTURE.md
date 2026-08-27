# System architecture

## System boundary

GatewayCX begins at a terrestrial or lunar user's network interface and ends at the destination
service. That boundary deliberately crosses hardware, networking, compute and operations. Solving
only the relay leaves the application paying every avoidable round trip. Solving only the cloud
leaves no path between regions.

The initial system has six logical roles:

1. **Earth regional gateway** connects terrestrial networks and service providers to the cislunar
   interconnect.
2. **Cislunar bearer network** supplies optical, RF or hybrid capacity without owning application
   semantics.
3. **Lunar regional gateway** terminates regional routing policy and exposes disruption state.
4. **Lunar access network** connects habitats, vehicles, landers, instruments and people.
5. **Lunar compute region** hosts caches, names, identities, storage, replicas and applications.
6. **Federation plane** coordinates trust, routes, capacity, incidents and accounting among
   operators.

These are roles, not necessarily six boxes. One early mission gateway may implement several. A
settlement-scale network should be able to separate them.

## Planes

### Native Internet plane

Carries ordinary IP traffic across a continuous path. It includes addressing, routing, DNS, TLS,
HTTP and the rest of the terrestrial compatibility surface. High latency is visible but the client
does not learn a spacecraft protocol.

### Resilience plane

Handles predicted contacts, interruption, queues, resumable transfer and deferred delivery. BPv7
is the starting candidate, not an unquestioned answer. The boundary between IP and DTN must state
what happens to sessions, encryption, acknowledgements and custody.

### Regional service plane

Keeps latency-sensitive or essential work in the lunar region. It includes local DNS and identity
validation, CDN and package mirrors, object storage, application replicas, edge processing and
eventual synchronisation with Earth.

### Bearer plane

Exposes capacity, delay, availability and error characteristics from optical and RF systems. A
bearer adapter may control terminals and contacts, but applications consume a service class rather
than a manufacturer's API.

### Operations and federation plane

Observes the system and coordinates multiple providers. OSS/BSS, service assurance, incident
management, capacity reservation, settlement and policy live here. They make the network operable
and commercial; they do not define the user's Internet protocol.

[`GX-O1`](OPERATIONS_DIAGNOSTICS.md) defines the first provider-neutral diagnostic seam: portable
fault classes, correlated state transitions and a minimum freeze frame without application
plaintext.

## Operating modes

| Mode | Backbone state | Expected behaviour |
|---|---|---|
| Continuous | Stable end-to-end path | Native IPv6 and ordinary transport operate with cislunar RTT. |
| Degraded | Reduced or intermittent bearer | Priority policy, resumable transfer and selective deferral apply. |
| Partitioned | No Earth–Moon path | Lunar-local services continue; accepted deferred traffic queues. |
| Recovery | Path returns | Queues drain by policy; replicas reconcile; conflicts remain visible. |

## Trust boundaries

- Bearer providers can observe link metadata but should not require application plaintext.
- A terminating cache or proxy is part of the service provider's trust boundary and must be
  explicit. GatewayCX does not treat covert TLS interception as an optimisation.
- Regional identity validation must account for stale revocation information during a partition.
- Operations telemetry must separate service observability from user-content access.

[`S013`](../../studies/S013_LUNAR_BLACK_START.md) applies a microgrid-style islanding and black-start
test to the logical dependencies of the lunar region. A locally hosted service is not independent
if its time, trust, naming or route-control start path still requires Earth.

## Architecture invariants

1. Same-region traffic stays in-region unless policy explicitly exports it.
2. A vendor failure cannot change the application protocol.
3. Accepted deferred traffic has a visible state until delivery or explicit expiry.
4. Priority does not mean undocumented starvation.
5. A precise model output is still a model output.
