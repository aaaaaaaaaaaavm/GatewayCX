# S014: GX-O1 network flight recorder

## Concept transfer

Automotive OBD does not require every manufacturer to expose the same internal controller. It
defines stable diagnostic classes that a tool can recognise. A flight recorder preserves the
state around an event rather than hoping the failure repeats on demand. Motorsport telemetry then
adds correlation across subsystems without pretending that one channel explains the entire car.

GatewayCX transfers those mechanisms into a provider-neutral network diagnostic profile. Optical,
RF, gateway and application implementations may retain their own detailed logs, but the federation
needs a small shared event vocabulary and a freeze frame at each boundary transition.

## Question

Can the S005 interruption and recovery sequence be reconstructed across lunar ingress, bearer and
Earth application boundaries without application plaintext or vendor-private telemetry?

## Profile

GX-O1 v0.1 requires every event to carry:

- a portable fault or state code;
- a trace and event identity;
- a monotonic replay offset;
- source node, region and component;
- previous and current state;
- a minimum bearer/queue freeze frame; and
- explicit confirmation that payload plaintext and user identity are absent.

The initial registry covers durable acceptance, bearer loss, fallback activation, preferred-path
restoration, adapter delivery, remote completion, expiry, storage depletion and invalid receipts.
It is deliberately smaller than a real provider fault catalogue.

## Method

The generated trace replays the S005 opaque-object case. Five events cross three component
boundaries:

1. the lunar ingress durably accepts the 10 MB object;
2. the bearer fails after 4 MB has crossed;
3. the bearer returns after the 120-second partition;
4. the Earth adapter receives the object; and
5. the Earth application records a processing receipt.

```bash
python -m gatewaycx.diagnostics
python -m gatewaycx.diagnostics --validate results/S014_diagnostic_trace.json
```

## Result

The reference trace passes the GX-O1 semantic validator. At contact loss it records:

| Freeze-frame field | Value |
|---|---:|
| Link state | unavailable |
| Transmit rate | 0 Mbps |
| Durable queue | 6 MB |
| Missing object bytes | 6 MB |

The validator rejects unknown portable codes, duplicate event identifiers, non-monotonic offsets,
missing freeze-frame fields, plaintext/user-identity flags, and a delivery trace that skips from
local acceptance directly to remote completion.

## Architecture consequence

GX-O1 separates portable diagnosis from proprietary implementation detail. A hardware partner can
map its acquisition, pointing, weather or amplifier faults into the shared contact-loss class while
retaining a provider extension for root-cause analysis. The common layer tells GatewayCX what
happened to traffic; it does not tell a terminal manufacturer how to build or debug a terminal.

The trace also gives S005 an observable contract. An operator can now distinguish:

- traffic still safe in the lunar queue;
- traffic delivered only as far as the Earth adapter; and
- work actually acknowledged by the remote application.

## Boundary

Every event is generated from synthetic S005 offsets. No telemetry was observed and no hardware
fault was diagnosed. The initial registry is not a standard, safety case or provider qualification.
It omits clock synchronisation error, log authentication, retention limits, sampling pressure,
provider extensions and multi-node trace collection.
