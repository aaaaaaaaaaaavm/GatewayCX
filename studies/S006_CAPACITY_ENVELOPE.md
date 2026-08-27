# S006: Earth–Moon capacity and buffering envelope

## Question

If a cislunar bearer advertises 20 Mbps, 100 Mbps, 622 Mbps or 1 Gbps, how much data must the
network keep in flight to use that rate, and how much durable storage is needed when the contact
disappears?

## Method

The deterministic derivation uses:

- NASA's cited closest and farthest Earth–Moon distances, converted from miles to kilometres;
- NASA's 384,400 km mean distance;
- the exact speed of light in vacuum;
- four comparison capacities, of which 20 and 622 Mbps are LLCD demonstrated extrema; and
- constant admitted traffic during 10-minute, one-hour and one-day outages.

The bandwidth-delay product is:

$$
BDP_{bytes} = \frac{capacity_{bit/s} \times RTT_s}{8}
$$

Generate the record with:

```bash
python -m gatewaycx.capacity
```

## Result at mean distance

| Nominal rate | Minimum in-flight window |
|---:|---:|
| 20 Mbps | 6.41 MB |
| 100 Mbps | 32.06 MB |
| 622 Mbps | 199.38 MB |
| 1 Gbps | 320.56 MB |

A link can close at 622 Mbps and still deliver far less to a single flow if the sender, receiver or
gateway cannot retain roughly 200 MB of in-flight state at mean lunar RTT. A 1 MiB window limits a
single mean-distance flow to about 3.27 Mbps regardless of a much larger physical link rate.

Storage is a separate scale. If 100 Mbps of admitted traffic continues during a one-day backbone
outage, 1.08 TB must be stored before replication overhead, protocol overhead or safety margin.

## Architecture consequence

The open bearer contract cannot stop at `capacity_mbps`. It needs at least RTT/one-way delay,
available contact duration, queue admission policy and assured durable storage. Service placement
reduces both the number of feedback loops and the backlog offered to that constrained interface.

## Boundary

This is a physics and arithmetic envelope. It is not a TCP tuning recommendation, a link budget or
a claim that LLCD's historical demonstration rate is continuously available. Loss, congestion,
relay processing, packet headers, contact geometry and reliability margin remain open.
