# CE-NPF 대체 생물자료 D3 NDNF 복잡규칙 재학습 결과 v1

## 판정

- 판정: `D3_NDNF_COMPLEX_RELEARNING_SPECIFIC_IMPAIRMENT_NOT_SUPPORTED`
- 입력·스키마·품질 게이트: 전부 통과, 40 strata, 10 paired mice.
- 사전 실행 설계감사: `PASS_TO_IMPLEMENT`.
- 독립 코드감사: 2건 모두 `PASS — ONE-SHOT ENDPOINT EXECUTION AUTHORIZED`.
- 사후 결과감사: `PASS`.
- 증거 지위: NDNF 활성화가 `A -> B`보다 `B -> A'` 재학습을 더 손상한다는
  사전고정 20-trial interaction은 방향은 양수였지만 exact 검정을 통과하지
  못했다. 이는 NDNF의 일반적 수상돌기 억제 기전이나 논문의 다른 endpoint가
  거짓이라는 판정이 아니다.

네 결합조건 가운데 세 방향조건은 통과했지만 one-sided exact sign-flip
`p < 0.05`가 실패했다.

| 사전고정 조건 | 값 | 통과 |
|---|---:|---|
| primary mean complexity interaction `> 0` | `+0.08` | 예 |
| exact one-sided `p < 0.05` | `0.3125` | **아니오** |
| mean Opto-Control in `B -> A' > 0` | `+0.10` | 예 |
| omission-inclusive mean interaction `> 0` | `+0.12` | 예 |

따라서 방향성 점추정이나 중앙값으로 exact 실패를 구제하지 않는다.

## 입력·실행 영수증

- 자료: Maristany de las Casas et al. 2026 G-Node,
  DOI `10.12751/g-node.etlk5k`.
- 논문: *Science* 392, `eadx4358`, DOI `10.1126/science.adx4358`.
- archive: 483,324,456 bytes, SHA-256
  `b9962e7760ac7299cc968fa4a23d2c965342d78abdded4f937a4081588f09ba3`.
- 계약: 10,151 bytes, SHA-256
  `e4bcde5224d5f8e9309bc84504a74f3e5edd67a71d573ecae6f0893951e9e690`.
- runner: 25,738 bytes, SHA-256
  `acf1bc5de75e8f98e37a0c25a9775af530e6e30facdff475fa1b49db09e2e6c7`.
- synthetic tests: 10/10 PASS; test SHA-256
  `db9ae13d5d3f79f61cc3dddf9d8f23f40d381aa322f96f91e12de863f12eb83b`.
- execution source lock SHA-256:
  `c5458ff69d9e2b5ce775944b2b8e2618ff87dbabf9c7bef69262271d957a33ba`.
- runtime: `C:\Users\dongh\AppData\Local\Programs\Python\Python311\python.exe`,
  Python 3.11.9, NumPy 2.4.6, SciPy 1.17.1.
- 실제 endpoint 실행: 잠금 확인 뒤 정확히 1회, exit code 0.
- 결과 JSON: 76,104 bytes, SHA-256
  `625e25206c165fd759d4aa8c9d7213392367bd6fd001115663ac8de3647c5b8b`.
- 결과 파일:
  `paper/6_뇌/국소회로_상태다양체_흐름_대응/repro/maristany_ndnf_relearning_v1_result.json`.

모든 stratum에서 primary eligible trial은 최소 22개, omission-inclusive
sensitivity eligible trial은 최소 23개였다. ZIP 129개 member의 CRC와 정확한
Control/Opto mouse 집합도 재확인했다.

## 고정 endpoint

각 mouse `m`, condition `c`, transition `t`에서 raw `Relearn`이 session 끝까지
new rule로 유지되는 terminal run의 첫 trial `s*`를 포함한다. 그 뒤 right
instruction 중 `Outcomes[:,0] in {0,1}`인 첫 20개 trial의 error rate는

\[
e_{mct}=\frac1{20}\sum_q(1-Outcomes_{q,0})
\]

이고

