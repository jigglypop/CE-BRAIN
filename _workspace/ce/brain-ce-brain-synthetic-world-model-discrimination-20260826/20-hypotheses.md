# Stage 0 hypotheses

Status: COMPLETE

Primary falsifiable hypothesis: the fixed candidate family selects the known
generating class under held-out intervention, not merely on training fit.

Expected winners are `A:R`, `B:G`, `C:F`, `D:S`, `E:O`, `F:O`, `G:O`.
The exact frequency, margin, unseen-error and persistence-improvement gates are
those in `00-contract.md`. A wrong class is a benchmark failure even if its
training reconstruction is lower.

Alternative outcomes remain admissible:

- A classified as G: symmetric simplification is not identifiable;
- B classified as R: directionality is not recovered;
- C classified as G/O: signed direction cost is not separately identifiable;
- D classified as O: switching is absorbed by a general operator;
- E classified as S/G: nonlinear recurrence is underidentified;
- F/G not classified as O: hidden/history state is not recovered.

No result is evidence about real-brain geometry.
