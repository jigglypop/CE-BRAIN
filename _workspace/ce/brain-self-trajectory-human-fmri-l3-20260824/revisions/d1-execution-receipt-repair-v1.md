# D1 fail-closed receipt repair

Status: COMPLETE

The first real D1 attempt stopped before any model outcome but exposed a failure-path defect: the exception path did not write a receipt. The first repair wrote `artifacts/d1-receipt.json` with SHA-256 `b9ba7c105f691056c0983749b9b8e0d954bf7c94e0144f948c69957902096d71`, but that minimal receipt preserved only the zero-accepted-pair stop and discarded the already-computed range/QC diagnostics.

`revisions/d1-receipt-minimal-v1.json` preserves those exact minimal contents. The second repair changes no signal transform, QC cutoff, split, feature, model, or outcome rule. It only retains every D1 pair's exact-range receipt and QC summary in the fail-closed receipt. D1 remains the only permitted signal split; D2/C1/C2/C3 remain unopened. A nonzero process exit is retained for `D1_FAIL_CLOSED`.
