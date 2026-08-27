# Prior art and contribution boundary

GatewayCX enters a field with substantial prior work.

## Existing foundations

- The terrestrial Internet protocol suite already defines addressing, routing, transport, naming
  and security.
- IETF and CCSDS delay-tolerant networking work addresses long delay, scheduled contacts and
  disruption.
- NASA's LunaNet work defines an interoperable lunar communications and navigation framework.
- NASA and other agencies have demonstrated optical communication from lunar and deep-space
  distances.
- 3GPP non-terrestrial networking extends cellular architecture towards satellite access.
- Commercial and institutional programmes are developing lunar relays, optical terminals, ground
  networks, edge computing and space-based data storage.

The evidence and the integration boundary are expanded in
[`research/PROGRAMMES_AND_PRIOR_ART.md`](../research/PROGRAMMES_AND_PRIOR_ART.md). The standards
status is kept separately in [`research/STANDARDS_BASELINE.md`](../research/STANDARDS_BASELINE.md)
so a demonstrated technology is not accidentally described as a normative interface.

## What GatewayCX does not claim

It does not claim to have invented Internet Protocol in space, DTN, laser communication, a lunar
relay constellation, 5G NTN, CDNs or data centres beyond Earth.

## Contribution being tested

The proposed contribution is an end-to-end, vendor-neutral compatibility architecture connecting
those pieces to one user-level requirement: ordinary terrestrial Internet service should operate
natively in a lunar region. The engineering work is to define the interfaces, regional autonomy,
service placement, failure semantics and evidence needed to make that sentence true.

That contribution is a programme objective. It becomes demonstrated only when the public
requirements and conformance tests are implemented independently.
