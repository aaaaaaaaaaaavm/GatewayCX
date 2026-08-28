# S023 — Ground-network offload boundary

## Question

How can a dedicated lunar relay and ground segment protect scarce deep-space support capacity, and what does optical inter-satellite communication contribute?

## Method and result

`python -m gatewaycx.ground_offload` uses synthetic, dimensionless scheduled-service units. A shared 100-unit pool receives 140 units and leaves 40 backlogged. Separating the synthetic 60-unit lunar demand into a 70-unit lunar pool clears both pools and raises served deep-space demand from 57.14 to 80 units. This illustrates isolation, not real DSN relief.

A second calculation makes delivery the minimum of lunar ingress, optical ISLs, Earth trunk and ground gateway. ISLs with zero Earth egress deliver zero; a 50-unit trunk limits 120 ISL units; scaling the trunk moves the bottleneck to the 70-unit ground gateway.

The result is [`results/S023_ground_offload.json`](../results/S023_ground_offload.json). No input is an antenna-hour, byte volume, mission request or measurement for Voyager, JWST, Parker Solar Probe, Artemis, DSN or a provider. Real closure requires schedules, ephemerides, links, weather, priorities, costs and authority.
