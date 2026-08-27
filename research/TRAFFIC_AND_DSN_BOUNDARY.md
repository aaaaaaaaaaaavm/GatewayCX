# Traffic growth and the DSN boundary

## The congestion problem is real

NASA describes the Deep Space Network as a shared, scheduled resource supporting dozens of
missions. Public NASA material reports requested antenna time exceeding availability, with
missions negotiating around critical events and spacecraft using onboard storage when data cannot
be returned immediately. NASA's Office of Inspector General has separately warned that crewed
Artemis traffic takes precedence and can conflict with major science users.

This means GatewayCX must not define “Moon Internet” as *send every lunar user session through the
same scarce DSN antenna schedule*. That would amplify the contention it is supposed to relieve.

## Architectural boundary

GatewayCX separates three jobs:

1. **Lunar regional traffic** stays within lunar access, relay and compute infrastructure.
2. **Earth–Moon regional transit** uses commercial/government lunar relays and Direct-With-Earth
   services exposed through provider-neutral contacts, queues and capacity.
3. **Deep-space mission support** remains the job of DSN and peer deep-space networks, with
   federation at terrestrial routing, service and data-exchange points.

NASA is already placing commercial lunar relays in the Near Space Network portfolio. GatewayCX can
align with that direction while adding user-level Internet compatibility, regional compute and an
open multi-provider service seam.

## How this reduces pressure instead of moving it

- Local lunar DNS, identity, content and operations remove repeated Earth round trips.
- Science products can be processed, filtered, compressed and prioritised near their source.
- Bulk objects can wait for planned contacts instead of holding an interactive session open.
- Optical trunks increase delivered bits when acquired; RF maintains a degraded service and
  control path.
- Durable admission prevents a gateway from accepting more delayed traffic than it can retain.
- Published minimum shares prevent a permanent emergency policy from silently starving science
  and background queues.

## What GatewayCX does not replace

It is not a DSN antenna scheduler, flight-operations authority or mission priority policy. S009 is
a regional byte-budget model that makes delivery, queuing and rejection visible. Real scheduling
requires ephemerides, antenna visibility, spacecraft constraints, ground weather, maintenance,
mission events and authorised safety policy.
