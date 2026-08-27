# GatewayCX interoperability profile

- **Document status:** pre-draft 0.1
- **Normative status:** none

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT** and **MAY** are intended in the
sense of BCP 14 when this document becomes normative. At present they identify the shape of the
future profile and are not a conformance claim.

## Roles

- **Regional client:** ordinary user or machine endpoint
- **Regional service:** application, cache, identity, naming or storage endpoint
- **Regional gateway:** policy and routing boundary for an Internet region
- **Bearer adapter:** maps a provider link into common capacity and state interfaces
- **Deferred-delivery agent:** accepts and tracks disruption-tolerant traffic
- **Federation operator:** exchanges routes, trust, policy and accounting information

## Interface set

| Interface | Purpose | Initial compatibility target |
|---|---|---|
| GX-U1 | Client to regional network | IPv6 and ordinary Internet access |
| GX-R1 | Regional interconnection | Routing, policy and service reachability |
| GX-B1 | Gateway to bearer adapter | Capacity, contacts, delay, health and reservation |
| GX-D1 | Service to deferred delivery | Submit, status, expiry, receipt and cancellation |
| GX-S1 | Regional service discovery | Same logical service, region-appropriate instance |
| GX-O1 | Operations telemetry | Traces, queues, faults, utilisation and SLA state |

## Delivery modes

| Mode | Meaning |
|---|---|
| `continuous` | An end-to-end network path exists; native transport owns reliability. |
| `deferred` | The system accepts a bounded object/message for later delivery and returns durable status. |
| `local-only` | The operation must remain inside the current region. |

A gateway must not report `continuous` success for traffic it has silently converted to deferred
delivery. A deferred acceptance is not destination delivery.

## Traffic classes

| Class | Intent |
|---|---|
| GX-T0 | Declared life-safety and emergency traffic |
| GX-T1 | Command, control and navigation |
| GX-T2 | Crew-interactive communications |
| GX-T3 | Mission and settlement operations |
| GX-T4 | Science and commercial bulk transfer |
| GX-T5 | Background replication, prefetch and archival |

The class names do not yet define admission, pre-emption or bandwidth shares. Those policies must
come from hazard and starvation analysis rather than intuition.

## Minimum bearer description

A GX-B1 adapter will eventually report at least:

- bearer identifier and provider;
- optical, RF or hybrid type;
- endpoints and direction;
- usable capacity and current allocation;
- propagation and processing-delay estimate;
- current and predicted availability window;
- acquisition or handover state;
- maximum accepted traffic unit;
- error and loss indicators; and
- source and freshness of every reported value.

No performance tier is defined until link-budget and operator evidence support one.

The first machine-readable pre-draft of this description is the
[`GX-B1 bearer capability contract`](../docs/architecture/BEARER_CONTRACT.md). Its reference
profiles test fields and semantics only; they are not terminal specifications.
