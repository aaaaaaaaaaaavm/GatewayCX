# Relay orbit envelope

GatewayCX does not select a relay orbit by analogy to terrestrial GEO. Earth geostationary orbit
works because a 23 h 56 min circular equatorial orbit can remain fixed in Earth's rotating frame.
The Moon rotates once per sidereal month. S022 derives that the corresponding two-body circular
radius lies outside the approximate lunar Hill sphere.

The first architecture rule is therefore:

> Treat “lunar GSO” as a rejected shorthand, not a deployment layer.

A roughly 24-hour lunar orbit can sit well inside the Hill screen, but it moves around the lunar
surface because 24 hours does not match lunar rotation. It is a high relay shell, not a stationary
slot.

## Consequence for the network

The logical GatewayCX layers remain useful, but they must not be assigned prematurely to fixed
orbit names:

| Network role | Geometry question before assignment |
|---|---|
| Surface access | Which sites, terrain masks and elevation limits must be served? |
| Lunar regional relay | Which orbit families meet coverage, latency, outage and capacity targets? |
| Earth–Moon trunk | Which nodes maintain Earth visibility and optical/RF diversity? |
| Data/compute node | Which location closes power, thermal, radiation, maintenance and backhaul? |

Candidate solutions may mix low circular orbit, higher circular or elliptical relays, frozen or
resonant families and libration-region trajectories. “Fewer satellites at higher altitude” is only
one axis. Higher shells also increase slant range and link-budget burden; lower shells move faster
and require more handovers. Multi-body stability, station keeping and Earth occultation can
dominate both.

S022 supplies an executable screening envelope. A selection requires ephemeris-based contact
analysis, surface demand sites, failures, optical/RF link budgets and capacity allocation.
