# Componentwise residual/Krawczyk implementation

Status: COMPLETE

Added `verified_interval_residual.py` as a separate exact layer preserving the
complete predecessor tightening result.

For each of four supplied rational witness matrices it builds the normalized
nominal node matrix, exact residual `I - B*A0`, outward magnitude matrices,
componentwise uncertainty product, both contraction norms, witness induced
norms, Banach inverse bounds, spectral inverse square-root bracket, and node
singular lower. Only four passing nodes plus a positive exact chord correction
produce the full-circle status.

The output also exposes raw/normalized separation and resolvent, family-wide
rank status, the residual projector-motion bound, and optional nominal
quadrature/total errors. Witnesses are checked rather than trusted. No network,
dataframe, numerical linear-algebra package, file I/O, data, or scientific
endpoint is used.
