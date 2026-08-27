# S004: Native HTTPS through a delayed cislunar byte relay

## Question

Can an unmodified terrestrial HTTPS client establish a verified TLS 1.3 session and retrieve an
ordinary HTTP resource when the application bytes cross mean Earth–Moon propagation delay?

## Method

The committed harness starts three local components:

1. an unmodified `curl` client;
2. a TCP byte relay that delays traffic in each direction by `distance / c` and adds first-order
   serialization time; and
3. a TLS 1.3 HTTP/1.1 origin using an ephemeral, locally trusted test certificate.

The full run uses 384,400 km, 100 Mbps and a 65,536-byte object. It performs one cold request and a
second two-request sequence to observe connection reuse.

```bash
python -m gatewaycx.emulation --output results/S004_native_https.json
```

CI runs the identical path with a 10 ms one-way delay. That is a functional regression test, not a
reproduction of the committed mean-distance timing measurement.

## Result

The unmodified client completed all three HTTPS requests, verified the test certificate and reused
the TLS connection for the second request in the pair. The measured record is committed in
[`results/S004_native_https.json`](../results/S004_native_https.json).

The result supports **compatibility**, not acceptable lunar user experience. A fresh connection
pays repeated propagation while a reused connection avoids a new TLS exchange. This is direct
evidence for keeping useful connections alive and removing cross-region service dependencies.

## Experimental boundary

This is socket-level, not packet-level, emulation. The local TCP handshake between `curl` and the
relay is not delayed. The harness does not model loss, jitter, shared queues, orbital contacts,
weather, link acquisition or TCP congestion-window evolution. The origin and relay are loopback
processes. No spacecraft, optical terminal or RF link was involved.

The next independent method must use a packet-level emulator or hardware-in-the-loop path and must
include DNS, IPv6, HTTP/2 and HTTP/3 before the M1 exit criterion can close.
