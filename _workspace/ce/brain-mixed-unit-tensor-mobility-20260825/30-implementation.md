# Implementation

Status: COMPLETE

Added `physical_tensor_mobility.py`. It parses exact heterogeneous state scales, energy/time scales, a real rational mobility matrix, and a dimensionless gradient. It constructs $\widetilde M$ entrywise, rejects nonsymmetry, computes every nonempty principal minor exactly, distinguishes PSD/PD, and withholds dynamics/dissipation outputs on failure.

For passing tensors it returns normalized and physical coordinate velocities and normalized/physical model-potential dissipation. No tolerance symmetrization, eigenvalue approximation, biological default, or drift term was introduced.

