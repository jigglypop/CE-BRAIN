# Implementation

Status: COMPLETE

Added `verified_weighted_interval_residual.py`. It parses one exact positive diagonal weight vector, normalizes its common scale, applies the exact similarity to node matrices, witnesses, and componentwise uncertainty, reuses the predecessor's node residual checker, divides the transformed singular lower by the exact diagonal condition number, and selects the better rigorous original-coordinate lower per node.

The original chord and projector geometry are retained. Weighted node success, full-circle failure, and full-circle success have distinct statuses. The base unweighted result remains embedded and cannot be overwritten by a worse weight.

