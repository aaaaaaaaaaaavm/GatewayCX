# Claim ledger

## Evidence classes

- **STANDARD:** normative public specification
- **PUBLIC FACT:** traceable public source
- **DERIVATION:** equation and stated inputs
- **MODEL:** output of committed software
- **ASSUMPTION:** chosen input without confirming evidence
- **MEASUREMENT:** instrumented observation
- **PARTNER DATA REQUIRED:** cannot close from public information
- **DECISION:** project architecture choice

## Current claims

| ID | Claim | Class | Evidence | Status |
|---|---|---|---|---|
| C001 | Ideal one-way propagation at 384,400 km is 1.2822 s. | DERIVATION | `distance / c` in `gatewaycx/model.py` | Reproduced in CI |
| C002 | Ideal round-trip propagation at that distance is 2.5644 s before relay processing. | DERIVATION | `2 × distance / c` | Reproduced in CI |
| C003 | Increasing link capacity does not reduce geometric propagation delay. | DERIVATION | Propagation and serialization are separate model terms. | Supported analytically |
| C004 | Direct Earth-hosted transactions accumulate delay with sequential cross-region dependencies. | MODEL | S001 baseline | Model only |
| C005 | Local service placement can remove avoidable cislunar RTTs and backbone bytes. | MODEL | S001 versus S002 | Model only |
| C006 | Lunar-local services can complete while the backbone is unavailable. | MODEL | S003 | Architecture/model only |
| C007 | Every existing Internet application will work well unchanged from the Moon. | — | No evidence; deliberately not claimed | Rejected |
| C008 | BPv7 is suitable for all GatewayCX traffic. | — | P02 remains open | Not claimed |
| C009 | A named commercial terminal satisfies a GatewayCX cislunar bearer profile. | PARTNER DATA REQUIRED | No profile-qualified data yet | Open |
| C010 | GatewayCX has been deployed or hardware-validated. | — | No hardware exists in this record | Rejected |
| C011 | LLCD demonstrated lunar-orbit optical downlinks up to 622 Mbps and uplinks up to 20 Mbps. | PUBLIC FACT | NASA LLCD project page | Public demonstration; not a GatewayCX measurement |
| C012 | Optical communications and DTN have been exercised together over the LLCD lunar optical trunk. | PUBLIC FACT | NASA LLCD/DTN experiment record | Public demonstration; topology partly virtual |
| C013 | The current CCSDS BPv7 publication is experimental 734.20-O-1; 734.2-B-1 is RFC 5050/BPv6-based. | STANDARD | CCSDS active-publications catalogue | Source reviewed |
| C014 | LNIS V5 is the current NASA/ESA/JAXA lunar interoperability specification baseline. | PUBLIC FACT | NASA LNIS page and V5 document | Source reviewed |
| C015 | A performance-enhancing proxy is required for native lunar Internet service. | — | No comparative measurement | Rejected as a general requirement |
| C016 | An unmodified curl client can complete verified TLS 1.3 and HTTP/1.1 through the mean-distance delayed-byte harness. | MEASUREMENT | S004 | Socket-level only; TCP setup not delayed |
| C017 | Reusing the S004 HTTPS connection avoids a second TLS handshake. | MEASUREMENT | S004 `num_connects` and `time_appconnect` | Reproduced by CI at reduced delay |
| C018 | A 622 Mbps flow at mean lunar RTT has a bandwidth-delay product of about 199.38 MB. | DERIVATION | S006 | Reproduced in CI |
| C019 | Continuing to admit 100 Mbps for a one-day outage requires 1.08 TB before overhead and margin. | DERIVATION | S006 | Reproduced in CI |
| C020 | Under the S007 assumptions, 19 of 243 placements are both resource-feasible and partition-resilient. | MODEL | S007 | Reproduced in CI; not a demand forecast |
| C021 | A lunar replica always reduces cislunar backbone traffic. | — | S007 provides a counterexample when update traffic exceeds avoided user traffic | Rejected |
| C022 | Service placement can trade replication bytes for lower interaction delay and partition survival. | MODEL | S007 Pareto frontier | Model only |
| C023 | One machine-readable capability shape can describe the minimum GatewayCX fields for illustrative optical and RF bearers. | TEST | S008 reference profiles | Interface-shape test only |
| C024 | A commercial bearer has passed GX-B1 qualification. | — | No provider profile or conformance report | Rejected |
| C025 | Under the S009 RF-fallback inputs, strict priority delivers zero GX-T4 and GX-T5 bytes. | MODEL | S009 | Reproduced in CI; synthetic traffic |
| C026 | Under the same inputs, bounded priority fully serves GX-T0/GX-T1 and preserves GX-T4/GX-T5 progress. | MODEL | S009 | Reproduced in CI; shares not safety-approved |
| C027 | GatewayCX eliminates DSN scheduling contention. | — | No DSN integration or operational study | Rejected |
| C028 | Under S010 assumptions, warm RF standby reduces maximum interactive interruption from 20 seconds to 0.5 seconds. | MODEL | S010 | Reproduced in CI; no transport session model |
| C029 | RF and optical bearers are operationally independent. | ASSUMPTION | S010 omits common power, platform and ground failures | Open |
| C030 | Make-before-break reachability automatically preserves every application session. | — | Transport and application semantics differ | Rejected |
| C031 | Under S011 inputs, content addressing reduces wire bytes from 1.03 GB with monolithic resume to 430 MB. | MODEL | S011 | Reproduced in CI; synthetic layers |
| C032 | Under the S011 state machine, interruption before activation leaves slot A/v1 active. | MODEL | S011 | State model only |
| C033 | A/B activation makes shared database migrations rollback-safe. | — | Shared mutable state is outside the slot model | Rejected |
| C034 | S011 implements Uptane, OCI Distribution or secure boot. | — | It models selected semantics only | Rejected |
| C035 | Under S012 inputs, calibrated and popularity policies both prefetch 850 MB of useful content and avoid 27 remote requests. | MODEL | S012 | Reproduced in CI; one synthetic trace |
| C036 | Under S012 inputs, the overconfident forecast wastes 450 MB and avoids seven fewer remote requests than popularity. | MODEL | S012 | Reproduced in CI; outcome constructed for mechanism testing |
| C037 | S012 establishes that a learned predictor outperforms the simple baseline. | — | Useful bytes and avoided requests are tied | Rejected |
| C038 | A predictor may evict essential content when its confidence is high. | — | Essential reservation is outside predictor authority | Rejected |
| C039 | Under the S013 graph, Earth-coupled dependencies allow only two of seven essential services to start during partition. | MODEL | S013 | Reproduced in CI; assumed graph |
| C040 | Under the S013 islandable graph, all seven essential services start without Earth. | MODEL | S013 | Logical reachability only |
| C041 | Under S013 single faults, loss of holdover time has the largest dependency impact. | MODEL | S013 | No oscillator or holdover-error model |
| C042 | S013 demonstrates electrical, hardware or secure-boot black-start capability. | — | It models logical service dependencies only | Rejected |
| C043 | Under S005 inputs, native HTTPS retry sends 14 MB while the durable object modes send 10 MB. | MODEL | S005 | Reproduced in CI; persistent chunk ledger assumed |
| C044 | BPv7 delivery status means delivery to the destination Application Agent, not proof that the application processed the payload. | STANDARD | RFC 9171 §5.7 | Source reviewed |
| C045 | BPv7 retains BPv6-style native custody transfer. | — | RFC 9171 moves custody transfer outside the base protocol | Rejected |
| C046 | A terminating deferred proxy preserves the original end-to-end TLS boundary. | — | TLS terminates at the proxy | Rejected |
| C047 | Idempotency and deduplication prove exactly-once execution. | — | Duplicate effects can be suppressed without proving exactly-once delivery or execution | Rejected |
| C048 | An arbitrary synchronous HTTPS session survives an indefinite cislunar partition transparently. | — | Application-visible semantics must change or the session fails | Rejected |
| C049 | The S014 reference trace passes the GX-O1 v0.1 semantic validator. | TEST | S014 | Reproduced in CI; one generated trace |
| C050 | At S014 contact loss, the portable freeze frame records 6 MB queued, zero transmit rate and no payload/user content. | MODEL + TEST | S005 offsets + GX-O1 validator | Synthetic trace only |
| C051 | A portable GX-O1 fault code proves a hardware root cause. | — | Portable codes classify traffic consequences, not internal physics | Rejected |
| C052 | GX-O1 replaces provider-specific diagnostic telemetry. | — | Provider extensions remain necessary | Rejected |
| C053 | S015 reproduces S010 warm-standby control rejection, interactive rejection and RF keepalive bytes on its shared timeline. | MODEL + TEST | S015 composition checks | Reproduced in CI; same synthetic assumptions |
| C054 | Under S015 inputs, optical carries 837.031 MB and RF carries 162.969 MB of one accepted 1 GB durable object. | MODEL | S015 | Byte-budget replay only |
| C055 | Under S015 inputs, the object reaches the adapter at 139.782 s and remote application completion at 139.802 s. | MODEL | S015 | Mean propagation plus declared processing interval |
| C056 | S015 demonstrates an operational BPv7 gateway or RF/optical handover. | — | No protocol or hardware executes | Rejected |
| C057 | The same GX-A1 response-field signatures are exercised for both GX-B1 reference media profiles. | TEST | S016 | One shared Python implementation only |
| C058 | Under S016 profile inputs, a 100 ms window moves 6.25 MB through optical and 1.25 MB through RF. | MODEL + TEST | S016 | Profile-driven byte budgets, not measurements |
| C059 | The S016 reference adapter preserves 1,745,392 optical-queue bytes and 6,745,392 RF-queue bytes across its injected fault. | MODEL + TEST | S016 | In-process state only; not crash durability |
| C060 | S016 demonstrates independent vendor or hardware interoperability. | — | Both instances share one implementation and no hardware | Rejected |
| C061 | S017 preserves 7,995,392 accepted bytes, 1,250,000 transmitted bytes and 6,745,392 queued bytes across a clean process restart. | TEST | S017 | Local SQLite/software test only |
| C062 | S017 rejects a changed-size reuse of an accepted traffic-unit ID without changing the ledger. | TEST | S017 | One SQLite implementation |
| C063 | The S017 traffic-unit schema has no payload-content column. | TEST | S017 schema inspection | Identifiers, sizes and classes remain metadata |
| C064 | S017 proves survival through power loss or qualifies storage for flight. | — | No abrupt-loss or hardware test | Rejected |
| C065 | S018 drives GX-A1 capability, queue, acquisition and transmission operations through a separate server process. | TEST | S018 | GatewayCX reference implementation on both sides |
| C066 | The S018 server rejects malformed JSON and remains available for a subsequent operation. | TEST | S018 | Local loopback test only |
| C067 | Restricting the reference binding to loopback authenticates or authorises its client. | — | Reachability is not identity or policy | Rejected |
| C068 | S018 demonstrates independent supplier or terminal interoperability. | — | No external adapter or hardware participates | Rejected |
| C069 | S019 accepts a correctly authenticated request and rejects modification or an incorrect pre-shared key. | TEST | S019 | Local HMAC reference mechanism only |
| C070 | S019 rejects the same valid sequence before and after a clean server restart. | TEST | S019 | SQLite single-node replay state |
| C071 | The S019 replay table contains the client identifier and last sequence but no secret column. | TEST | S019 schema inspection | Secret still exists in a process-readable key file |
| C072 | S019 provides confidentiality, PKI, key lifecycle or flight-qualified security. | — | None of these mechanisms is implemented | Rejected |
| C073 | S019 demonstrates independent supplier or terminal interoperability. | — | Both endpoints are GatewayCX reference software | Rejected |
| C074 | S020 rolls back an uncommitted traffic unit and preserves an earlier committed unit after `SIGKILL`. | TEST | S020 | Coordinated pre-commit fault point on local SQLite |
| C075 | S020 preserves a committed traffic unit when the writer is killed before closing and subsequently accepts new work. | TEST | S020 | Coordinated post-commit fault point on local SQLite |
| C076 | S020 qualifies storage for electrical power loss or flight. | — | No power, device-cache, filesystem-corruption or flight-hardware test | Rejected |
| C077 | S021 drives GX-A1 operations through an authenticated server implementation that imports no GatewayCX runtime module. | TEST | S021 source inspection and process probe | Separate code path in the same repository |
| C078 | S021 preserves accepted and transmitted byte state across a restart of the standalone adapter. | TEST | S021 | Local standalone SQLite implementation |
| C079 | S021 proves external supplier, multi-organisation or hardware interoperability. | — | Both implementations are authored in this project and no hardware participates | Rejected |
| C080 | Under the S022 inputs, the two-body Moon-synchronous radius is about 88,452 km from lunar centre, versus an approximate Hill radius of 61,524 km. | DERIVATION | S022 | First-order screen, not propagated stability analysis |
| C081 | A roughly 24-hour circular lunar orbit is stationary over the lunar surface. | — | The Moon's sidereal rotation is about 27.32 days | Rejected |
| C082 | Under S022 zero-elevation equatorial geometry, the ideal minimum falls from ten satellites at 100 km to three at 5,000–8,000 km. | DERIVATION | S022 | Not global coverage or a constellation design |
| C083 | S022 selects the production lunar relay orbit. | — | No multi-body propagation, sites, link budgets, failures or capacity | Rejected |
| C084 | In S023, separating 60 synthetic lunar units clears both constructed pools. | MODEL | S023 | Not real DSN demand or capacity |
| C085 | Optical inter-satellite links alone deliver lunar data to Earth. | — | Earth trunk and ground gateway remain required | Rejected |
| C086 | A lunar relay automatically offloads Voyager, JWST or Parker Solar Probe traffic. | — | Those missions require compatible end-to-end services | Rejected |
| C087 | GatewayCX defines a replacement for LunaNet or BPv7. | — | LNIS V5 and RFC 9171 are inherited baselines | Rejected |
| C088 | LNIS V5 permits IPv4, IPv6 and BPv7 at LNSP-user network-layer interfaces, including over bilaterally defined non-LNIS links. | STANDARD | LNIS V5 §4.5 Table 12 | Source reviewed |
| C089 | NASA reports that DTN became operational in the Near Space Network and Deep Space Network after its DTN Project completed in January 2026. | PUBLIC FACT | NASA SCaN DTN page | Source reviewed 2026-08-28; not a GatewayCX result |
| C090 | A GatewayCX profile test establishes LunaNet compliance. | — | LNIS defines compliance at its own service/interface level and applicable documents | Rejected |
| C091 | S024 is an operational lunar ephemeris or production constellation design. | — | It uses circular two-body propagation and synthetic capacities | Rejected |
| C092 | Under S024 inputs, the medium 8-node class maintains a routed path for all three sampled sites through the named single-node fault. | SIMULATION | S024 | 48-hour, 600-second sample; simplified geometry and link graph |
| C093 | S025 shows the declared DWE Ka class loses its positive paper margin under 6 dB additional loss. | DERIVATION | S025 | Architecture inputs; no terminal or field measurement |
| C094 | A positive S025 optical or RF margin proves service availability. | — | Acquisition, weather, interference and hardware are not closed | Rejected |
| C095 | S026 sizes a flight-ready lunar data centre. | — | Comparative class model omits major subsystems and qualification | Rejected |
| C096 | S027 establishes a viable market or customer price. | — | Cost and utilisation inputs are synthetic | Rejected |
| C097 | S028 accepts a valid offline identity during a partition, bounds it by expiry, and rejects it after revocation becomes visible. | TEST | S028 X07 | HMAC reference key; not federated identity or protected key custody |
| C098 | S028 resolves every database workload with one consistency policy. | — | X08 deliberately assigns fail-closed, convergent and escrow semantics by class | Rejected |
| C099 | S028 rejects a corrupt update payload and rolls back an interrupted SQLite schema migration while slot A stays active. | TEST | S028 X14 | No secure boot, registry or real application deployment |
| C100 | S028 performs electrical lunar black start. | — | X16 launches local child processes only | Rejected |
| C101 | S028 restores exactly 23 committed rows after 60 seeded transaction cases and deliberate SQLite header corruption. | TEST | S028 X18 | Local file/backup test, not raw-device or power-loss qualification |
| C102 | S029 passes two independent impairment methods and a loopback packet-capture gate for DNS/IPv6, TLS 1.3, HTTP/2, HTTP/3, SMTP and file transfer. | MEASUREMENT | GitHub run 33220236500 and artifact 9704881339 | 25 ms one-way configuration; standards-library clients and minimal SMTP |
| C103 | The existence of the S029 harness proves native lunar Internet performance. | — | Short-delay loopback tests do not establish lunar-delay usability | Rejected |

The ledger will grow when the evidence grows. A claim does not become stronger by appearing in the
README.
