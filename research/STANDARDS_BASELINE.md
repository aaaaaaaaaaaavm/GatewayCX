# Standards baseline

**Baseline date:** 2026-08-28
**Purpose:** identify the interfaces GatewayCX can inherit before proposing new ones.

This is a research baseline, not a declaration of conformance. A row marked *inherit* means the
project should use the named standard unless testing shows a specific incompatibility. A row marked
*profile* means GatewayCX may need to select options, add operational constraints or define a
mapping. It does not mean the underlying protocol is being replaced.

| Plane | Existing base | GatewayCX action | Present evidence |
|---|---|---|---|
| Local addressing and forwarding | IPv6, RFC 8200 | Inherit | S029 dual-method IPv6/DNS packet run passed at short delay |
| Secure web service | TLS 1.3, HTTP/2, HTTP/3 | Inherit and test | S004 HTTP/1.1 and S029 short-delay H2/H3 measurements |
| Continuous-path transport | TCP and QUIC | Inherit and measure | Satellite guidance exists; cislunar behaviour pending |
| Disrupted delivery | LNIS V5 §3.1.2; BPv7, RFC 9171 and updates | Inherit BPv7; profile service/operations semantics around it | S030 pinned dtn7-go/bp7-rs bidirectional harness pending external run |
| Bundle security | BPSec, RFC 9172 | Profile | Standard identified; threat model pending |
| Scheduled routing | CCSDS SABR | Evaluate | Public recommended standard; no contact-plan trial yet |
| Lunar service interoperability | LNIS V5 | Treat as the current baseline and map every applicable seam | Sections 3.1.1.2, 3.1.2, 3.1.3, 4.5, 5.1, 6.1 and 6.4 mapped |
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

## Relationship to LunaNet and operational NASA DTN

LNIS V5 is the primary public lunar interoperability baseline. It defines a network of cooperating
networks and expects multiple public and private LunaNet Service Providers. GatewayCX inherits that
model. LNIS V5 §3.1.1.2 defines real-time IP service; §3.1.2 requires BPv7 for disruption-tolerant
service; §4.5 permits IPv4, IPv6 and BPv7 network-layer interfaces over links both inside and outside
the LNIS physical-link set; and §§5.1, 6.1 and 6.4 establish provider-to-provider communication and
crosslink boundaries.

NASA now states that, after the multi-centre DTN Project completed in January 2026, DTN is an
operational service in both the Near Space Network and Deep Space Network. GatewayCX consequently
does not treat DTN or Bundle Protocol as its invention. It must interoperate with that standards and
operations ecosystem.

GatewayCX asks the layer-above and layer-around question: what service placement, identity,
replication, bearer abstraction, failure semantics, operations and commercial machinery are needed
so an ordinary terrestrial Internet client can use the same service namespace from an autonomous
lunar region? This is a profile and implementation focus, not a claim that LunaNet excludes Internet
protocols or edge services. The exact boundary is recorded in
[`INTEROPERABILITY_LAYERING.md`](../docs/architecture/INTEROPERABILITY_LAYERING.md).

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

- Run and review the S029 dual-method DNS/IPv6/TLS/HTTP2/HTTP3/SMTP/file packet artifact at lunar delay and under loss/reordering.
- Measure cold TLS, first byte and connection reuse separately.
- Define a bearer capability document independent of optical or RF supplier telemetry.
- Extend the LNIS section mapping into field-level conformance cases as applicable documents mature.
- Extend S030 wire interoperability into full daemon and convergence-layer sessions before choosing an implementation-specific gateway contract.
- Implement the S005 acceptance, adapter-delivery and application-receipt states across that trial.

All source links are recorded in [`references/SOURCES.md`](../references/SOURCES.md).
