# Native Internet compatibility

"The terrestrial Internet works on the Moon" is useful only after separating three cases that are
often collapsed.

## Case A: continuous native path

When a stable path exists, ordinary IP packets cross the cislunar network. Existing DNS, TLS,
HTTPS, email and file-transfer clients should function without a GatewayCX-specific application.
They still see large RTT, possible asymmetric capacity and higher loss cost.

This is the strongest meaning of native compatibility and the first emulation target.

## Case B: regional service instance

The user asks for the same service name, but resolution or service discovery selects a lunar
instance. Static content, identity material, application logic or data replicas are already local.
The application remains ordinary; placement removes cislunar dependencies.

This is how the system becomes pleasant rather than merely correct.

## Case C: disrupted delivery

A normal synchronous socket cannot remain useful through an arbitrary hours-long partition by
wishful thinking. GatewayCX may queue a message, object or task through a DTN service, or a service
may accept the request locally and reconcile later. That changes delivery semantics and must be
visible to the application or user.

This is resilient operation, not perfectly transparent native transport.

[`S005`](../../studies/S005_IP_DTN_RECOVERY.md) separates three acknowledgements that an
implementation must not collapse:

| State | Meaning |
|---|---|
| `accepted_pending` | A local ingress has persisted the object under a declared retention policy. |
| `bp_delivered` | The destination BP application agent or adapter has received the payload. |
| `remote_completed` | The remote application returned an idempotency-bound processing receipt. |

BP delivery is not application processing. Deduplication is not an exactly-once guarantee.

## Compatibility contract

GatewayCX will not claim that every terrestrial application works well unchanged. It will measure
applications by dependency round trips, timeout assumptions, consistency needs, bandwidth,
jitter sensitivity and partition tolerance. The target is:

- no special client for baseline continuous Internet access;
- ordinary service names and identities for regional instances;
- optional delay-aware APIs for applications that want stronger disruption behaviour; and
- honest failure or pending states where synchronous semantics cannot be preserved.
