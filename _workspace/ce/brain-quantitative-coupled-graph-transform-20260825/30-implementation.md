# Implementation

Status: COMPLETE

Added `quantitative_coupled_graph_transform.py`. The dependency-free exact-rational gate normalizes base/fiber cross-Lipschitz constants, computes $q$, base fixed-point factor, $\alpha$, tube/slope margins, the coupled transform factor $Q$, its strict margin, robust-interior status, and the supplied graph dimension.

Base invertibility, tube invariance, slope invariance, and transform contraction have separate failure codes. The transform factor is withheld when $\alpha\le0$. No trajectory fitting or smooth-manifold code was added.

