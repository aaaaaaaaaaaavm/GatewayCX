# Lunar and orbital data centres

Data centres are part of the network because service placement determines how often a user pays
cislunar light time.

## Required functions

An early lunar compute region may provide:

- recursive DNS and service discovery;
- certificate and identity validation material;
- operating-system, package, map, media and model-weight caches;
- messaging and collaboration services;
- object storage and resumable transfer queues;
- read replicas and application-specific write logs;
- science processing, compression and prioritisation; and
- local monitoring, safety information and habitat applications.

## Placement candidates

| Placement | Strength | Cost or risk |
|---|---|---|
| Habitat/surface | Lowest latency to residents and equipment; maintainable with local infrastructure | Lunar dust, thermal cycling, local power and landing risk |
| Lunar orbit | Natural adjacency to relays; broad visibility; potentially continuous solar geometries | Radiation, maintenance difficulty and an extra access link |
| Earth | Mature capacity and operations | Every dependency pays cislunar delay and fails with the backbone |
| Hybrid | Service-specific placement and redundancy | Consistency, routing and operational complexity |

No placement is selected in the current baseline. P09 remains open until power, thermal,
radiation, mass, maintenance and demand models exist.

## Data semantics

Every service must classify data as one of:

- authoritative in the lunar region;
- authoritative on Earth with lunar read replica;
- multi-region with conflict resolution;
- immutable or content-addressed and freely cacheable;
- delay-tolerant object/message; or
- prohibited from replication by policy.

"Put a cache on the Moon" is not a consistency model. Encrypted third-party content also cannot be
silently cached by the network; the service provider must participate or publish reusable objects.

