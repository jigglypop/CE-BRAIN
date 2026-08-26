# Structural pivot result: matched intervention twins

Status: COMPLETE

Decision: `TWIN_STRUCTURE_CONFIRMATION_STOP`

The independent fresh-seed confirmation recovered every expected class in all
84 replicates. A/B/C/F/G passed validation selection, twin-contrast prediction,
analytic identity, finite receipt and equal-arm gates. D/E also passed expected
selection 12/12, twin NRMSE, identifiability and receipt gates.

The frozen D/E state-pairing gate failed:

- D: permutation $p\le0.01$ in 5/12, required 10/12;
- E: permutation $p\le0.01$ in 0/12, required 10/12.

E's median selected twin NRMSE was `0.05973076849`, but its pairing advantages
were on the order of $10^{-9}$ and centered around zero. This means the selected
operator predicted the average intervention contrast accurately without
recovering which initial-state twin produced which contrast. D had positive but
insufficiently replicated pairing advantage.

Independent mathematics and status audits verified the manifest, result receipt,
all 84 aggregates, 5,376 unique common-random receipts, 10,752 unique arm hashes,
zero split/confirmation overlap and unchanged sealed bytes. No arithmetic,
permutation-direction, serialization or implementation defect was found.

Receipts:

- manifest SHA-256:
  `4310f873f31d083128fb22226ee6c4c318bd25c2f0b532a49884f11240c3650f`;
- result SHA-256:
  `645a117c1441f8d666b1bba8aded0ffef42b556ac9e471bd5bb222c98a1f7048`.

The parent Stage 0 STOP remains unchanged. Stage 1 is not authorized. This route
may not be retuned or relabeled. A successor must change the state-persistence or
intervention seam so state-specific contrast variation is present at stimulation,
and must preserve this result as a negative witness.
