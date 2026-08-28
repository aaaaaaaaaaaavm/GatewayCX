# S021 — Independent-code adapter interoperability

## Question

Can the GatewayCX authenticated client operate an adapter server that was separately implemented
with the Python standard library and does not import the GatewayCX runtime?

## Method

`python -m gatewaycx.independent_adapter_probe` parses the standalone server's imports, hashes its
source, launches [`adapters/standalone_rf_adapter.py`](../adapters/standalone_rf_adapter.py) as a
separate process and calls it through `GX-A1-JSONL-HMAC/0.1`.

The client exercises capabilities, snapshot, deferred submission, duplicate recognition, contact,
acquisition, time advance and transmission. It shuts the server down, restarts it over the same
standalone SQLite database and verifies the byte ledger again.

## Acceptance checks

- The server source imports no `gatewaycx` module.
- The authenticated wire version and portable adapter version match.
- The server identifies its distinct implementation.
- A traffic unit is accepted once and recognised as a known duplicate.
- Contact and acquisition reach `ready`.
- The assumed RF profile drains the declared unit without exceeding its capacity.
- Accepted/transmitted/queued counts survive a server restart.
- No payload content crosses the binding.

## Result

All bounded checks pass in
[`results/S021_independent_adapter.json`](../results/S021_independent_adapter.json).

This is the first GatewayCX interface result with separate client and server code paths. It is not
external validation: both were authored inside the same project. The server implements the S021
operation subset, not the complete future conformance profile. It controls no supplier terminal,
RF modem, optical system or physical bearer.
