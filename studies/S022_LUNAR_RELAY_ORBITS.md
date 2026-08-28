# S022 — Lunar relay-shell envelope

## Question

Can a Moon-fixed analogue of geostationary orbit anchor a small high lunar relay constellation,
and what first-order coverage trade appears as relay altitude increases?

## Method

`python -m gatewaycx.lunar_orbits` applies two-body circular-orbit geometry and an approximate Hill
sphere screen. It derives:

\[
r_{sync}=\left(\frac{\mu T^2}{4\pi^2}\right)^{1/3}
\]

for the Moon's sidereal period, and:

\[
r_H \approx a\left(\frac{m_{Moon}}{3m_{Earth}}\right)^{1/3}
\]

for the approximate lunar Hill radius. Four circular shell altitudes are then compared using
orbital period, surface horizon half-angle, horizon slant range and the minimum number of
equally-spaced satellites that covers one ideal equatorial great circle down to zero-degree
elevation.

## Result

The two-body Moon-synchronous radius is 88,452 km from lunar centre, while the approximate Hill
radius is 61,524 km. The synchronous radius is about 1.44 times the Hill radius, so a simple
circular “lunar GSO” is rejected as the architecture baseline.

An 8,000 km shell has a period close to one Earth day, not one lunar sidereal month, and therefore
is not stationary over the Moon. In the ideal equatorial screen, raising the shell from 100 km to
5,000–8,000 km reduces the zero-margin satellite count from ten to three while increasing horizon
slant range and one-way propagation.

The generated record is [`results/S022_lunar_orbits.json`](../results/S022_lunar_orbits.json).

## Boundary

The count is not a global constellation design. It excludes poles, terrain masks, minimum
elevation, link budgets, capacity, plane phasing, eclipses, failures and station keeping. Hill
radius is only a first stability screen. Real lunar communications architectures can use
elliptical, frozen, resonant or multi-body trajectories near libration regions; those require
trajectory propagation and contact analysis rather than circular-shell intuition.
