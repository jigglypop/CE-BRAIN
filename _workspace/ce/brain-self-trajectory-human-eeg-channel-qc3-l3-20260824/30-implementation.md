# BA-SELF3 channelwise R2 apparatus implementation

Status: COMPLETE

Scope: apparatus only. A1/A2/B1 are complete; no model stage opened.

Implementation is confined to `artifacts/channelwise_qc.py` (SHA-256
`e3713b2b9533d7523a903901c04808901eba79724c7b4822d2673877b72e8f0b`).
It contains no quotient coordinate, target, path feature, loss, or model
code. Before a signal stage it verifies the frozen current-contract SHA-256
`765c54ee2b20006619b3059c68ec3a5d1a3f007381f6d89593c597015ac41fce`, the
sealed trial-manifest and A0 receipt, and BA-SELF2 apparatus SHA-256
`9740d04ab8198a403d94d9c825b1a8f7279c159854fb6403f84da8c4a48685a4`.
The verified BA-SELF2 module in turn locks the BA-SELF1 BrainVision reader.
At a signal stage BA-SELF1 alone supplies range access, parsing, causal filter,
and the old absolute diagnostic; BA-SELF2 alone supplies the R1 matched
diagnostic. Thus neither matched diagnostic can substitute for or block R2.

For each finite $126\times63$ post-filter window the implementation uses the
contract definition directly: it subtracts each channel's temporal median,
uses that channel's $1.4826\operatorname{MAD}$ scale, and takes
$Q_A^{\rm ch}=\max_{t,c}|R_{tc}/s_c|$. It analogously centres the one-step
difference channelwise and returns $Q_D^{\rm ch}=\max_{t,c}|D_{tc}/r_c|$.
Any nonfinite value or nonpositive/nonfinite channel scale is a hard failure.
Old absolute QC and BA-SELF2 R1 are receipt-only matched diagnostics and never
enter a gate. A2 freezes exactly median plus six *unscaled* MAD from 64
channelwise scores.

The default command is offline preflight. `--execute` is required for A1, A2,
or B1 range access. Receipt writing is atomic; all ordinary exceptions produce
an `APPARATUS_INVALID` receipt with both endpoint flags false and only the
stage-accurate unopened splits. B1 requires a sealed allocation and A2 receipt,
reads only its 32 allocated pairs, records exact range receipts plus QA/QD and
reasons, and returns a nonzero status unless at least 24/32 pairs and 12/16 in
each session pass. It never opens a model endpoint.

P0/A0 completed without signal access:

```text
.codex\hooks\python.cmd python ...\channelwise_qc.py --stage A0-ALLOCATION ... --output artifacts\b1-allocation.json
```

The resulting allocation receipt is `A0_ALLOCATION_PASS`, SHA-256
`91fff95baa5ff309d2dda23e4206da8f7f04fd6341c6b1012b2dbb82bb95f1c2`, with
`signal_accessed=false`. It records every D2 trial hash, SHA-256 ordering key,
session, word, and old/new split. It deterministically assigns B1 16/16 pairs
and retains D2-M 57/43 pairs, while all eight word levels occur in each
D2-M session. Every preflight/allocation receipt explicitly records `model_outcome_opened=false`,
the pinned SELF1 BrainVision hash, and fixed filter geometry alongside
`model_outcome_computed=false`.

## Executed apparatus stages

A1 completed with receipt `artifacts/a1-channelwise-receipt.json`, SHA-256
`219aabf504deb6c16db719fb9f19da9a09a5f464da4791ce3735f378bbfe21e`:
`A1_APPARATUS_PASS`, 16 exact windows, and zero hard-domain rejects.

A2 completed with receipt `artifacts/a2-channelwise-receipt.json`, SHA-256
`8270f31272ff21814c0c0ed5614d74dd29acd8f2045bc645baaa68e41a4d28d8`:
`A2_APPARATUS_PASS`, 64 exact windows, zero hard-domain errors, and frozen
channelwise cutoffs $Q_A^{\rm ch}=9.610396697909561$ and
$Q_D^{\rm ch}=11.350540283998544$.

B1 completed with receipt `artifacts/b1-channelwise-transfer-receipt.json`,
SHA-256 `d3b7319804206b3ddcc6f35260706dfe4d4b961e0053db80c1c16c9569ead362`.
Its status is `APPARATUS_INVALID_CHANNELWISE_QC_TRANSFER`: 17/32 accepted
pairs, with 10/16 in `ses-01` and 7/16 in `ses-02`, below both frozen transfer
requirements. Window failures were 6/32 in `ses-01` and 11/32 in `ses-02`;
pair reasons were both $Q_A$ and $Q_D$ for 6 pairs, $Q_D$ only for 8, and
$Q_A$ only for 1. Both scientific and model outcome flags are false. D2-M and
C1/C2/C3 remain sealed. This is an apparatus-transfer failure only, not a
result about the path equation, self, or consciousness.
