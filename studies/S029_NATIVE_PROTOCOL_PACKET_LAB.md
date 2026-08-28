# S029 — Native protocol packet laboratory

## Question

Can the native Internet stack GatewayCX promises be exercised as packets and protocol exchanges
through two independent impairment methods rather than inferred from an HTTP latency model?

## Protocol matrix

`gatewaycx.native_protocol_lab` creates ephemeral IPv6 services and runs:

| Service | Concrete exchange |
|---|---|
| Naming | DNS AAAA query and response over IPv6 UDP |
| Secure web | TLS 1.3 with ALPN-negotiated HTTP/2 request |
| QUIC web | HTTP/3 request and response over QUIC |
| Email | SMTP envelope, DATA payload and stored-message digest |
| File | 32 KiB HTTP/2 object with exact byte count and digest |

The first method is a GatewayCX userspace TCP-chunk/UDP-datagram impairment relay. The second is the
Linux kernel `netem` qdisc. The GitHub Actions job captures both on loopback into one pcap, records
each method separately and refuses to pass unless every protocol check and a non-empty capture exist.

Run the userspace method with the pinned optional dependencies:

```bash
python -m pip install -e '.[lab]'
python -m gatewaycx.native_protocol_lab --method userspace --one-way-delay-ms 25 --output S029.json
```

The kernel method requires `CAP_NET_ADMIN`; capture requires `CAP_NET_RAW`. The repository workflow
configures and removes the qdisc in an isolated hosted runner and uploads the pcap/results as the
`s029-native-protocol-evidence` artifact.

## Boundary

The HTTP clients are standards libraries, not an ordinary browser, and the SMTP agent is minimal.
The initial CI delay is short so it proves wiring and captures without conflating that with lunar
usability. Full M1 evidence still needs the same matrix at 1.282 seconds one-way with controlled
loss, reordering, timeout and recovery cases, plus review of the capture itself.
