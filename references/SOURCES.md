# Sources and standards map

This is the starting research map, not yet a standards-conformance statement. Links point to the
publishing organisation where possible. Accessed 2026-08-28.

## Internet and transport

- IETF, [RFC 8200: Internet Protocol, Version 6](https://www.rfc-editor.org/rfc/rfc8200)
- IETF, [RFC 9000: QUIC](https://www.rfc-editor.org/rfc/rfc9000)
- IETF, [RFC 9002: QUIC Loss Detection and Congestion Control](https://www.rfc-editor.org/rfc/rfc9002)
- IETF, [RFC 8446: TLS 1.3](https://www.rfc-editor.org/rfc/rfc8446)
- IETF, [RFC 9114: HTTP/3](https://www.rfc-editor.org/rfc/rfc9114)
- IETF, [RFC 1034: Domain Names](https://www.rfc-editor.org/rfc/rfc1034)
- IETF, [RFC 2488: Enhancing TCP Over Satellite Channels using Standard
  Mechanisms](https://www.rfc-editor.org/rfc/rfc2488) (Best Current Practice; historical but
  directly relevant)
- IETF, [RFC 3135: Performance Enhancing Proxies](https://www.rfc-editor.org/rfc/rfc3135)
  (Informational; records both mechanisms and architectural consequences)
- IETF, [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) and
  [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174), requirement language

## Delay and disruption tolerance

- IETF, [RFC 4838: Delay-Tolerant Networking Architecture](https://www.rfc-editor.org/rfc/rfc4838)
- IETF, [RFC 9171: Bundle Protocol Version 7](https://www.rfc-editor.org/rfc/rfc9171)
- IETF, [RFC 9713: BPv7 Administrative Record Types Registry](https://www.rfc-editor.org/rfc/rfc9713)
  (updates RFC 9171)
- IETF, [RFC 9758: Updates to the `ipn` URI Scheme](https://www.rfc-editor.org/rfc/rfc9758)
  (updates RFC 9171)
- IETF, [RFC 9172: Bundle Protocol Security](https://www.rfc-editor.org/rfc/rfc9172)
- CCSDS, [734.20-O-1: Bundle Protocol Version 7 Experimental
  Specification](https://ccsds.org/wp-content/uploads/gravity_forms/5-448e85c647331d9cbaf66c096458bdd5/2025/06/734x20o1.pdf),
  Orange Book, April 2025
- CCSDS, [734.2-B-1: Bundle Protocol Specification](https://ccsds.org/searchpubs/), Blue Book,
  September 2015. This is based on RFC 5050/BPv6; it must not be cited as a BPv7 profile.
- CCSDS, [734.3-B-1: Schedule-Aware Bundle Routing](https://ccsds.org/searchpubs/), Blue Book,
  July 2019

## Lunar networks and optical communications

- NASA/ESA/JAXA, [LunaNet Interoperability Specification Version
  5](https://www.nasa.gov/wp-content/uploads/2025/02/lunanet-interoperability-specification-v5-baseline.pdf),
  29 January 2025
- NASA SCaN, [Delay/Disruption Tolerant Networking](https://www.nasa.gov/communicating-with-missions/delay-disruption-tolerant-networking/), stating that completion of the DTN Project in January 2026 made DTN operational in the Near Space Network and Deep Space Network
- NASA, [Deep Space Optical Communications](https://www.jpl.nasa.gov/missions/deep-space-optical-communications-dsoc/)
- NASA, [Lunar Laser Communications Demonstration](https://www.nasa.gov/mission/lunar-laser-communications-demonstration-llcd/)
- NASA, [LLCD experiments with DTN over optical communications](https://www.nasa.gov/directorates/somd/space-communications-navigation-program/disruption-tolerant-networking-experiments-with-optical-communications/)
- ESA, [Moonlight lunar communications and navigation](https://www.esa.int/Applications/Connectivity_and_Secure_Communications/Moonlight)
- NASA, [Leveraging lunar relays](https://www.nasa.gov/technology/space-comms/near-space-network/leveraging-lunar-relays/)

## Shared ground-network demand

- NASA, [How the Deep Space Network supports agency missions](https://www.nasa.gov/technology/space-comms/deep-space-network/how-nasas-deep-space-network-supports-the-agencys-missions/)
- NASA JPL, [Service Scheduling Software](https://ai.jpl.nasa.gov/public/projects/sss/)
- NASA Office of Inspector General, [Revitalizing the Deep Space Network](https://oig.nasa.gov/news/revitalizing-the-deep-space-network-to-support-nasas-growing-space-exploration-program/)
- NASA, [Lunar Communications Relay and Navigation Systems](https://www.nasa.gov/goddard/esc/lcrns/)

## Physical constants and geometry inputs

- NIST, [speed of light in vacuum](https://physics.nist.gov/cgi-bin/cuu/Value?c), exactly
  299,792,458 m/s
- NASA Science, [Moon facts](https://science.nasa.gov/moon/facts/), mean Earth–Moon distance
  384,400 km
- NASA Space Place, [Earth–Moon distance range](https://spaceplace.nasa.gov/moon-distance/en/),
  225,309–251,903 miles on the cited page
- NASA JPL Solar System Dynamics, [Planetary physical parameters](https://ssd.jpl.nasa.gov/planets/phys_par.html),
  starting reference for lunar radius, gravitational parameter, mass ratio and rotation inputs used
  in the S022 first-order derivation

## Terrestrial access and non-terrestrial networks

- 3GPP, [Non-Terrestrial Networks overview](https://www.3gpp.org/technologies/ntn-overview)
- 3GPP, [Release 17 work summary](https://www.3gpp.org/about-us/technologies/lte), including NR
  NTN, IoT over NTN and 5GC edge-computing support
- 3GPP, [TS 24.193: Access Traffic Steering, Switching and Splitting](https://portal.3gpp.org/desktopmodules/Specifications/SpecificationDetails.aspx?specificationId=3607)

## Cross-industry mechanism sources

- IETF, [RFC 8684: Multipath TCP](https://www.rfc-editor.org/rfc/rfc8684)
- IETF, [RFC 6897: MPTCP application-interface considerations](https://www.rfc-editor.org/rfc/rfc6897),
  including make-before-break and break-before-make handover
- Android Open Source Project, [A/B seamless system updates](https://source.android.com/docs/core/ota/ab)
- Uptane, [Standard for secure automotive software updates](https://uptane.org/docs/2.0.0/standard/uptane-standard)
- Open Container Initiative, [Image specification](https://specs.opencontainers.org/image-spec/)
- IEEE, [802.1DG automotive TSN profile](https://standards.ieee.org/ieee/802.1DG/7480/)
- National Laboratory of the Rockies, [microgrid islanding and black start](https://www.nlr.gov/grid/black-start)

## Candidate commercial implementations

Commercial terminal and network suppliers will be recorded in a separate, equally structured
implementation matrix after capability profiles exist. A homepage is evidence that a company
markets a technology, not evidence that its current hardware closes a cislunar link.
