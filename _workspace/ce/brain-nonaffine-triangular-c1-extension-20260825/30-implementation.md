# Implementation

Status: COMPLETE

The existing C1 certificate already consumes only the uniform inverse bound $\mu$ and no affine matrix data. Its module scope was corrected to a triangular C1-diffeomorphism base. Added `sine_perturbed_base_inverse_lipschitz`, which accepts exact $a\in[0,1)$ and returns $(1-a)^{-1}$; invalid, float, Boolean, noncanonical, negative, and boundary inputs fail closed.

No coupled-base, local-domain, or higher-derivative behavior was added.

