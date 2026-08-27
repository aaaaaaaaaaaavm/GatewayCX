# System requirements

Requirements use **shall** only where a verification method is named. Values marked TBD are open
engineering inputs, not permission to choose a convenient number inside a model.

## Native compatibility

| ID | Requirement | Verification |
|---|---|---|
| GX-NAT-001 | An unmodified standards-based client in the lunar region shall resolve a terrestrial domain and complete an encrypted HTTPS transaction while a continuous path is available. | Packet-level emulation and application log |
| GX-NAT-002 | A terrestrial client shall access a lunar-hosted service through the same standards profile. | Bidirectional emulation |
| GX-NAT-003 | The architecture shall preserve end-to-end application encryption unless the service owner explicitly selects a terminating proxy. | Packet capture and trust-boundary inspection |
| GX-NAT-004 | Existing applications shall not require a mission-specific API merely to obtain continuous-path Internet connectivity. | Client inventory and clean-device test |

## Regional autonomy

| ID | Requirement | Verification |
|---|---|---|
| GX-REG-001 | Traffic whose source and destination are in the lunar region shall not require a cislunar hop. | Route and packet inspection |
| GX-REG-002 | Essential naming, identity validation, messaging and habitat information services shall operate through a defined backbone-outage window, `T_partition` (TBD). | Fault-injection test |
| GX-REG-003 | Deferred writes shall expose their pending state and reconcile according to an application-specific policy after recovery. | Partition/recovery test |
| GX-REG-004 | The system shall distinguish local completion, remote completion, queued delivery and failure to the service layer. | API conformance test |

## Cislunar interconnect

| ID | Requirement | Verification |
|---|---|---|
| GX-INT-001 | The interconnect shall operate across optical, RF or hybrid bearers through a capability interface independent of manufacturer. | Two-adapter interoperability test |
| GX-INT-002 | The interconnect shall expose current capacity, predicted availability, delay, queue state and error state. | Telemetry conformance test |
| GX-INT-003 | Traffic policy shall distinguish life-safety, command/control, interactive, operational, science and background classes. | Policy and starvation test |
| GX-INT-004 | Failure of the preferred bearer shall not silently discard traffic accepted for deferred delivery. | Bearer-loss fault injection |
| GX-INT-005 | Continuous IP and deferred delivery modes shall have explicit transition semantics. | State-transition test |

## Core Internet services

| ID | Requirement | Verification |
|---|---|---|
| GX-COR-001 | Earth and lunar regions shall share interoperable naming and service-discovery semantics. | Cross-region resolution tests |
| GX-COR-002 | Identity and certificate validation shall have a documented partition policy, including revocation limitations. | Security review and outage test |
| GX-COR-003 | Time-dependent security mechanisms shall define holdover and recovery behaviour when the Earth time source is absent. | Clock fault injection |
| GX-COR-004 | Addressing and routing policy shall permit regional aggregation and multi-operator interconnection. | Route-policy analysis |

## Operations and governance

| ID | Requirement | Verification |
|---|---|---|
| GX-OPS-001 | Every accepted traffic unit shall be traceable across regional and bearer boundaries without exposing application plaintext. | Distributed trace test |
| GX-OPS-002 | Capacity reservation, accounting and service-level data shall use open interfaces. | Schema and implementation conformance |
| GX-OPS-003 | No conformance requirement shall name one commercial vendor as its only implementation. | Specification review |
| GX-OPS-004 | Safety-priority policy shall prevent unbounded starvation of lower classes outside declared emergencies. | Load and policy test |

## Evidence requirements

| ID | Requirement | Verification |
|---|---|---|
| GX-EVD-001 | Every numerical output shall identify its input, model version and evidence class. | CI audit |
| GX-EVD-002 | Generated results shall be reproducible from committed source and inputs. | Clean-checkout CI run |
| GX-EVD-003 | Model output shall not be labelled measurement, qualification or flight performance. | Claim-ledger review |

