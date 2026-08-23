# BA-SELF3 channelwise R2 validation

Status: COMPLETE

Scope: apparatus only. A1/A2/B1 execution is complete; model validation did
not open.

Focused synthetic validation command:

```text
.codex\hooks\python.cmd pytest _workspace\ce\brain-self-trajectory-human-eeg-channel-qc3-l3-20260824\artifacts\test_channelwise_qc.py -p no:cacheprovider
```

Result: `10 passed in 0.93s` (Python 3.11.9, NumPy 2.4.6). The test source is
SHA-256 `32298856c0859b10ea9185ee74941c64096b3eaeca3b80335fbb6a754eb23328`.
The focused checks cover per-channel finite affine invariance with mixed-sign
gains and offsets, unit rescaling, explicit non-invariance to time-varying gain
and montage mixing, spike and step sensitivity, the disclosed broad-artifact
masking limitation, nonfinite/zero-scale fail-closed behaviour, the frozen
median-plus-six-MAD cutoff law, the pair/session transfer gate, deterministic
production allocation with eight-word coverage, and offline preflight/seal
ordering with stage-accurate unopened splits. A monkeypatched integration
check additionally proves that range/parser/filter and absolute diagnostic
calls target verified SELF1, while the R1 matched diagnostic targets SELF2;
no network is used by that check.
An additional real offline-preflight check asserts the audit-required
`model_outcome_opened=false`, pinned SELF1 hash, and fixed filter geometry.

The metadata-only allocation command then returned
`{"network_accessed": false, "status": "A0_ALLOCATION_PASS"}`. This is an
implementation check and a signal-blind split commitment, not neural evidence.
A1 and A2 then passed their real exact-range apparatus stages: A1 retained all
16 windows without a hard-domain reject, and A2 retained all 64 windows and
froze $Q_A^{\rm ch}=9.610396697909561$ and $Q_D^{\rm ch}=11.350540283998544$.
Their receipts and hashes are recorded in `30-implementation.md`.

B1 failed its frozen held-out-window apparatus transfer gate at 17/32 accepted
pairs (10/16 `ses-01`, 7/16 `ses-02`), below 24/32 and 12/16 per session. The
stage therefore closed as `APPARATUS_INVALID_CHANNELWISE_QC_TRANSFER`; D2-M
and C1/C2/C3 remain sealed. No endpoint, target, feature, loss, fitted
coefficient, model selection, path result, self claim, consciousness claim, or
biological mechanism claim was computed. This is a measurement/QC transfer
failure, not evidence for or against the path equation.
