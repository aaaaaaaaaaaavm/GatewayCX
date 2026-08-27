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
| C011 | LLCD demonstrated lunar-orbit optical downlinks up to 622 Mbps and uplinks up to 20 Mbps. | PUBLIC FACT | NASA LLCD project page | Public demonstration; not a GatewayCX measurement |
| C012 | Optical communications and DTN have been exercised together over the LLCD lunar optical trunk. | PUBLIC FACT | NASA LLCD/DTN experiment record | Public demonstration; topology partly virtual |
| C013 | The current CCSDS BPv7 publication is experimental 734.20-O-1; 734.2-B-1 is RFC 5050/BPv6-based. | STANDARD | CCSDS active-publications catalogue | Source reviewed |
| C014 | LNIS V5 is the current NASA/ESA/JAXA lunar interoperability specification baseline. | PUBLIC FACT | NASA LNIS page and V5 document | Source reviewed |
| C015 | A performance-enhancing proxy is required for native lunar Internet service. | — | No comparative measurement | Rejected as a general requirement |
| C016 | An unmodified curl client can complete verified TLS 1.3 and HTTP/1.1 through the mean-distance delayed-byte harness. | MEASUREMENT | S004 | Socket-level only; TCP setup not delayed |
| C017 | Reusing the S004 HTTPS connection avoids a second TLS handshake. | MEASUREMENT | S004 `num_connects` and `time_appconnect` | Reproduced by CI at reduced delay |
| C018 | A 622 Mbps flow at mean lunar RTT has a bandwidth-delay product of about 199.38 MB. | DERIVATION | S006 | Reproduced in CI |
| C019 | Continuing to admit 100 Mbps for a one-day outage requires 1.08 TB before overhead and margin. | DERIVATION | S006 | Reproduced in CI |
| C020 | Under the S007 assumptions, 19 of 243 placements are both resource-feasible and partition-resilient. | MODEL | S007 | Reproduced in CI; not a demand forecast |
| C021 | A lunar replica always reduces cislunar backbone traffic. | — | S007 provides a counterexample when update traffic exceeds avoided user traffic | Rejected |
| C022 | Service placement can trade replication bytes for lower interaction delay and partition survival. | MODEL | S007 Pareto frontier | Model only |
| C023 | One machine-readable capability shape can describe the minimum GatewayCX fields for illustrative optical and RF bearers. | TEST | S008 reference profiles | Interface-shape test only |
| C024 | A commercial bearer has passed GX-B1 qualification. | — | No provider profile or conformance report | Rejected |

The ledger will grow when the evidence grows. A claim does not become stronger by appearing in the
README.
