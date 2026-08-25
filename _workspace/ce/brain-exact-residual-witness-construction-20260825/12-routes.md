# Routes

Status: COMPLETE

| Route | Decision | Reason / reopening condition |
|---|---|---|
| Exact Gauss--Jordan over $\mathbb Q(i)$ | SELECTED | Fully deterministic, exact, already compatible with normalized predecessor matrices. |
| Fraction-free Bareiss inversion | OPEN OPTIMIZATION | May reduce coefficient growth but adds no claim strength. Reopen for demonstrated performance need. |
| Float solver followed by bounded rational rounding | OPEN | Needs a frozen rounding denominator/error contract and a residual proof for the rounded output. |
| Diagonal weighted norms | OPEN | Requires predeclared weights, condition reporting, and proof translating the weighted inverse bound back to the physical norm. |
| Post-hoc weight search after observing failure | REJECTED | It changes certificate geometry and invites target-dependent selection without a frozen rule. |

