# Stage 0 result validation

Status: COMPLETE

## Mechanical validation

- Focused suite before sealing: `6 passed in 0.87s`.
- Contract and lane checks: `OK contract`, `OK lanes`.
- Manifest SHA-256 recomputation:
  `cadaefa5d746146967c6772a59b1ee5141fbed79b8d804c783b3775c62f9f12a`.
- Result SHA-256 recomputation:
  `44d059d3b0786b37738782d74a406eac3f77c46ee9286f72f449fc0700c38ab2`.
- All 14 sealed input hashes still match.
- Population is exactly 84 unique world/replicate identities; every selected
  descriptor has a valid serialization hash and every row reports unseen opened
  after selection.
- Independent recomputation agrees with the stored aggregate.

## Frozen gate outcome

| World | Expected/wins | Median margin | Median unseen | Persistence | Permutation | Pass |
|---|---:|---:|---:|---:|---:|---:|
| A | R 12/12 | 0.002439 | 0.146407 | 12/12 | 12/12 | yes |
| B | G 12/12 | 0.005768 | 0.197456 | 12/12 | 12/12 | yes |
| C | F 12/12 | 0.031840 | 0.116952 | 12/12 | 12/12 | yes |
| D | S 12/12 | 0.062175 | 0.301197 | 12/12 | 12/12 | yes |
| E | O 12/12 | 0.003758 | 0.474156 | 12/12 | 9/12 | **no** |
| F | O 12/12 | 0.038909 | 0.386921 | 12/12 | 12/12 | yes |
| G | O 12/12 | 0.040997 | 0.174069 | 12/12 | 12/12 | yes |

World E permutation failures are replicate 0 `0.02812945125`, replicate 3
`0.02876192819`, and replicate 6 `0.02454216750`, against the frozen `<=0.02`
criterion. The required frequency is at least 10/12; the observed frequency is
9/12. Independent mathematics review found no arithmetic, serialization,
selection, or hash defect.

Mechanical audit gate: PASS. Scientific gate:
`STAGE0_STRUCTURE_DISCRIMINATION_STOP`. `stage1_authorized=false`.
