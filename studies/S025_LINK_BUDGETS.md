# S025 — RF/optical class link budgets

`python -m gatewaycx.link_budgets` evaluates two RF and two optical architecture classes. RF uses
free-space loss and a C/N0-to-Eb/N0 margin, then injects 6 dB additional loss. Optical uses aperture,
beam divergence, range, photon energy and a Gaussian pointing penalty at four pointing errors. A
separate sensitivity combines optical weather availability with RF fallback.
The acquisition sweep charges 5, 20, 60 and 180 seconds against a declared 600-second contact and
reports the resulting hybrid optical/RF contact yield. It is a terminal-class timing sensitivity,
not a claim that acquisition control or flight terminal dynamics have been reproduced.

The result is [`results/S025_link_budgets.json`](../results/S025_link_budgets.json). Inputs are not
vendor specifications. A paper margin does not prove acquisition, availability or hardware
performance; the model exists so class assumptions can later be replaced by controlled evidence.
