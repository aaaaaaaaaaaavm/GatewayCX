# S011: Content-addressed A/B lunar updates

## Concept transfer

Two mature mechanisms solve different halves of the problem:

- automotive/mobile A/B updates keep the running system untouched until an inactive target is
  complete, verified and healthy; and
- container registries describe immutable content by digest so unchanged layers can be reused.

GatewayCX combines them for lunar gateways and essential regional services. A manifest says which
objects form the target version. The lunar depot requests only missing chunks. A contact
interruption leaves the active slot untouched and already verified chunks remain useful.

## Question

How much cislunar traffic and failure exposure can be removed when a related service version is
distributed as verified chunks and activated through an A/B state machine?

## Method

The synthetic current image is 1.00 GB in 100 ten-megabyte chunks. The target is 1.03 GB in 103
chunks. Its 600 MB base layer is unchanged; runtime, application and configuration layers change.
The first contact delivers 250 MB and then stops.

The comparison includes:

- a monolithic transfer restarted after interruption;
- a monolithic transfer with perfect byte-range resume; and
- a content-addressed transfer requesting only absent chunk digests.

The activation replay runs once with a successful health check and once with a failed health check.

```bash
python -m gatewaycx.update_delivery
```

## Result

| Transfer | Cislunar wire bytes |
|---|---:|
| Monolithic restart | 1.280 GB |
| Monolithic range resume | 1.030 GB |
| Content-addressed missing chunks | 0.430 GB |

The first contact delivers 250 MB of missing chunks; the second resumes the remaining 180 MB.
Sixty target chunks are already present and no completed chunk is retransmitted.

During the interrupted download, slot A remains active on v1. Slot B cannot become active until the
manifest and every chunk pass the declared pre-activation checks. If the v2 trial boot fails its
health check, B becomes unbootable and the state returns to A/v1.

## Architecture consequence

The lunar region needs a signed inventory protocol, not merely a file mirror. An update manifest
must carry content identities, compatible bundle identity, target hardware, monotonic version,
freshness and signatures. The activation service must report `downloading`, `complete`, `verified`,
`trial`, `successful`, `unbootable` and `rolled_back` as distinct states.

Content identity also lets software, maps and AI model weights share the same transport machinery
without making them the same trust class.

## Boundary

The study hashes descriptor metadata; it does not generate or transfer gigabyte payloads. It does
not implement OCI Distribution, Uptane, signatures, secure boot or a filesystem. A/B rollback does
not solve incompatible database schemas, shared mutable storage or corrupted hardware. Stable
chunking and cross-version encryption policy determine whether the byte savings survive reality.
