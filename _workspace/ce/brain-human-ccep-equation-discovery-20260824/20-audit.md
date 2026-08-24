# BA-OBS-DISC1 pre-implementation formal audit

Status: COMPLETE

Gate: PASS

## Snapshot audited

- `00-contract.md`: 15식 grammar, endpoint-blind 24/48/39/40 split, sequential barrier;
- `10-sources.md`: cable/Green/heat/delay/reference 및 official dataset source;
- `11-math.md`: conditional semigroup, dimensionless audit, finite-readout no-go;
- `12-routes.md`: selected/killed/deferred route와 claim ceiling;
- direct predecessor BA-OBS-ID3 `40-final-report.md`.

이 판정은 실제 endpoint 결과를 보지 않은 stable pre-implementation snapshot에 대한 것이다.

## Formal-status ledger

| item | status | audit finding |
|---|---|---|
| $C\dot v=-(L_g+J_{\rm ion})v+Bu$ | **[공리: 국소 모델 선택]** | passive/operating-point short-window approximation으로 source-grounded다. 실제 whole brain의 고정 선형법칙으로 승격하지 않는다. |
| $v(t)=e^{-C^{-1}At}C^{-1}Bq$ | **[조건부 정리]** | 고정 finite stable linear system 가정 아래 정확하다. |
| observed heat/cable/delay/anisotropy/direction candidates | **[경험식 후보]** | 물리 grammar는 근거가 있으나 실제 적합·예측 지위는 D0 이후에만 생긴다. |
| $x=t/50\mathrm{ms}$, $r=\ell/50\mathrm{mm}$ 및 exp/log core | **[산출: 무차원 감사]** | 모든 core argument가 무차원이다. focused checker 19 tests pass. |
| fitted $q$ | **[정의: effective kernel-shape exponent]** | topological/neural/conscious dimension이 아니다. |
| distance-stratified salted split | **[산출: metadata-only allocation]** | signal-independent이며 four-stage distance ranges가 겹친다. Raw bytes는 과거 traversal되었지만 151 pair endpoint는 선행 run에서 계산되지 않았다. |
| source-cluster interval | **[분석자 규칙]** | shared stimulation trial dependence 때문에 pair-iid interval보다 적절하다. subject/population uncertainty를 제공하지 않는다. |
| D0 result | **[미완성]** | endpoint unopened; selection evidence일 뿐 독립 confirmation이 될 수 없다. |
| D1/D2/D3 results | **[미완성/예측 예정]** | prior-stage fit을 고정한 순차 held-out prediction으로만 열 수 있다. |

## Gate checks

### Source and measurement

PASS. Exact S3 object identity와 metadata lock이 있으며, dataset DOI family citation과 v1.0.2
object identity의 역할을 분리했다. Reference/volume-conduction nuisance를 neural dynamics와
분리했고 bipolar를 primary, contact-mean을 matched control로 둔다.

### Mathematics and dimensionlessness

PASS. Heat-kernel truncation, generalized exponent, delay와 anisotropic metric proxy의 모든
exp/log argument가 고정 scale로 정규화되었다. Nonlinear multi-start/Jacobian/boundary gate와
$x'\le0$ infeasibility가 local-minimum/floor rescue를 막는다.

### Leakage and statistics

PASS. D0 안에서만 구조를 선택하고, D1/D2를 통과한 뒤 numerical coefficients만 다음 stage
전에 누적 refit한다. Failure 뒤 같은 stage로 구조를 바꾸지 않는다. Geometry tuple은
joint-permute하고 primary interval은 actual source sites를 equal-weight cluster resample한다.

### Claim ceiling

PASS. 가능한 가장 강한 문장은 single-subject observed CCEP energy의 MNI-conditioned
held-out prediction improvement다. Ambient/infinite-dimensional metric, axonal geodesic,
population, consciousness, self, hippocampus와 AGI 주장은 금지되어 있다.

## Non-blocking P2 notes carried into implementation

1. Dataset DOI는 family citation이며 exact derivative identity는 S3 VersionId/ETag/hash다.
2. D0 cross-validation은 selection 기준이지 독립 유의성 증거가 아니다.
3. 실제 D0 전에 source lock, analytic/null/common-reference fixtures, dimensionless check와
   downstream-receipt barrier를 executable하게 통과시켜야 한다.
4. BIEXP도 H-DELAY와 마찬가지로 관측 bin의 $x'\le0$을 floor로 숨기지 않고 infeasible로
   처리한다.

## Authorization

`Gate: PASS`. Implementation/fixture/source-cache audit로 진행할 수 있다. 실제 endpoint는
fixture PASS 뒤 D0만 먼저 열며, 이후 stage는 계약 barrier에 따른다.

## Math-verifier revision 1/2 — pre-endpoint implementation parity

실제 source cache와 D0 endpoint를 열기 전 code audit에서 세 P1을 수정했다.

1. mean fit failure가 bipolar primary gate를 막지 않도록 mean을 reference diagnostic으로
   다시 분리했다.
2. downstream barrier fixture는 boolean을 적는 대신 격리 temporary path에서 같은
   `enforce_barrier`가 예외를 내고 receipt를 만들지 않는지 실행한다.
3. 구현에 사용한 $\beta$, $a/\kappa/\lambda$, BIEXP parameter의 유한 bounds를 계약 §7에
   숫자로 동결했다.

이 revision 시점에 source-cache와 D0/D1/D2/D3 receipt는 없고 실제 response endpoint는
열리지 않았다. 따라서 split, 식, window 또는 threshold의 결과후 조정이 아니다.
