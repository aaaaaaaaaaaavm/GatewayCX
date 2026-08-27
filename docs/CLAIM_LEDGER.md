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
| C025 | Under the S009 RF-fallback inputs, strict priority delivers zero GX-T4 and GX-T5 bytes. | MODEL | S009 | Reproduced in CI; synthetic traffic |
| C026 | Under the same inputs, bounded priority fully serves GX-T0/GX-T1 and preserves GX-T4/GX-T5 progress. | MODEL | S009 | Reproduced in CI; shares not safety-approved |
| C027 | GatewayCX eliminates DSN scheduling contention. | — | No DSN integration or operational study | Rejected |
| C028 | Under S010 assumptions, warm RF standby reduces maximum interactive interruption from 20 seconds to 0.5 seconds. | MODEL | S010 | Reproduced in CI; no transport session model |
| C029 | RF and optical bearers are operationally independent. | ASSUMPTION | S010 omits common power, platform and ground failures | Open |
| C030 | Make-before-break reachability automatically preserves every application session. | — | Transport and application semantics differ | Rejected |
| C031 | Under S011 inputs, content addressing reduces wire bytes from 1.03 GB with monolithic resume to 430 MB. | MODEL | S011 | Reproduced in CI; synthetic layers |
| C032 | Under the S011 state machine, interruption before activation leaves slot A/v1 active. | MODEL | S011 | State model only |
| C033 | A/B activation makes shared database migrations rollback-safe. | — | Shared mutable state is outside the slot model | Rejected |
| C034 | S011 implements Uptane, OCI Distribution or secure boot. | — | It models selected semantics only | Rejected |
| C035 | Under S012 inputs, calibrated and popularity policies both prefetch 850 MB of useful content and avoid 27 remote requests. | MODEL | S012 | Reproduced in CI; one synthetic trace |
| C036 | Under S012 inputs, the overconfident forecast wastes 450 MB and avoids seven fewer remote requests than popularity. | MODEL | S012 | Reproduced in CI; outcome constructed for mechanism testing |
| C037 | S012 establishes that a learned predictor outperforms the simple baseline. | — | Useful bytes and avoided requests are tied | Rejected |
| C038 | A predictor may evict essential content when its confidence is high. | — | Essential reservation is outside predictor authority | Rejected |

The ledger will grow when the evidence grows. A claim does not become stronger by appearing in the
README.
