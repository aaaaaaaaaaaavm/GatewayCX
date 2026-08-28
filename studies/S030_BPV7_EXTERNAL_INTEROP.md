# S030 — External BPv7 fault-gateway interoperability

## Question

Can two independently maintained RFC 9171 implementations exchange exact application payloads in
both wire directions through the real GatewayCX adapter, authentication and durable-ledger path?

## Method

The external workflow fetches and builds two pinned dependencies without copying their source into
GatewayCX:

- `dtn7-go` `53d0208fe8da6dc3d4cb5d54c859cd4d59d921e7` provides the Go BPv7 builder/parser.
- `bp7-rs` `e3289bca2aed8f86585790d7aebd340d7bde7289` provides the Rust `bp7` encoder/decoder used by
  the dtn7-rs ecosystem.

For each direction, `gatewaycx.bpv7_interop_lab`:

1. accepts the opaque bundle through the S019 HMAC and durable sequence boundary;
2. submits its ID and byte count into the real GX-A1 RF adapter and SQLite traffic ledger;
3. injects `GX.BEARER.CONTACT_LOST` and sends a half-length wire image that the other parser must reject;
4. clears the fault, reacquires the bearer and transmits the complete ledgered byte count; and
5. requires the independent decoder to recover the exact application payload.

The workflow also rejects tampered authenticated metadata, rejects reuse of each accepted sequence
and proves the final accepted/transmitted byte totals equal the two bundle wire lengths.

## Boundary

This crosses real external BPv7 serializers and parsers, but not full routing daemons or a TCP/UDP/LTP
convergence-layer session. GatewayCX does not inspect or modify bundle contents. BPSec, endpoint
registration, contact plans, routing, expiry and remote application receipts remain later M2 tests.
External licences remain with their projects; no dependency source or built binary is distributed by
this repository.
