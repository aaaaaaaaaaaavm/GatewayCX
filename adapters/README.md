# Standalone adapter examples

This directory contains implementations that do not import the `gatewaycx` Python package. Their
purpose is to keep an interface test from passing only because client and server share the same
classes, validation code or traffic store.

`standalone_rf_adapter.py` implements the authenticated JSONL envelope and a bounded GX-A1 RF
operation subset with the Python standard library. S021 launches it as a separate process and
drives it with the GatewayCX authenticated client.

Standalone means a separate code path. It does not mean independent organisation, supplier,
product, terminal or validation authority. The example has no modem API, payload transfer,
pointing control, physical link, production credential lifecycle or flight assurance.
