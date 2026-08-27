# S007: Constrained lunar service placement

## Question

Given small orbital and surface compute/storage budgets, where should DNS, identity, operations,
static content and a science archive run so essential services survive an Earth-link partition?

## Method

The model evaluates all 243 placements of five services across Earth, lunar orbit and the lunar
surface. It rejects plans that exceed either lunar site's declared storage or compute budget, then
requires all three essential services to have a lunar instance.

For an Earth-hosted service, the model counts user request and response bytes on the cislunar
backbone. For a lunar-hosted service, it counts the declared replica-update bytes. User delay is the
request rate multiplied by each service's sequential round trips and the selected site's RTT.

The service demand, update rate, resource size and local RTT values are assumptions constructed to
exercise the architecture. They are not a settlement forecast.

```bash
python -m gatewaycx.placement
```

## Result

The search found 108 resource-feasible plans, of which 19 keep all essential services available
during a cislunar partition. Two plans remain on the delay/backbone Pareto frontier:

| Plan | Lunar placement | Interactive delay per hour | Cislunar bytes per hour |
|---|---|---:|---:|
| Minimum backbone | DNS, identity and operations on surface | 1,773.51 s | 13.052 GB |
| Minimum delay | DNS, identity and static content on surface; operations in orbit | 1,501.29 s | 15.551 GB |

The Earth-central comparison produces 57,751.21 seconds of aggregate interactive delay and 12.772
GB/h of cislunar user traffic, but no essential service survives a backbone partition.

## What changed in the architecture

“Put the service on the Moon” is incomplete. A replica exchanges user traffic for update traffic.
In this bounded case, partition resilience and much lower interactive delay cost *more* backbone
bytes than the Earth-central comparison. That is acceptable only if the operator makes the trade
explicit and has queue/storage capacity for the update stream.

GatewayCX should therefore expose service placement as a policy object containing:

- authority and replica sites;
- essential-outage requirement;
- storage and compute allocation;
- request dependency count;
- update volume and consistency class; and
- delay and backbone objectives without collapsing them into an unexplained weighted score.

## Boundary

This is a combinatorial architecture model, not a data-centre feasibility study. Compute units are
abstract. It omits power, cooling, radiation, mass, consistency protocols, replica fan-out,
failures and cost. Those constraints can be added without changing the exhaustive-search method.
