# Validation

Status: COMPLETE

```text
.codex\\hooks\\python.cmd python -m compileall -q examples\\brain\\ba_obs_hpc7_endpoint_recovery.py
.codex\\hooks\\python.cmd pytest tests\\test_ba_obs_hpc7_endpoint_recovery.py -q
```

Result: `4 passed in 4.01s`. Tests use the real frozen predecessor witness and
result but write only temporary successor artifacts. They cover frozen-content
recovery, prior refusal, terminal/execution-lock drift, validator failure, and
the no-validator/no-producer path sentinel. Actual default recovery was not run.

Revision 1: `5 passed in 10.46s`; this covers the orphan-receipt counterexample
and pair verification. The refrozen executor/test hashes are
`78e606f46947bc9658a1e4f7c508fe3f7762c77ab81f0ae17d260ade1674e8d5` and
`bb12538f619f4ef762081708c2110d4701ce37e84b99cf39b95d0752fbed909a`.

Revision 2 switches to immutable `validator_precomplete.json` and
`validator_complete.json`; final code/test hashes are recorded in the frozen
execution lock. Default status is expected to report `PENDING` with a nonzero
exit until a separately authorized transaction is executed.
