# Twin confirmation metrics

Status: COMPLETE

Primary metrics are expected validation winner frequency, median winner twin
NRMSE, D/E blockwise permutation p-value frequency, A/B/C/F/G linear-contrast
identity, and equal-arm adverse-control identity.

For D/E, the Monte Carlo randomization p-value uses 999 independently
hash-derived draws from the full product of eight uniform within-block
permutation groups. Fisher--Yates draws may contain fixed points and repeat.
Smaller permuted loss than paired loss is at least as extreme against the
one-sided pairing hypothesis. Ties count against it. No normal approximation is
used. NRMSE flattens `(block,twin,time=2..63,node)`.
