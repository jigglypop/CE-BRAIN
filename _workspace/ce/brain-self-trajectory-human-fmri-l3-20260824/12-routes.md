# BA-SELF1-L3 우회 경로 — revision 2, 실제 EEG 우선

Status: COMPLETE

Contract SHA-256: `2b08c0fd5eb69ae6f3d096a6542e248b6d2b69da985f90c7d06071e0690be50e`

## 공통 경계

실제 EEG의 관측된 현재값·공변량을 조건부로 한 방향 있는 과거 요약의 held-out future-prediction만 묻는다. 자아·의식·무한차원·해마 주소는 식별하지 않는다. BA-SRM multipatch input/rank STOP을 threshold/seed/endpoint 변경으로 재포장하지 않는다. 각 후속 후보는 다른 measurement transform, mechanism 및 adverse falsifier를 가진 별도 contract여야 한다.

| 우선 | 후보와 상태 | 자유도 | 독립 kill | target-aware |
|---|---|---:|---|---|
| 1 | R1: current scalp-EEG area | `OPEN / math-ready` | $M_0=53$, $M_1=59<75$ at $d=4$; $A$ adds 6 per scalar output/24 joint | reverse, 20 shuffle, rest, subject-03 confirmation 중 하나 실패; $G_{task}<.02$ | no |
| 2 | R2: EEG microstate semi-Markov transition word | `BLOCKED_INPUT` | $K(K-1)$ for $K=3,4$: 6/12 | current microstate+dwell+input baseline에 held-out 이득 없음; shuffle에서도 이득 유지 | no, separate contract |
| 3 | R3: causal multiband phase-amplitude directed history | `BLOCKED_INPUT` | fixed 3 bands, retained $r\le4$: predeclared family 최대 12 | reversed lag/input-history, volume-conduction control에서 이득 유지 | no, separate contract |
| 4 | R4: EEG-to-sealed-fMRI cross-modal prediction | `BLOCKED / fMRI sealed` | EEG path coefficients $\le24$ times independently fixed ROI count | motion/physiology/current EEG baseline에 못 이김; target-aware ROI/lag | no, new run |

## R1 — current scalp quotient

Baseline은 current state, local derivative, start/end, length/energy, increment mean/covariance/central $m_3,m_4$/coordinate range, word, condition을 포함한다. session은 predictor가 아니며 leave-one-session-out split과 bootstrap strata로만 사용한다. $d=4$에서 exact count는 $p_0=53$, $p_1=59<75$다. session dummy를 제거해 previous zero-variance/intercept-collinearity P0는 해소됐다.

R1의 수학적 준비 상태는 구현 또는 biological result가 아니다. fixed reverse, 20 fixed shuffles, matched rest, independent sub-03 C3와 fail-closed QC 중 하나가 실패하면 result claim을 kill한다. R1이 endpoint에서 실패하면 same signature의 threshold·bootstrap seed·window 변경 재시도는 금지된다.

## R2 — discrete microstate sequence

Calibration-frozen $K\in\{3,4\}$ microstate, current state, dwell, input을 가진 first-order semi-Markov baseline에 past transition word를 추가한다. Smooth area와 다른 discrete transition/dwell mechanism이며 label is gauge이므로 label-independent code를 receipt에 남긴다. held-out transition likelihood 이득이 없거나 order shuffle에서도 유지되면 kill한다. $K$나 word length를 endpoint 뒤 늘리면 target-aware tuning이다.

## R3 — causal multiband history

Causal FIR bank의 fixed low/beta/gamma-like band coordinates에서 current phase/amplitude·input baseline에 one predeclared lagged directed coupling을 더한다. Noncausal Hilbert는 금지한다. volume conduction/common-reference/scanner residual 대조와 reversed lag/input-history가 필수다. 실패하면 band/lag menu 확대는 허용되지 않는다.

## R4 — independent modality check

현재 fMRI는 sealed다. 후속 run에서만 independently fixed atlas ROI와 lag로 EEG history가 current EEG·motion·physiology를 넘어 future fMRI를 예측하는지 묻는다. ROI/lag/preprocessing을 EEG result 뒤 선택하면 즉시 kill이다. 성공해도 cross-modal prediction일 뿐 neural mechanism이나 self/consciousness 증거는 아니다.
