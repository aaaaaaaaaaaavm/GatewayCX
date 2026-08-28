# S024 — Lunar relay ephemeris, contacts and failures

## Question

How do relay altitude and population affect South-pole, near-side and far-side service when orbital
motion, lunar occultation, capacity, optical weather and a satellite failure are sampled over time?

## Method

`python -m gatewaycx.ephemeris` propagates circular Kepler orbits for 48 hours at 600-second steps,
rotates positions into a Moon-fixed frame, calculates 10-degree surface visibility, builds a
line-of-sight inter-satellite graph and searches for a path to an Earth-visible relay. Each contact
gets a 100 Mbps access ceiling and either a 500 Mbps optical trunk or 50 Mbps RF fallback under a
declared weather pattern. Every candidate is repeated with its first satellite removed.

The generated record is [`results/S024_ephemeris.json`](../results/S024_ephemeris.json).

## Boundary

This is an ephemeris-driven architecture simulation, but not an operational ephemeris. It excludes
n-body perturbations, libration, station keeping, terrain, antenna patterns, acquisition, ground
stations and protocol overhead. It compares candidate classes; it does not select a constellation.
