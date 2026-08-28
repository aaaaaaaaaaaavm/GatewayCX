# Open problems

An open problem is not a decorative future-work list. Each item names the evidence required to
close it.

| ID | Problem | Present state | Closure evidence |
|---|---|---|---|
| P01 | Native protocol behaviour | S029 dual-method lab executes DNS/IPv6, TLS 1.3, HTTP/2, HTTP/3, SMTP and file transfer with CI packet capture; first external run pending | Lunar-delay matrix, browser/MUA clients, loss/reordering cases and reviewed captures |
| P02 | IP/DTN boundary | S005 semantic and trust-boundary model | Working gateway, two BPv7 implementations and fault-injected security evidence |
| P03 | Lunar regional topology | S024 time-samples three circular candidate constellations, three sites, contacts, capacity and one-node failure | SPICE/n-body candidate trajectories, terrain, ground sites and externally reviewed constellation design |
| P04 | Optical link performance | S025 class budget covers geometry, photon margin, pointing, weather and RF fallback | Terminal-specific acquisition model plus hardware/field data |
| P05 | RF fallback capacity | S025 S/Ka classes include clear and +6 dB loss cases; S024 applies fallback capacity | Terminal-specific coding/interference analysis and measured degraded-mode service |
| P06 | Cache and replica placement | S007 synthetic exhaustive model | Trace-driven demand and physical resource model |
| P07 | Identity during partition | S028 X07 validates signed offline capability, stale revocation, expiry and reconnection | Federated PKI, protected keys, time source and operator revocation trial |
| P08 | Database consistency | S028 X08 executes fail-closed strong, convergent register and escrow policies across two SQLite replicas | Application traces and a distributed database implementation under network faults |
| P09 | Lunar data-centre feasibility | S026 compares surface, orbital and hybrid power/thermal/radiation/mass/storage classes | Qualified parts, environment, maintenance, launch and deployment inputs |
| P10 | Safety traffic policy | S009 synthetic anti-starvation model | Hazard-derived shares, deadlines and fault-injected scheduler |
| P11 | Multi-provider governance | No operating agreement | Interface, liability, settlement and incident model |
| P12 | Commercial case | S027 executes cost per delivered and retained bit across utilisation/availability sensitivities | Evidence-backed demand, supplier costs, financing and service pricing |
| P13 | Ownership and trademark | Exploratory public record | Written organisational policy before commercial release |
| P14 | Lunar software and data update safety | S028 X14 signs a manifest, rejects corrupt payload, preserves A on failed health and rolls back a schema transaction | Registry/transparency integration, secure boot and real service deployment |
| P15 | Predictive cache value | S012 synthetic admission trace | Held-out lunar demand, calibrated candidate, drift and contact-aware replay |
| P16 | Lunar black start | S028 X16 launches five child services without Earth and executes lost-time dependency failure | Electrical start, real daemons, oscillator error, network interfaces and reconnection tests |
| P17 | Federated diagnostics | S014 GX-O1 generated reference trace | Independent adapters, authenticated event transport, clock model and observed fault replay |
| P18 | Integrated recovery testbed | S028 X18 injects 60 seeded transaction faults, corrupts a real SQLite file and restores exact committed rows; S020/S021 retain kill and separate-process evidence | Packet path, external BPv7/bearer implementations, raw-device faults and link process |
