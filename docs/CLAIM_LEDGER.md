# Claim ledger

## Evidence classes

- **STANDARD:** normative public specification
- **PUBLIC FACT:** traceable public source
- **DERIVATION:** equation and stated inputs
- **MODEL:** output of committed software
- **ASSUMPTION:** chosen input without confirming evidence
- **MEASUREMENT:** instrumented observation
- **PARTNER DATA REQUIRED:** cannot close from public information
- **DECISION:** project architecture choice

## Current claims

| ID | Claim | Class | Evidence | Status |
|---|---|---|---|---|
| C001 | Ideal one-way propagation at 384,400 km is 1.2822 s. | DERIVATION | `distance / c` in `gatewaycx/model.py` | Reproduced in CI |
| C002 | Ideal round-trip propagation at that distance is 2.5644 s before relay processing. | DERIVATION | `2 × distance / c` | Reproduced in CI |
| C003 | Increasing link capacity does not reduce geometric propagation delay. | DERIVATION | Propagation and serialization are separate model terms. | Supported analytically |
| C004 | Direct Earth-hosted transactions accumulate delay with sequential cross-region dependencies. | MODEL | S001 baseline | Model only |
| C005 | Local service placement can remove avoidable cislunar RTTs and backbone bytes. | MODEL | S001 versus S002 | Model only |
| C006 | Lunar-local services can complete while the backbone is unavailable. | MODEL | S003 | Architecture/model only |
| C007 | Every existing Internet application will work well unchanged from the Moon. | — | No evidence; deliberately not claimed | Rejected |
| C008 | BPv7 is suitable for all GatewayCX traffic. | — | P02 remains open | Not claimed |
| C009 | A named commercial terminal satisfies a GatewayCX cislunar bearer profile. | PARTNER DATA REQUIRED | No profile-qualified data yet | Open |
| C010 | GatewayCX has been deployed or hardware-validated. | — | No hardware exists in this record | Rejected |

The ledger will grow when the evidence grows. A claim does not become stronger by appearing in the
README.

