# S018 — GX-A1 local process-boundary transport

## Question

Can a client drive the GX-A1 runtime seam through a separate adapter-server process, reject
malformed input without losing service, and restart while preserving the S017 traffic ledger?

## Method

The probe starts the reference adapter in a child process bound only to an OS-assigned TCP port on
`127.0.0.1`. A client performs capability discovery, snapshot, deferred submission, contact,
acquisition, time advance and transmission as one JSON line per connection. It then sends invalid
JSON directly, confirms the server remains alive, performs a controlled shutdown and starts a new
server against the same SQLite file.

The submitted unit is 65,536 bytes. At the illustrative RF profile's 100 Mbps forward capacity, a
100 ms window drains it completely after the 20-second acquisition ceiling.

## Result

All positive transport, error-isolation and restart checks pass. The second server begins with
`link_state=unavailable` while retaining 65,536 accepted and transmitted bytes and zero queued
bytes. Malformed JSON returns `invalid_json`; the first server remains available afterwards.

The deterministic record is
[`results/S018_adapter_transport.json`](../results/S018_adapter_transport.json).

## Boundary

Loopback is not authentication. The binding has no peer identity, message integrity,
confidentiality, authorisation or replay protection. Both processes use the same GatewayCX
reference adapter, so this is process separation rather than supplier interoperability. No payload
content, BPv7 bundle, packet, terminal SDK or physical bearer participates.
