# GX-A1 authenticated reference binding

## Decision

S019 adds a second, explicitly versioned process binding:
`GX-A1-JSONL-HMAC/0.1`. It keeps S018 available as the unauthenticated transport baseline and
adds a narrow trust mechanism rather than silently changing the earlier result.

Each request carries a client identifier, a strictly increasing sequence, a request identifier,
an operation, arguments and an HMAC-SHA256 message authentication code. The HMAC covers the
canonical JSON representation of every field except `mac`. Each authenticated response echoes the
request identity and sequence and carries its own HMAC.

## Key and replay state

The reference server reads one 256-bit pre-shared key from a file at process start. The key is
never written to the traffic database, result file or diagnostic record. SQLite persists only:

| Field | Purpose |
|---|---|
| `client_id` | Select the configured trust relationship. |
| `last_sequence` | Reject any validly signed sequence that is not newer. |

MAC comparison uses `hmac.compare_digest`. Sequence advancement runs inside a SQLite
`BEGIN IMMEDIATE` transaction so two requests cannot both claim the same next sequence in the
single-node reference store.

The sequence is consumed after authentication and before operation dispatch. This is deliberate:
a malformed or failing operation cannot be replayed as a fresh command. It also means a response
lost after dispatch creates uncertainty. Callers must reconcile operation state, and operations
that commit traffic need their own idempotency identity. GX-A1 `submit` already uses
`traffic_unit_id`; the other operations do not yet have a general transaction protocol.

## Security boundary

This mechanism establishes possession of one shared secret and message integrity for the local
reference exchange. It does **not** establish:

- confidentiality or traffic-flow privacy;
- public-key identity, certificate validation or organisational federation;
- key derivation, rotation, revocation or recovery;
- per-operation authorisation or multi-role policy;
- forward secrecy, hardware-protected keys or secure boot;
- protection against a compromised authorised process; or
- flight, safety or cryptographic certification.

Loopback remains a deployment restriction, not an identity mechanism. A production or
multi-provider binding needs a reviewed secure transport, lifecycle-managed credentials, policy
and auditable recovery semantics. S019 is the executable point from which those choices can be
tested; it is not their substitute.

## S019 result

The probe accepts a correctly signed request and response, rejects request modification and an
incorrect key, rejects an exact replay in the same process, restarts the server over the same
database, rejects the replay again and accepts the next sequence. It also checks that the replay
table has no secret column and that traffic-byte state survives restart.

Both endpoints remain GatewayCX reference software on one machine. No terminal, supplier adapter
or physical bearer is involved.
