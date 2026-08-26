# Implementation

Status: COMPLETE

Runtime: `reality_stone/python/reality_stone/clarus/verified_signed_conformal_interval_defective_edge_rank.py`.

Test: `tests/test_verified_signed_conformal_interval_defective_edge_rank.py`.

The runtime computes rather than trusts content hashes, verifies strict Ed25519, and
does not instantiate the conformal/rank certificate before cryptographic success.
