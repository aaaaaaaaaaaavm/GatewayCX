# S009: Contact-aware admission and anti-starvation

## Question

When an optical contact disappears and only an RF fallback remains, can GatewayCX protect crew and
command traffic without silently starving science and background queues?

## Method

The model offers 145.5 GB across GX-T0 through GX-T5 to two synthetic ten-minute contact cases:

- nominal 500 Mbps optical plus 100 Mbps RF, providing 45 GB; and
- 100 Mbps RF fallback only, providing 7.5 GB.

It compares strict priority with a bounded-priority policy. Bounded priority first allocates a
declared minimum share to every active class, then lets higher classes borrow unused allocation.
Unsent deferred traffic queues; unsent non-deferred traffic is explicitly rejected.

```bash
python -m gatewaycx.admission
```

## RF-fallback result

Strict priority fully serves safety, command and interactive demand, partially serves operations,
and delivers zero science or background bytes. The bounded policy still fully serves GX-T0 safety
and GX-T1 command demand while delivering at least the declared floor to science and background.

This does not prove that the selected shares are safe. It proves that starvation behaviour can be
expressed, tested and reviewed instead of hidden inside a queue implementation.

## Architecture consequence

An admitted traffic unit needs one of four visible outcomes: delivered, partially delivered and
queued, queued, or rejected. Priority policy belongs above the optical/RF adapter, while available
contact bytes and durable queue limits come from GX-B1. This lets the same policy survive a bearer
change without pretending the two links have the same capacity or availability.

## Boundary

The volumes, contacts and shares are assumptions. The model has no ephemeris, antenna constraint,
packet scheduler, deadline utility, pre-emption or hazard analysis. It is not a model of NASA's DSN
scheduler and does not assign capacity to Voyager, JWST, Parker Solar Probe or Artemis.
