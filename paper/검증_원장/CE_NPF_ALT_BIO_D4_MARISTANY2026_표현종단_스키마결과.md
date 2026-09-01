# CE-NPF 대체 생물자료 D4 Maristany 2026 표현 종단 스키마 결과

## 판정

- Figure 5 동일 열의 세션간 기술 비교:
  `PASS_CONDITIONAL_DESCRIPTIVE`.
- 동물 수준 확인 검정: `D4_ANIMAL_JOIN_SCHEMA_BLOCKED`.
- 청소년기 의미 고정 판정: `D4_DEVELOPMENTAL_SCOPE_BLOCKED`.
- endpoint 결과: 계산하지 않음.

공급자 README와 논문은 같은 FOV와 같은 NDNF interneuron을 5개 세션 동안
추적했다고 기술하고 MAT의 세포 열 수도 세션간 일정하다. 그러나 공개 MAT에는
`mouse_id`, `fov_id`, 지속 `cell_id`, registration confidence가 없다. 170개
세포를 독립 표본으로 검정하면 4마리를 170마리처럼 세는 pseudoreplication이므로
정식 D4를 실행하지 않는다.

## Figure 5 정본 후보

- archive member:
  `Figure5/Data/Figure5Data_Selectivity_RepDrift.mat`
- member SHA-256:
  `2eaa588d454cb2863b31f3eb8ba374a66c18de7c5d138d10d0a2964f5004010a`
- 공급자 범위: 4 animals, 동일 NDNF interneurons 170개, 5 sessions.
- session 의미: 1--3은 Rule A, 4는 Rule B, 5는 Rule A'.
- `x_df`: 180 frame, -3 s에서 3 s까지 단조 증가.

각 session의 주요 배열은 다음과 같다.

| 구조 | 필드 | 형상 |
|---|---|---:|
| `type_sum_all[1..5]` | `nu_type1`, `nu_type2`, `sel_types` | `180 x 170` |
| `type_sum_all[1..5]` | `nu_sel` | `180 x 6`; 세포 열 비대응, 제외 |
| `cd_choice_all[1..5]` | `Lcd_proj`, `Rcd_proj` | 각각 `180 x 170` |
| `cd_stim_all[1..5]` | `Lcd_proj`, `Rcd_proj` | 각각 `180 x 170` |
| `sig_all` | `Choice`, `Outcome`, `Stimuli`, `Silent`, `Both`, `Delay` | 각각 `5 x 170`, 0/1 |

trial-level instruction, choice, outcome, trial count, raw/deconvolved trace, mouse/FOV
key와 발달 연령은 없다. `nu_type1/2`는 이미 trial-averaged activity다.
`Figure5Data_TransitionError.mat`의 A-B/B-A 각 207열에는 persistent cell ID가
없으므로 세션간 열 순서로 결합하지 않는다.

## Figure 4가 정본이 될 수 없는 이유

- `Figure4/Data/DataRepDrift_CaImagingDendrites.mat`, SHA-256
  `6b3c315020a3bd57fae2a16fec88e75fd722534e4a3d364605bdc5752b75d49b`:
  control 56열, test 58열.
- `Figure4/Data/DataSummary_CaImagingDendrites.mat`, SHA-256
  `81eed435ea1527d26d109d0370ba12aca811c202ab88d5e349164551049c8278`:
  control 43열, test 42열.
- 두 자료의 동일 열 fingerprint는 control 31개, test 32개만 정확히 겹치며
  단순 부분집합이 아니다.
- 어느 자료가 최종 representational-drift 모수인지 README와 실행코드가
  지정하지 않고, 논문의 51 dendritic trees/5 animals와도 직접 일치하지 않는다.

따라서 Figure 4 정본을 임의로 선택하지 않는다.

## 실행하지 않은 누출방지 기술 endpoint

Figure 5 전체 170열을 유의성 flag로 사후 선택하지 않고, 공급자 report epoch
MATLAB index `91:151`의 signed representation을

\[
r_{is}(t)=\nu^{(1)}_{is}(t)-\nu^{(2)}_{is}(t)
\]

로 둘 수 있다. 같은 열 안에서

\[
C_i^{AA}=\operatorname{median}_{(a,b)\in\{(1,2),(1,3),(2,3)\}}
\rho(r_{ia},r_{ib}),
\]

\[
C_i^{AB}=\operatorname{median}_{a\in\{1,2,3\}}
\rho(r_{ia},r_{i4}),\qquad
C_i^{AA'}=\operatorname{median}_{a\in\{1,2,3\}}
\rho(r_{ia},r_{i5})
\]

를 기술할 수 있다. 후보 기술량

\[
Q_i=C_i^{AA'}-C_i^{AB}
\]

가 양수면 A' 표현이 B보다 과거 A에 더 가깝다는 뜻이다. 강한 완전고정 명제는

\[
G_i=C_i^{AA'}-C_i^{AA}\ge-\delta
\]

같은 동등성 문제지만, 외부에서 정한 신뢰도 기반 `delta`와 animal cluster가
없으므로 실행하거나 p값을 만들지 않는다.

## 2번 가설의 재구성

원래 명제

> 뉴런/뉴런군은 의미를 가지고 태어나며 청소년기에 고정된다.

는 이 자료의 연령 범위와 식별변수로 판정할 수 없다. 생물학적으로 관측 가능한
형태는 다음처럼 분해해야 한다.

\[
\text{stable anatomical unit identity}
+\text{context-dependent functional representation}
+\text{possible reinstatement}.
\]

즉, 해부학적으로 같은 세포가 유지되는 것과 그 세포의 과제 관련 표현이 고정되는
것은 다른 명제다. 규칙에 따른 이동과 과거 규칙의 재사용은 “내재 의미 라벨”보다
문맥·회로·학습상태에 조건부인 예측/인과 기능으로 적어야 한다.

## 원래 질문과 다음 게이트

- 답한 것: 공개 Figure 5는 같은 세포 열의 기술적 A/B/A' 비교까지 가능하다.
- 반증한 것: 없음. 이는 결과가 아니라 독립단위와 join의 입력 실패다.
- 살아 있는 것: stable identity와 context-dependent representation을 분리하는
  재구성 가설.
- 다음 허용 행동: mouse ID, persistent cell ID, registration QC, trialwise 활동과
  행동이 함께 있는 독립 자료에서 animal-clustered endpoint를 먼저 계약한다.
- 금지: 170개 열을 독립 표본으로 p값 계산, 유의세포만 사후 선택, Figure 4 정본
  임의 선택, 이 성체 수일 자료로 출생--청소년기 고정을 주장하는 것.
