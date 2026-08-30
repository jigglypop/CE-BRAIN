# CE-BRAIN Stage 8 DANDI 001371 공식선택해독 R2 계약

Status: `PREREGISTERED / OUTCOME_BLIND`

기준일: 2026-08-31

## 변경 이유

R1의 단일 pre-window 평균차 축은 두 세션에서 held-out 선택감도를 확립하지 못했다. R2는 공식 논문 코드가 사용하는 `choice_binarized`, Poisson tuning curve, uniform prior, 0.2초 decoder bin에 맞춘다. R1 수치는 바꾸지 않는다.

## 고정 자료

- development 1: S29-211118
- development replication: S20-210519
- region: PFC primary, CA1 secondary
- official cell types: Pyramidal Cell, Narrow Interneuron, Wide Interneuron
- encoder trials: `update_type=1`, `correct∈{0,1}`, `maze_id∈{3,4}`
- random-state 21로 encoder trial 80% train, 20% held-out
- decoder update trials: `update_type∈{2,3}`, `maze_id=4`; DID는 correct만 사용

## 모델

- 선택값은 1=left(-1), 2=right(+1)로 고정한다.
- train trial 전체 시간에서 선택별 unit Poisson rate를 구한다.
- 0.2초 spike count의 두 선택 log-likelihood를 uniform prior로 비교한다.
- 수치안정을 위해 train rate에 `1e-6 Hz` floor만 둔다.

## 양성대조와 correction endpoint

- held-out delay-only trial은 trial 내 bin log-odds 합으로 최종 선택을 분류한다.
- 양성대조: balanced accuracy≥0.60, choice-label permutation 2,000회 `p<0.01`.
- update trial은 실제 `t_update` 기준 pre `[-1.0,-0.2]초`, post `[+0.2,+1.0]초`의 final-choice 정렬 log-odds 평균을 구한다.
- 주 endpoint DID는 `mean(post-pre|switch correct) - mean(post-pre|stay correct)`.
- final choice×시간 절반 strata 안에서 switch/stay를 2,000회 permutation한다.
- PFC에서 DID>0, permutation `p<0.01`, bootstrap 95% 하한>0을 요구한다.
- S29와 S20이 모두 PFC 문턱을 통과해야 `RAPID_CORRECTION_POISSON_CODE_ESTABLISHED_REPLICATED`다.

## claim ceiling

이 계약도 within-trial prospective-code correction만 검사한다. 이후 trial이나 day까지 남는 `v_C`, synaptic/geometry 변화, READ/WRITE 분리, chemistry gate는 검사하지 않는다.
