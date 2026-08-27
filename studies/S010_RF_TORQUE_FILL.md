# S010: RF continuity around optical handover

## Concept transfer

A hybrid powertrain can use a second torque source to cover a transition instead of allowing a
hole in delivered wheel torque. Multipath networking already expresses the less metaphorical form:
validate another path before the first disappears and preserve the connection across subflows.

GatewayCX transfers that mechanism, not the drivetrain. The optical bearer is the high-capacity
path; RF is a lower-capacity continuity path kept cold, warm or permanently assigned selected
traffic.

## Question

How much interactive interruption and rejected traffic disappear when RF is ready before a
synthetic optical outage?

## Method

S010 replays 180 seconds in 0.5-second steps. A 500 Mbps optical path fails at 60 seconds, returns
at 120 seconds and takes 15 seconds to reacquire. A 20 Mbps RF path takes 20 seconds to acquire cold
or 0.5 seconds to switch when warm. Offered traffic is 0.5 Mbps control, 2 Mbps interactive and 100
Mbps deferred bulk.

Three policies run against the identical event trace:

- **cold failover:** acquire RF after optical fails;
- **warm standby:** maintain a 0.1 Mbps RF keepalive and switch after 0.5 seconds; and
- **split continuity:** keep control and interactive traffic on RF while optical carries bulk.

```bash
python -m gatewaycx.handover
```

## Result

| Policy | Longest interactive interruption | Rejected interactive bytes | Peak bulk queue | Explicit continuity cost |
|---|---:|---:|---:|---:|
| Cold failover | 20.0 s | 5.000 MB | 817.188 MB | 0 |
| Warm standby | 0.5 s | 0.125 MB | 774.531 MB | 1.313 MB keepalive |
| Split continuity | 0 s | 0 | 773.438 MB | RF capacity dedicated to live traffic |

All deferred bulk is eventually delivered after optical recovery. None is silently discarded.

## Architecture consequence

The “RF fallback” requirement is too weak. GX-B1 needs readiness state, acquisition time and
failure-domain identity. The policy plane needs to distinguish:

- cold spare;
- warm validated standby;
- simultaneous split traffic; and
- whether switching preserves a transport session or only restores reachability.

This is also where the automotive analogy stops. A 0.5-second link gap can still destroy an
application transaction; preserving a data session requires MPTCP, QUIC migration, application
retry or another explicit mechanism.

## Boundary

Every number is assumed. RF and optical are treated as independent even though a real deployment
may share spacecraft power, pointing, gateway, spectrum coordination or ground infrastructure.
There is no terminal energy model, packet transport, link budget, weather process or hardware.
