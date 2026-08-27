# S013: Lunar network islanding and black start

## Concept transfer

An electrical microgrid does not remain resilient merely because it has local generators. It must
disconnect cleanly, preserve a local reference, start a minimal dependency set without the wider
grid, and reconnect in a controlled order. GatewayCX transfers that dependency discipline—not the
electrical control equations—to the lunar regional Internet.

The corresponding network references are holdover time, a local trust root, authoritative local
naming, identity verification, route control, durable queues and an operations API. If any of those
quietly depends on Earth, a lunar data centre can have power and compute yet still fail to restart.

## Question

Can the declared essential lunar network services restart during an Earth partition, and which
single local dependency causes the largest logical collapse?

## Method

S013 executes a deterministic dependency graph in stages. It compares:

- an Earth-coupled graph during partition;
- the same graph after the three Earth dependencies return; and
- an islandable graph during partition.

It then removes each of seven local essential services, one at a time, and repeats the islanded
start. A service starts only when all declared dependencies are running.

```bash
python -m gatewaycx.black_start
```

## Result

| Scenario | Essential services started |
|---|---:|
| Earth-coupled, Earth partitioned | 2 / 7 |
| Earth-coupled, Earth restored | 7 / 7 |
| Islandable, Earth partitioned | 7 / 7 |

In the Earth-coupled graph, local naming waits for Earth DNS, identity waits for Earth identity, and
route control waits for Earth contact control. Only holdover time and the local trust root start.
In the islandable graph, all seven services start in four dependency stages without Earth.

Single-fault injection exposes holdover time as the largest declared dependency: with it absent,
only the local trust root starts. Failure of either the local trust root or route controller leaves
four of seven essential services running. That is an architecture warning, not evidence that a
particular clock or routing implementation will fail.

## Architecture consequence

"Lunar region" needs a black-start profile with a machine-readable dependency graph and a tested
Earth-absent start procedure. At minimum it should declare:

- local sources of time, trust, naming and route policy;
- maximum safe holdover and credential-freshness rules;
- the start and reconnect order;
- degraded modes when one reference is unavailable; and
- evidence captured before and after each transition.

The graph also connects the data-centre and communications problems. Storage and compute are not
operationally local if their control dependencies still cross the cislunar backbone.

## Boundary

This is logical dependency reachability, not a power, oscillator, secure-boot or hardware model.
"Started" means dependencies are present, not that the service is correct or secure. The graph is
an architecture assumption constructed to expose coupling. Single-fault tests omit correlated and
Byzantine failures, clock-error growth, compromised keys and state reconciliation after Earth
returns.
