# S008: Vendor-neutral bearer profile conformance

## Question

Can optical and RF bearer descriptions expose the same minimum service contract without naming a
manufacturer or pretending that their physical implementations are identical?

## Method

S008 defines the pre-draft GX-B1 JSON Schema, implements cross-field semantic checks and runs two
illustrative bearer profiles through the same checker.

```bash
python -m gatewaycx.conformance profiles/bearers/*.json
```

Negative tests remove a scheduled contact plan, remove durable queue capacity, terminate payload
security without disclosure and claim qualification without a report. Each case must fail.

## Result

The reference optical and RF descriptions pass the common pre-draft interface. The negative cases
fail for the intended reasons. This closes the machine-readable *shape* of the first capability
contract, not its values or external interoperability.

## Boundary

- Both profiles are illustrative and use assumed values.
- The semantic checker is not a complete JSON Schema implementation; standards-compliant JSON
  Schema tooling may additionally validate the published schema.
- No provider adapter, terminal, waveform, contact-plan service or reservation API is implemented.
- No supplier is qualified, preferred or endorsed.

S008 remains partially open until two independently built adapters pass the profile and carry
traffic through a reference gateway.
