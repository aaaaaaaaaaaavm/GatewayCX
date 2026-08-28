# Operations diagnostics

## GX-O1 boundary

GX-O1 is the minimum portable evidence surface between GatewayCX providers. It is not a demand for
identical internal telemetry.

| Layer | Shared GX-O1 record | Provider-owned extension |
|---|---|---|
| Bearer | Availability transition, capacity, queue and contact fault class | Pointing loop, modem, amplifier, weather and terminal detail |
| Gateway | Accepted state, missing bytes, expiry and storage fault class | Database, process and storage-engine diagnostics |
| Delivery | Adapter receipt and application receipt as separate events | Application processing and business-domain detail |
| Security | Invalid receipt or policy failure class | Keys, algorithms, sensitive audit evidence and response workflow |

The portable record must not contain payload plaintext or a direct user identifier. Correlation uses
an opaque trace identity and traffic-unit identity. Access control, retention and log integrity are
still required even when content is excluded.

## Freeze frame

A transition record captures the minimum state needed to reproduce the traffic consequence:

- bearer identity and link state;
- current transmit rate;
- durable queue bytes; and
- bytes still missing for the correlated traffic unit.

This is deliberately analogous to an automotive freeze frame. It preserves the conditions around
the fault; it does not prove the fault's physical root cause.

The executable registry is
[`profiles/diagnostics/gx-o1-fault-codes.json`](../../profiles/diagnostics/gx-o1-fault-codes.json).
The first conforming trace is
[`results/S014_diagnostic_trace.json`](../../results/S014_diagnostic_trace.json).
The first cross-plane trace is embedded in
[`results/S015_integrated_replay.json`](../../results/S015_integrated_replay.json).
