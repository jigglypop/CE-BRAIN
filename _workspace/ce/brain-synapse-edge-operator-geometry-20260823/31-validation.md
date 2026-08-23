# BA-SRM4 구현 검증과 봉인 상태

Status: COMPLETE

Date: 2026-08-23

이 문서의 `validation`은 코드·수치 무결성 검증을 뜻한다. 계약의
validation/development split outcome은 열지 않았으며, confirmation/test도 봉인 상태다.

## 1. 실행 정책

PowerShell policy를 우회하지 않았다. 수동 `.codex/hooks/run.cmd`가 내부적으로
`-ExecutionPolicy Bypass`를 사용한다는 사실을 확인한 뒤 더 이상 사용하지 않았다.

- Python: `.codex/hooks/python.cmd`
- status/gate: `%LOCALAPPDATA%\ce-research-core\release\ce-research-core.exe` 직접 실행
- selected interpreter: `C:\Users\dongh\AppData\Local\Programs\Python\Python311\python.exe`
- Python version: 3.11.9

## 2. focused validation

실행 명령:

```powershell
.codex\hooks\python.cmd python -m py_compile `
  _workspace\ce\brain-synapse-edge-operator-geometry-20260823\artifacts\prepare_discovery_dataset.py

.codex\hooks\python.cmd python -m py_compile `
  _workspace\ce\brain-synapse-edge-operator-geometry-20260823\artifacts\discover_edge_equation.py

.codex\hooks\python.cmd pytest `
  _workspace\ce\brain-synapse-edge-operator-geometry-20260823\artifacts\test_prepare_discovery_dataset.py `
  _workspace\ce\brain-synapse-edge-operator-geometry-20260823\artifacts\test_discover_edge_equation.py -q
```

결과: source compile PASS, `13 passed in 0.13s`.

검사 범위:

- predecessor group quarantine와 LIMS slice-specimen group atomicity;
- IC/VC typed channel 분리와 structural missingness;
- future pulse sentinel의 input 누출 방지;
- BLOB-free discovery-scoped SQL;
- group-atomic deterministic folds;
- robust scaler/missing imputation;
- interaction Jacobian finite difference;
- synthetic group-CV signal recovery;
- 3/5 stability-core와 interaction hierarchy;
- finite reference $d_{\rm eff}$ bound.

## 3. data receipt 재현

V2 dataset preparation은 11.1 GB pinned DB hash, source manifest hash, eligible manifest hash를
모두 다시 확인하고 9초 안에 완료됐다.

```text
status                         PASS_DISCOVERY_DATASET
database SHA-256               dbf19786...2d48c5
source manifest SHA-256        4ddb4a52...aa62c2
eligible manifest SHA-256      74d6d3b1...fd81c
selected sequences             1,383
event rows                     16,596
all outcomes predecessor-only  true
validation outcomes read       false
confirmation outcomes read     false
waveform BLOBs read             false
```

V2 split manifest에는 4,259개 unique LIMS slice-specimen group이 있고 한 group이 둘 이상의
assigned split을 갖는 충돌은 0이다. predecessor-contact 414개 group은 모두
`discovery-contaminated`다.

## 4. discovery equation 재현

V2 discovery equation은 약 13초에 완료됐다. ex IC→IC 168 groups와 in IC→IC 185 groups에만
적합했고 VC 6/4 groups에는 abstain했다. 5 outer × 4 inner group nesting을 유지했으며 모든
fold preprocessing과 ridge fit은 해당 training groups에서만 계산됐다.

discovery nested-OOF selector의 constant 대비 group-mean standardized MSE 차이는 ex
$1.8897\pm0.2658$, in $2.9795\pm0.5708$이었다. 이 값은 discovery 후보 생성 진단이며
development validation이나 confirmation 성능이 아니다.

## 5. 독립 감사

status auditor:

- Gate PASS;
- V2 grouping atomicity, old-eligible-only outcomes, IC/VC separation, VC abstention 확인;
- 5×4 nested group selection과 3/5 stability core 확인;
- validation/confirmation outcome 미접촉 확인;
- V1 artifacts를 `SUPERSEDED / DO NOT CITE`로 기록할 것을 요구했고 `30-implementation.md`에
  반영했다.

math verifier:

- P0 결함 없음;
- standardized-coordinate Jacobian과 $J^TR^{-1}J$ whitening 확인;
- ex/in pointwise rank 4와 rank $\le16$ 확인;
- frozen lambda grid에서 $d_{\rm eff}$ 단조성 확인;
- ex 50 ms trace는 tolerance $10^{-4}$에서 conditional hard-rank increment 0이지만
  coefficient 또는 모든 표현에서의 전역 redundancy로 확대 해석하면 안 된다고 판정;
- discovery $\Delta$MSE, rank, $d_{\rm eff}$를 biological state count, donor-held-out,
  validation 승리, infinite-dimension 또는 AGI evidence로 쓰는 것을 금지.

## 6. 검증 판정

구현·수치 검증: PASS.

과학적 상태: `[경험식][미완성]`, discovery-only.

validation/development status: `SEALED / NOT READ`.

confirmation/test status: `SEALED / NOT READ`.

다음 unlock은 frozen stability-core V2를 source-mechanistic baseline, constant, linear,
raw-RBF, time shuffle, clamp swap과 같은 LIMS slice-specimen validation groups에서 단 한 번
비교하는 것이다. 그 결과를 보기 전에는 식·항·split·target·threshold를 바꾸지 않는다.
