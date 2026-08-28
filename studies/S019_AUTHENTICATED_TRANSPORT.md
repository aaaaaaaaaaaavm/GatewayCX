# S019 — Authenticated adapter transport

## Question

Can the GX-A1 reference process boundary authenticate a configured client, detect modification and
reject replay after a server restart without storing its secret or payload content in the durable
ledger?

## Method

`python -m gatewaycx.authenticated_transport_probe` creates a temporary 256-bit pre-shared key,
starts the RF reference adapter in a separate process and exchanges canonical JSONL envelopes over
TCP loopback. The probe then:

1. authenticates a capability call and traffic submission;
2. sends one valid snapshot twice;
3. changes an already-signed operation;
4. signs a request with the wrong key;
5. cleanly restarts the server over the same SQLite database;
6. repeats the earlier valid envelope; and
7. sends the next correctly signed sequence.

The committed JSON excludes keys, MACs, ports and process identifiers. Random key generation
therefore does not change the deterministic result.

## Acceptance checks

- Valid request and response MACs are accepted and verified.
- Same-process and post-restart replay return `replayed_sequence`.
- Modified and wrong-key requests return `authentication_failed`.
- The next sequence after restart succeeds.
- Accepted traffic byte state persists.
- The replay schema contains only client identity and sequence state.
- No payload content is supplied.

## Result

All bounded checks pass in [`results/S019_authenticated_transport.json`](../results/S019_authenticated_transport.json).

This establishes a local reference authentication and integrity mechanism. It does not establish
confidentiality, PKI, key lifecycle, role authorisation, abrupt-power-loss durability, independent
interoperability or terminal security. Because sequence state advances before dispatch, a caller
that loses a response must reconcile state before deciding whether a new operation is safe.
