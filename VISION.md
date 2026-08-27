# Vision

## End state

A person or machine on the Moon joins a local network and receives ordinary Internet service.
Existing terrestrial services remain addressable through the same names, accounts and trust
relationships. Services that need low latency run or replicate in the lunar region. The cislunar
backbone carries traffic that genuinely belongs in the other region. If that backbone disappears,
the Moon does not become digitally inert.

GatewayCX calls this **one logical Internet across autonomous regions**.

It is one Internet because addressing, naming, identity, security and service interfaces
interoperate. It has autonomous regions because light time and disruption make an Earth-dependent
lunar network structurally fragile.

## User-level test

The architecture succeeds when an ordinary client can:

- open an existing Earth website without a space-specific browser;
- use the same identity and certificate trust in either region;
- communicate with a lunar-local service at local latency;
- reach Earth services with the delay made honest rather than hidden;
- continue using essential lunar services during a backbone outage; and
- resume or reconcile interrupted work after connectivity returns.

## What cannot be designed away

The mean-distance vacuum round trip is about 2.565 seconds. A relay constellation cannot reduce
that below the geometric light-time path. Interactive Earth–Moon conversation will remain delayed.
Earth control is unsuitable for time-critical lunar machinery. Strongly consistent databases
cannot remain simultaneously available across arbitrary partitions.

GatewayCX is not an attempt to argue with those facts. It is an attempt to stop paying the same
physical penalty unnecessarily ten times inside one application action.

## Beyond the Moon

Earth and the Moon are not separate planets, so the first system is properly cislunar rather than
interplanetary. Its regional architecture should nevertheless be extensible. A later Mars region
would change contact plans, autonomy and delay by orders of magnitude without requiring a new idea
of what an Internet region is.

