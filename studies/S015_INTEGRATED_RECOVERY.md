# S015: Integrated RF/optical recovery

## Question

Do the RF/optical continuity model, durable-delivery contract and GX-O1 flight recorder still agree
when they are forced onto one event timeline and one byte ledger?

## Composition

S015 combines three previously separate boundaries:

- S010 supplies the 180-second warm-standby bearer schedule, traffic rates and keepalive cost;
- S005 supplies durable local acceptance, adapter delivery and application completion semantics;
  and
- S014 supplies GX-O1 fault codes, freeze frames and trace validation.

The replay does not paste their published answers together. It recalculates one shared byte budget
and checks that its control/interactive results reproduce S010 warm standby.

## Method

A synthetic 1 GB encrypted object is accepted into the lunar durable queue at 50 seconds. Optical
capacity is 500 Mbps. Optical fails at 60 seconds, RF becomes available at 60.5 seconds with 20 Mbps,
and the preferred optical path returns at 135 seconds after the declared 15-second reacquisition.

Control and interactive traffic consume 0.5 and 2 Mbps before the durable object. The simulation
runs in 0.5-second steps. The final adapter-delivery time adds mean-distance one-way propagation;
the application receipt adds a declared 20 ms processing interval.

```bash
python -m gatewaycx.integrated_replay
```

## Result

### Bearer and queue timeline

| Event | Time | Durable bytes remaining |
|---|---:|---:|
| Object accepted locally | 50.000 s | 1.000 GB |
| Optical contact lost | 60.000 s | 378.125 MB |
| RF fallback active | 60.500 s | 378.125 MB |
| Optical preferred path restored | 135.000 s | 215.156 MB |
| Earth adapter delivery | 139.782 s | 0 MB |
| Earth application completion | 139.802 s | 0 MB |

Optical carries 837.031 MB of the object and RF carries 162.969 MB. The complete 1 GB accepted
object reaches the Earth adapter with no modelled retransmission. That zero depends on the same
persistent receiver-ledger assumption declared in S005; it is not attributed to BPv7 or a bearer.

### Continuity

| Metric | S015 result |
|---|---:|
| Maximum control/interactive interruption | 0.5 s |
| Rejected control bytes | 31,250 |
| Rejected interactive bytes | 125,000 |
| RF keepalive bytes | 1,312,500 |

All three values reproduce the S010 warm-standby replay. Deferred object bytes are conserved, not
silently rejected, and every S015 diagnostic event passes GX-O1 validation.

## What the integrated trace now proves

Inside this synthetic replay, one traffic identity can be followed through:

1. local durable acceptance;
2. preferred-bearer failure;
3. degraded RF continuity;
4. optical reacquisition;
5. destination-adapter delivery; and
6. remote application completion.

The physical path states and application acknowledgements share the same clock. The trace records
no payload plaintext or direct user identity.

## Boundary

S015 remains a deterministic byte-budget model. It does not run packets, congestion control,
BPv7, BPSec, RF or optical hardware. RF and optical are assumed independent; terminal power,
weather correlation and pointing are absent. The result validates composition of current models,
not a deployed gateway. The next threshold is an executable pair of adapters with an actual
durable object store and fault-injected link process.
