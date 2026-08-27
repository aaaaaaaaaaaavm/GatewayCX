# ADR-0003: Specify bearer capabilities, not vendors

- **Status:** accepted
- **Date:** 2026-08-27

## Context

Optical and RF terminal suppliers expose different control, telemetry and performance interfaces.
Making one supplier's current product the architecture would turn early familiarity into permanent
coupling.

## Decision

GatewayCX will define bearer capability and conformance profiles. A supplier is a candidate
implementation only after public or partner-provided data show that its hardware satisfies a
profile.

## Consequences

- Astrogate can fit naturally without becoming a project dependency.
- RF remains available for command, emergency and degraded operation.
- Vendor comparisons belong in a sourced implementation matrix, not the core requirement set.
- An open interface can coexist with proprietary terminals and operator services.

