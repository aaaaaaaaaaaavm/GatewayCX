# GX-B1 bearer capability contract

## Purpose

GX-B1 is the replaceable seam between a cislunar gateway and an optical, RF or hybrid bearer. The
service plane should be able to ask *what capacity, contact, delay, queue and failure state exists?*
without importing a terminal manufacturer's private data model into every application.

The USB-C analogy is useful only at this interface level: independent implementations meet a
common contract. GX-B1 is not a claim that laser and RF terminals share a physical connector,
waveform, pointing system or regulatory approval.

## Published artifacts

- [`gatewaycx-bearer-profile.schema.json`](../../spec/schema/gatewaycx-bearer-profile.schema.json)
  defines the JSON shape using JSON Schema Draft 2020-12.
- [`gatewaycx.conformance`](../../gatewaycx/conformance.py) adds cross-field semantic checks without
  a third-party runtime dependency.
- [`reference-optical.json`](../../profiles/bearers/reference-optical.json) and
  [`reference-rf.json`](../../profiles/bearers/reference-rf.json) exercise the same contract with
  illustrative inputs.

The reference profiles represent no company and no hardware. Every numerical value has evidence
level `assumed`.

## Contract groups

| Group | What the gateway needs to know |
|---|---|
| Identity | Stable bearer identifier, media family and two endpoint regions |
| Performance | Directional capacity, latency range, acquisition ceiling and traffic-unit limit |
| Availability | Continuous, scheduled or opportunistic mode; prediction horizon and contact plan |
| Queue | Whether deferred traffic is accepted, durable bytes and backpressure behaviour |
| Security | Whether payload remains transparent and how management access authenticates |
| Telemetry | Link, rate, queue, next-contact and fault state with bounded freshness |
| Evidence | Source, date, conditions and commercial evidence level |

## Semantics that a flat hardware datasheet misses

1. A scheduled bearer without a contact-plan reference cannot support deterministic admission.
2. A bearer cannot accept deferred delivery with zero durable storage.
3. Payload termination or transformation must disclose the changed trust boundary.
4. A profile cannot claim `qualified` without linking a conformance report.
5. Capacity is directional and is not meaningful without delay, availability and queue state.

## What conformance means today

Passing the current checker means a document is structurally and semantically complete for the
pre-draft 0.1 fields. It does not prove that a terminal delivers the declared values. The two
reference documents test the interface shape, not multi-vendor interoperability. GX-INT-001 remains
open until two independent adapters exchange live state and traffic through the same gateway.

## Supplier fit

An optical-terminal company such as Astrogate—or any comparable RF, optical or hybrid supplier—can
fit below GX-B1 by publishing an adapter and attaching evidence to each claimed value. GatewayCX
does not require the supplier to disclose internal pointing, modulation or control implementation.
It requires the externally consequential behaviour to be testable.