\[
d_{m,t}=e_{m,Opto,t}-e_{m,Control,t},
\qquad
D_m=d_{m,B\to A'}-d_{m,A\to B}
\]

로 고정했다. `DirOut`은 실제 raw에서 binary가 아니고 valid outcome과도 89회
불일치하므로 endpoint에는 쓰지 않고 source QC 교차표로만 보존했다.

## mouse별 결과

`e_C`, `e_O`는 각각 Control과 Opto의 primary error rate다. `D`는 primary
interaction, `tilde D`는 impulsive만 제외하고 omission을 error로 센 고정
민감도 interaction이다.

| mouse | `e_C_AB` | `e_O_AB` | `e_C_BA` | `e_O_BA` | `d_AB` | `d_BA` | `D` | `tilde D` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `NWO1` | 0.30 | 0.80 | 1.00 | 0.55 | +0.50 | -0.45 | -0.95 | -0.95 |
| `NWO3` | 0.50 | 0.20 | 0.80 | 0.80 | -0.30 | +0.00 | +0.30 | +0.30 |
| `NWO4` | 0.25 | 0.45 | 0.80 | 0.55 | +0.20 | -0.25 | -0.45 | -0.35 |
| `NWO5` | 0.55 | 0.45 | 0.55 | 0.95 | -0.10 | +0.40 | +0.50 | +0.85 |
| `NWO6` | 0.60 | 0.30 | 0.85 | 0.90 | -0.30 | +0.05 | +0.35 | +0.25 |
| `NWO9` | 0.35 | 0.35 | 0.65 | 0.85 | +0.00 | +0.20 | +0.20 | +0.40 |
| `NWO10` | 0.50 | 0.55 | 0.95 | 1.00 | +0.05 | +0.05 | +0.00 | -0.10 |
| `NWO11` | 0.25 | 0.75 | 0.45 | 1.00 | +0.50 | +0.55 | +0.05 | -0.10 |
| `NWO12` | 0.85 | 0.60 | 0.45 | 0.75 | -0.25 | +0.30 | +0.55 | +0.65 |
| `NWO13` | 0.65 | 0.55 | 0.80 | 0.95 | -0.10 | +0.15 | +0.25 | +0.25 |

## 추론

| 항목 | 값 |
|---|---:|
| `mean(D)` | `+0.08` |
| `median(D)` | `+0.225` |
| `D > 0` | 7/10 mice |
| `D = 0` | 1/10 mice |
| `mean(d_AB)` | `+0.02` |
| `mean(d_BA)` | `+0.10` |
| `mean(tilde D)` | `+0.12` |
| exact tail | 320/1024 |
| exact one-sided p | `0.3125` |

interaction error-count는
`[-19, 6, -9, 10, 7, 4, 0, 1, 11, 5]`였고 합계는 16이다. 7마리의 양성
방향에도 불구하고 두 큰 음성값 때문에 완전열거 귀무분포에서 관측합 이상인
배정이 320개였다. outlier 제외, 다른 창, rank test 또는 공급자 미공개 helper
추정으로 주판정을 바꾸지 않는다.

논문의 Figure 1H는 별도의 transition별 지표와 Wilcoxon 검정을 보고한다. 이번
결과는 `Outcomes` 기반 첫 20 valid right trials의 사전고정 difference-of-
differences이므로, 논문의 개별 transition 결과를 재현하거나 반박하는 검정으로
해석하지 않는다. “한 transition은 유의하고 다른 transition은 유의하지 않다”는
사실만으로 두 효과의 차이가 유의하다고 할 수도 없다.

## 세부식에 주는 실제 제약

사전 모형은

\[
\dot W_{ij}=\eta\,G_i\,\delta_t x_jy_i-\lambda W_{ij},
\qquad
G_i=\sigma(a_i-\beta n_i),\quad\beta>0
\]

에서 NDNF activity `n_i`가 학습 gate `G_i`를 낮춘다고 놓았다. 이 D3가 직접
시험한 행동 contrast를

\[
\Gamma=
\bigl(e_{Opto,B\to A'}-e_{Control,B\to A'}\bigr)
-\bigl(e_{Opto,A\to B}-e_{Control,A\to B}\bigr)
\]

라 하면 `hat Gamma=+0.08`이지만 `p_exact=0.3125`다. 따라서 이 자료로
`Gamma>0`이나 복잡도에 따른 `partial error / partial n_NDNF` 증가를 확인된
생물학 제약으로 채택하지 않는다. 위 가소성 gate 식은 후보식으로만 남는다.

유효계량

\[
g_\eta(z)=J_{F_\eta}(z)^\top\Sigma_\eta^{-1}J_{F_\eta}(z),
\qquad \eta=(A,W,\tau)
\]

과의 화살표도 닫히지 않았다. 이번 행동 cohort에는 `Delta W`, `Delta tau`,
population geometry가 없고 Figure 2--5의 다른 동물 cohort와 identity join도
없으므로 `NDNF -> Delta W -> Delta g -> behavior` 매개를 만들지 않는다.

## 원래 질문에 대한 답

- 답한 것: 동일 10마우스의 paired Control/Opto raw 행동에서 사전고정한
  complexity-specific 초기 재학습 interaction은 지지되지 않았다.
- 지지에 실패한 것: `ALT_BIO_D3_NDNF_COMPLEX_RELEARNING_v1`의 확인적 양성
  판정. 방향성 기술량은 증거 승격 조건을 만족하지 않는다.
- 반증되지 않은 것: NDNF interneuron이 apical dendritic integration에
  관여한다는 논문의 다른 개입 결과, 더 긴 시간척도의 학습효과, 다른 endpoint,
  성체 표현 변화 일반론.
- 전혀 판정하지 못한 것: 청소년기 의미 고정, 시냅스 가중치 변화, 축삭
  전도속도, 물리적 공간 접힘, 리만계량 변화.

## 다음 허용 행동

- 같은 D3 행동자료의 창·필터·검정을 바꾸어 이 주장을 구제하지 않는다.
- 이 결과를 NDNF gate나 `Delta W -> Delta g`의 양성 증거로 승격하지 않는다.
- 독립 계보에서 같은 생물학적 단위를 rule A/B/A'에 걸쳐 추적한 표현자료로
  “고정 의미”를 직접 시험하거나, 같은 동물의 synaptic/latency/population-
  geometry/behavior를 함께 측정한 개입자료로 매개사슬을 시험한다.
- condition order, period/carryover, complexity와 session 순서를 분리할 수 없는
  현재 한계는 후속자료 전까지 유지한다.
