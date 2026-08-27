# S005: IP/DTN interruption and recovery semantics

## Question

What exactly happens to an Internet transaction when the Earth–Moon path disappears after part of
its payload has crossed, and where can disruption tolerance be added without lying about
acknowledgement or encryption?

## Standards boundary

[BPv7/RFC 9171](https://www.rfc-editor.org/rfc/rfc9171) is an application-layer
store-carry-forward overlay. Its status reports can describe bundle reception, forwarding,
delivery and deletion. The standard also says that a delivery report means the payload was
delivered to the destination Application Agent; it does not mean that the application processed
the payload. Status reporting is optional and disabled by default because indiscriminate reports
can add unacceptable traffic.

BPv7 does not carry BPv6's native custody-transfer flag. RFC 9171 moves that subject to separate
bundle-in-bundle encapsulation work. GatewayCX therefore does not turn the word "custody" into an
unspecified reliability promise.

[BPSec/RFC 9172](https://www.rfc-editor.org/rfc/rfc9172) can provide integrity and confidentiality
between a BP security source and acceptor. Those endpoints are not automatically the original web
client and service. Application-to-application confidentiality still needs a declared endpoint and
key boundary.

## Compared modes

| Mode | What the client uses | Durable local acceptance | Plaintext at gateway | Outage behaviour |
|---|---|---:|---:|---|
| Native HTTPS retry | Ordinary end-to-end HTTPS | No | No | Socket fails; application retries |
| Terminating deferred proxy | Owner-approved local HTTPS proxy | Yes | Yes | Proxy resumes the durable object |
| Opaque deferred object | Delay-aware object API over local HTTPS | Yes | No | Encrypted object resumes through the DTN path |

The last two modes return an explicit `accepted_pending` state. Neither represents that state as
remote completion.

## Method

The deterministic replay sends a synthetic 10 MB object over a 20 Mbps mean-distance cislunar
path. The path fails after 4 MB and returns after 120 seconds.

The native case discards the partial synchronous transaction, pays a declared three-round-trip
reconnection cost and sends the complete object again. The two durable cases assume a persistent
receiver chunk ledger and send only the remaining 6 MB after recovery. That ledger is an
application/object-layer assumption, not a capability attributed to BPv7 itself.

```bash
python -m gatewaycx.disruption
```

## Result

| Mode | Cislunar wire bytes | Retransmitted | User-visible state during outage | Remote completion |
|---|---:|---:|---|---:|
| Native HTTPS retry | 14 MB | 4 MB | Failed or timed out | 133.293 s |
| Terminating deferred proxy | 10 MB | 0 MB | Accepted, pending | 125.302 s |
| Opaque deferred object | 10 MB | 0 MB | Accepted, pending | 125.302 s |

The byte and timing difference is conditional on the declared chunk ledger and reconnect model.
The more important result is the acknowledgement chain:

1. `accepted_pending` means the lunar ingress persisted the object under a retention policy.
2. `bp_delivered` means the destination BP adapter received the payload.
3. `remote_completed` requires a separate idempotency-bound receipt from the remote application.

A mutation can be delivered more than once. The model requires an idempotency key and suppresses a
second application effect, but it still does not claim exactly-once execution.

## Architecture decision

GatewayCX keeps native end-to-end HTTPS for continuous paths. It offers durable delivery only as an
explicit service contract:

- a terminating proxy is permitted only when the service owner chooses that trust boundary; or
- an opaque object remains encrypted by the applications while gateways store and forward it.

An arbitrary synchronous HTTPS stream cannot be converted into an indefinite-partition service
transparently. That is not a missing optimisation. The application semantics are different.

## Boundary

S005 is a state and timing model. It does not run TCP, TLS, BPv7, BPSec or a BP convergence layer.
It does not simulate lost status reports, expiration, depleted storage, fragmentation, route
selection or key distribution. A real gateway and two independent BPv7 implementations are still
required before ADR-0002 can become final.
