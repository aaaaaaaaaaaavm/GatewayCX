# S012: Predictive prepositioning with forecast error cost

## Concept transfer

Recommendation systems estimate future demand, edge caches move likely objects toward users, and
spare-parts logistics puts scarce inventory where a failure may occur. The transferable mechanism
is not "use AI". It is to make a forecast, reserve capacity for non-negotiable stock, optimise the
remaining inventory against a hard budget, and account for what the forecast got wrong.

GatewayCX applies that mechanism before an Earth–Moon contact interruption. The predictor may be a
neural network later, but it produces only probabilities. A deterministic allocator owns the cache
budget and always installs the declared essential set first.

## Question

Does a forecast-driven policy deliver more useful lunar cache content than a simple popularity
baseline without spending contact capacity on unrequested objects?

## Method

The synthetic case has a 900 MB cache budget, of which 300 MB is reserved for emergency maps and
medical references. Six optional objects compete for the remaining space. Each object has a size,
a number of remote requests avoided if used, a realised outcome, and probabilities from three
forecast inputs.

For each policy, an exhaustive search maximises declared expected utility. The utility values
avoided 2.564-second round trips and charges 0.75 seconds of opportunity cost for each unused
100 MB. The oracle sees the outcome and exists only as an upper bound.

```bash
python -m gatewaycx.preposition
```

## Result

| Policy | Prefetched | Useful | Wasted | Remote requests avoided | Brier score |
|---|---:|---:|---:|---:|---:|
| Essential only | 300 MB | 300 MB | 0 MB | 14 | n/a |
| Popularity only | 850 MB | 850 MB | 0 MB | 27 | 0.104175 |
| Calibrated input | 850 MB | 850 MB | 0 MB | 27 | 0.052038 |
| Overconfident input | 850 MB | 400 MB | 450 MB | 20 | 0.349762 |
| Oracle upper bound | 850 MB | 850 MB | 0 MB | 27 | 0 |

Lower Brier score is better; it is reported here as an outcome score, not proof of calibration.

The calibrated input selects the same objects as the oracle in this realised trace. It does not,
however, deliver more useful bytes or avoid more requests than the simple popularity policy. The
overconfident input fills 450 MB with an unrequested entertainment bundle and avoids seven fewer
remote requests than popularity.

The result is therefore a failed admission test for a learned policy, not evidence that predictive
prepositioning is ready. A more complex predictor must beat the simple baseline across held-out,
time-ordered demand traces and under forecast drift before it earns operational authority.

## Architecture consequence

The predictor/allocator interface should carry probability, forecast age, model identity and
calibration evidence per immutable object. The allocator—not the predictor—enforces:

- an essential-content reservation;
- contact and storage budgets;
- expiry, trust and privacy eligibility; and
- a record of useful, unused and evicted bytes after outcomes arrive.

This is the useful connection between neural networks and cislunar networking: prediction is a
replaceable input to a measurable inventory decision, not the decision-maker and not a safety
claim.

## Boundary

All demand, probability, size and cost inputs are synthetic. Calling one input "calibrated" does
not establish calibration from one batch. No neural network is trained or run. The study omits
privacy, encryption, expiry, multicast, cache churn and uncertain contact duration. Prefetching
moves traffic to a better time; it does not reduce the bytes required to populate the cache.
