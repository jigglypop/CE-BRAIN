# Real-data endpoint audit

Status: COMPLETE

Gate: PASS

Endpoint status: EMPIRICAL FAIL

The independent stable-snapshot audit verified the exact 12,967,760-byte asset
and SHA-256, train-only unit retention, development-only selection, held-out
mask, all-train-bin NMSE denominator, matched full-VAR selection, bootstrap
arithmetic and temporary-NWB deletion. No apparatus defect remains.

The final retained population contains 295 units. The affine candidate has
NMSE `0.9605287919`, versus `0.9610053891` for full VAR, `0.9605781411` for
base-only and `1.5758308630` for persistence. Its full-VAR improvement is only
`0.0496%`, with paired bootstrap interval `[-0.1140, 0.4095]`; both the frozen
1% and lower-bound-above-zero rules fail. Moreover,

$$
q=1.0955465>1,
\qquad
\kappa=3.9189690,
\qquad
q\kappa=4.2934127>1.
$$

Thus the positive affine-contracting-fiber biological bridge is falsified for
this session and measurement/model contract. Ordinary temporal predictability
survives, because persistence is much worse. This result does not falsify the
conditional mathematical construction and does not establish a biological
manifold, generator, metric or causal attraction.
