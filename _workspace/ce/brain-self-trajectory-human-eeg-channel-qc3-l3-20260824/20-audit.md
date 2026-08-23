# BA-SELF3-L3 audit: channelwise affine-invariant QC

Status: COMPLETE  
Contract SHA-256: `765c54ee2b20006619b3059c68ec3a5d1a3f007381f6d89593c597015ac41fce`  
Sources SHA-256: `a4be903d20a0f6e1391cde907c7f727b8804b62cd6ace02ab9be1fd9572012a7`  
Math SHA-256: `87778e0738961a7c8b49004b01684f55b92e35368fb06c6a457625094232ec02`  
Routes SHA-256: `041b0bcf1c58dc8d49437819d776647520ba1c50c627a7b131cc6bf5f03afad9`

## Gate decision

Gate: PASS

The frozen R2 route is internally coherent and has no P0 blocker. The audit does not open a signal endpoint and does not promote the state/path hypothesis. P1 limitations are retained as claim restrictions and are not reasons to block the apparatus route.

## P0/P1 findings

### P0 — none

- The contract, source lane, math lane, and route lane agree on R2: per-channel temporal-median residual and first-difference robust scales, with maximum dimensionless scores and explicit nonfinite/zero-scale rejection (`00-contract.md` §4; `11-math.md` §§1–2; `12-routes.md` Decision).
- The affine statement is exact for every finite channelwise (a_c\ne0) and offset (b_c): (Q_A^{ch}(X')=Q_A^{ch}(X)) and (Q_D^{ch}(X')=Q_D^{ch}(X)). The proof handles negative gain through absolute scale and the difference score removes the offset (`11-math.md` §2).
- The claim is correctly limited to fixed channelwise affine changes. The source and math lanes explicitly exclude time-varying gain, montage mixing, saturation/clipping, broad common artifacts, and electrode failure as removed or identified causes (`10-sources.md` Physical interpretation; `11-math.md` §3).
- The prior BA-SELF1 absolute-QC D1 failure and BA-SELF2 common-gain failure are treated as apparatus-only, with no model endpoint. BA-SELF1 records 0/32 retained; BA-SELF2 records 13/32 retained (8/16 and 5/16), so neither is used as a biological result (`10-sources.md` Pinned predecessor evidence; `00-contract.md` §1).
- B1 allocation is signal-blind and arithmetically consistent: 32 pairs total, 16 per session, leaving D2-M at 57/43 and 100 pairs (`12-routes.md` Signal-blind B1; `11-math.md` §4). Word-coverage and allocation-receipt requirements are explicit pre-gates; failure is `APPARATUS_INVALID_DESIGN` before any model access.
- B1 is prohibited from opening (z), target, path feature, losses, fitted coefficients, or model selection. The receipt must state `model_outcome_opened=false` (`12-routes.md` Signal-blind B1 and Required receipts). The prior D1 target-awareness/burn boundary is explicit: D1 was QC-only and excluded from B1/D2-M.
- D2-M has 57/43 pairs and therefore at least 30 per session; the contract’s (2N>p_1=59) design guard is stated as a guard, not as a claim of full-rank OLS. Ridge/SVD and fold-local conditioning checks remain required (`00-contract.md` §6–§7; `11-math.md` §4).
- The no-go is correctly scoped: finite history can be represented as an augmented instantaneous state, while scalp EEG identifies only an observation quotient. Thus a future ordered-history gain cannot decide whether self is ontologically a state or a path (`00-contract.md` §8; `11-math.md` §5; `12-routes.md` Claim ceiling).

### P1 — retained limitations

- R2 is measurement QC, not a neural or physiological invariant. Within-channel robust scaling can mask an artifact that inflates its own scale; montage mixing, time-varying gain, clipping, and broad artifacts can pass or fail for reasons unrelated to neural quality. Raw diagnostics and all scale failures must remain in receipts (`10-sources.md` Physical interpretation; `11-math.md` §3).
- B1 is held-out-window apparatus transfer, not independent replication: its `sub-02` recording was signal-seen for predecessor QC-only checks, and B1/D2-M share recording-level dependence. This prevents population or mechanism claims (`10-sources.md` B1/D2 independence status; `12-routes.md` Signal-blind B1).
- The 32 B1 pairs are 64 windows, but pair-level acceptance is the unit for the 24/32 and 12/16 thresholds. D2-M’s session-level minimum and word-coverage checks must be reported separately; windows must not be counted as independent subjects (`11-math.md` §4; `12-routes.md` Kill and resume rules).
- The (d\in\{2,3,4\}) rank is an observed quotient rank candidate after fold-local whitening, not the dimension of the brain, consciousness, or a Riemannian manifold. The claim ceiling explicitly excludes infinite dimension, neuron-wise edge strength, hippocampal hashing, consciousness, and self ontology (`00-contract.md` §6 and §8; `10-sources.md` Claim ceiling).

## Required receipt checks before any endpoint

1. P0/A0: source/header lock, exact 206 range/Content-Range/ETag/payload hash, parser and filter hashes, 63-channel geometry, allocation hash, zero-scale outcomes, negative-gain/offset synthetic invariance, and adverse-artifact checks.
2. A1/A2: every window’s (Q_A^{ch},Q_D^{ch}), calibration list, frozen median-plus-six-MAD cutoffs, and accepted/rejected reasons.
3. B1: all trial hashes, old/new splits, ordering key and algorithm version, session/word counts, 32-pair and 64-window accounting, acceptance counts, and `model_outcome_opened=false`.
4. D2-M: per-session QC counts, (2N>59) guard, rank/conditioning, selected menu, losses, reverse/shuffle controls, and no reuse of B1 for model selection.
5. C1/C2/C3: sealed `sub-03` provenance and stage-specific futility/final-confirmation receipts; no early opening or post-hoc route change.

## Validation evidence

- Dimensionless standard checks: 19 passed in 0.34 s; checker exit code 0 (recorded in the run validation evidence).
- The audit is a document/claim coherence gate. It does not substitute numerical endpoint validation, and no raw EEG signal was opened by this audit.

## Claim disposition

The active empirical claim remains `[예측]`/`[미완성]`: ordered history may improve held-out temporal prediction beyond the matched observed-current-state baseline under the declared EEG measurement model. A result, if later obtained, remains within-dataset and cannot decide the ontology of self. No consciousness, AGI, infinite-dimensional, neuron-level, or population claim is active.

