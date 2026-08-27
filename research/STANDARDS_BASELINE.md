# Standards baseline

**Baseline date:** 2026-08-27  
**Purpose:** identify the interfaces GatewayCX can inherit before proposing new ones.

This is a research baseline, not a declaration of conformance. A row marked *inherit* means the
project should use the named standard unless testing shows a specific incompatibility. A row marked
*profile* means GatewayCX may need to select options, add operational constraints or define a
mapping. It does not mean the underlying protocol is being replaced.

| Plane | Existing base | GatewayCX action | Present evidence |
|---|---|---|---|
| Local addressing and forwarding | IPv6, RFC 8200 | Inherit | Standard reviewed; implementation not tested |
| Secure web service | TLS 1.3, HTTP/2, HTTP/3 | Inherit and test | Standards identified; socket tests pending |
| Continuous-path transport | TCP and QUIC | Inherit and measure | Satellite guidance exists; cislunar behaviour pending |
| Disrupted delivery | BPv7, RFC 9171 and updates | Profile by traffic class | S005 semantic model; no GatewayCX node yet |
| Bundle security | BPSec, RFC 9172 | Profile | Standard identified; threat model pending |
| Scheduled routing | CCSDS SABR | Evaluate | Public recommended standard; no contact-plan trial yet |
| Lunar service interoperability | LNIS V5 | Align | Current public specification reviewed at programme level |
| Lunar access | 3GPP NTN and local radio systems | Adapt below IP | Capability family identified; lunar profile pending |
| Optical and RF bearers | Provider-specific terminals | Define a neutral capability contract | No provider qualified |
| Naming, identity and trust | DNS and Web PKI | Preserve across regions | Architecture decision; partition tests pending |

## The BPv7 distinction

The terminology matters:

- RFC 9171 is the IETF Bundle Protocol Version 7 standards-track specification.
- RFC 9713 and RFC 9758 update parts of RFC 9171.
- CCSDS 734.2-B-1, the September 2015 Blue Book, is based on RFC 5050/BPv6.
- CCSDS 734.20-O-1, the April 2025 Orange Book, is the CCSDS experimental BPv7 specification
  based on RFC 9171.

GatewayCX will therefore say *BPv7/RFC 9171* unless a tested implementation conforms to a stated
CCSDS BPv7 experimental profile. It will not use “CCSDS BPv7” as an undifferentiated label.

## Relationship to LunaNet

LNIS V5 is the primary public lunar interoperability baseline. It covers cooperative services for
missions in transit to, around and on the Moon, including Direct-With-Earth and lunar relay cases.
GatewayCX should align its bearer and inter-network interfaces with LNIS where applicable.

GatewayCX asks an additional end-to-end product question: what service placement, identity,
replication, failure semantics and operations are needed so an ordinary terrestrial Internet client
can use the same service namespace from a lunar region? This is a study focus, not a claim that
LunaNet excludes Internet protocols or edge services.

## What the evidence already rules out

1. **Capacity alone is not an Internet architecture.** LLCD demonstrated 622 Mbps down from lunar
   orbit, but propagation time and application dependency chains remain.
2. **Optical alone is not a resilient bearer plan.** The LLCD DTN experiment explicitly exercised
   storage and forwarding through optical-link interruption.
3. **DTN is not a transparent replacement for every IP flow.** BPv7 is message-oriented and fits
   disruption-tolerant delivery; interactive native applications still need continuous-path
   behaviour or a deliberate regional service boundary.
4. **A transport proxy is an architectural decision.** RFC 3135 records both the satellite
   performance rationale and the consequences of splitting or modifying end-to-end behaviour.
5. **Cellular access is one layer, not the entire Internet.** 3GPP NTN can inform lunar access and
   mobility while DNS, identity, service placement, backbone scheduling and disrupted delivery
   remain separate responsibilities.
6. **Bundle delivery is not application completion.** RFC 9171 delivery reporting ends at the
   destination Application Agent. GatewayCX needs a separate application receipt when processing
   completion matters.
7. **BPv7 custody cannot be inherited from BPv6 by vocabulary.** The BPv7 base protocol does not
   retain BPv6's custody-transfer flag; any stronger retention contract must name its mechanism.

## Next conformance work

- Extend the existing unmodified HTTPS socket result to packet-level DNS, IPv6, HTTP/2 and HTTP/3.
- Measure cold TLS, first byte and connection reuse separately.
- Define a bearer capability document independent of optical or RF supplier telemetry.
- Map each GatewayCX service interface to the exact LNIS V5 section before claiming alignment.
- Trial two BPv7 implementations before choosing any implementation-specific gateway contract.
- Implement the S005 acceptance, adapter-delivery and application-receipt states across that trial.

All source links are recorded in [`references/SOURCES.md`](../references/SOURCES.md).
