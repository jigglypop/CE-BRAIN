# MaleCNS 전체 연결의 집단 전달과 내부 상태 검사

문서 유형: 개발 분석 원장. 시작일: 2026-09-14.
사용자 목표는 추론한 연구 패턴을 실제 MaleCNS에서 있는 그대로 찾는 것이다.
이전 단계의 [데이터 재고](malecns_inventory.md)는 완료한 입력 점검이며,
이번 단계에서는 원시 연결을 재사용해 집단 전달의 폐쇄 필요조건을 검사한다.
사전등록·새 동물 표본·실제 발화 기록의 분석은 아니다.

후속 상태: 아래 범주 분석 당시 미실행이었던 전량 dyad 중복·상호연결과 실제 중간 ID 경로는
[별도 ID 경로 원장](malecns_dyad_return_findings.md)에서 완료했다. 이 문서의 기존 범주
행렬·판정·산출물은 그대로 보존하며 서로 다른 분모의 수치를 합치지 않는다.

## 질문과 입력

질문은 같은 뉴런 상위분류 안의 뉴런들이 동일한 다음 target-category 분포를 갖는가이다.
공식 full weights의 모든 행을 사용한다. `status == Glia`, non-Glia의 `superclass` 결측,
annotation에 없는 segment를 각각 분리하고 나머지 27개 superclass를 유지한다.
총 30개 관측 범주다. superclass는 뉴런 정체성 분류이며 접촉의 해부학적 ROI가 아니다.

분류된 뉴런 밖으로 나가는 weight와 그 반대 방향도 보존한다. self-loop와 confidence
통과 표에 실린 작은 weight도 제거하지 않는다. zero-out annotation은 따로 세고
임의의 self-loop로 채워 넣지 않는다. 원표의 중복 dyad 검사는 아직 별도 과제이므로
비가중 판본의 단위는 "고유 연결"이 아닌 "connection record"다.

## 모형과 대조

발신 뉴런 $i$에서 관측 범주 $B$로 가는 weight를 $c_{iB}$,
$n_i=\sum_Bc_{iB}$로 둔다. $q_i(B)=c_{iB}/n_i$는 **시냅스 수로 정의한 구조적 이동
대리모형**이다. 전달물질 부호·막전압·생리적 전이확률을 측정한 값이 아니다.
같은 source 범주의 모든 $q_i$가 같아야 이 분할의 strong lumpability가 가능하다.
정확한 이 조건이 깨지는 것은 내부 상태를 지운 축약의 반례이지 실제 기억의 확인은 아니다.

양의 out-degree를 가진 source 수를 $m$, 총 weight를 $S=\sum_i n_i$라 하면

$$p_B=\frac{\sum_i c_{iB}}S,\qquad
T=\frac1S\sum_i n_i\|q_i-p\|_2^2.$$

source별 $n_i$와 범주별 target 총량을 유지하고 target stub을 무작위 재배치하는 대조에서

$$\mathbb E_0[T]=\frac{m-1}{S-1}(1-\|p\|_2^2).$$

이는 finite-population 다변량 초기하분포의 분산을 합한 정확한 기대값이다.
관측/기대 비율은 p값이나 독립 표본 효과크기가 아니다. 같은 T-bar의 여러 partner 및
세포형·공간 제약을 교환 가능한 생물학 표본으로 취급하지 않는다. `S<=1` 또는 `m<=1`은
대조 기대값 미정의로 남긴다. 양의 degree 0개인 범주는 관측 T도 미정의다.

주 계산은 모든 target을 포함한 weight 판본이다. 같은 전체 입력의 connection-record
판본과, target이 superclass-assigned 뉴런인 경우로 조건화한 판본을 민감도로 비교한다.
후자는 경계를 잘라낸 전체망 대체물이 아니다. 분산·total variation은 전체 source에서
집계하며, 읽을 수 있는 개별 반례는 out-weight 100 이상인 source 중 target 확률 범위가
가장 큰 좌표의 양 끝을 선택한다. 이 선택은 예시용 극단값이며 대표 뉴런이나 확인 집합이 아니다.

## 구현과 현재 상태

[전체 집계 코드](../verify/MaleCNS/whole_structure.py)와
[작은 독립 검사](../tests/test_malecns_whole_structure.py)를 새로 구현했다.
전체 raw 행은 스트리밍하고 211,577개 annotation의 incoming/outgoing 범주 집계를 저장한다.
결과를 쓰기 전 전체·범주·annotation 수지를 검사한다. 기존 출력은 덮어쓰지 않는다.
고정-margin null 기대값은 작은 모든 stub 배치를 열거하는 검사로 별도 대조한다.

전체 집계와 type-conditioned source-LOO 실행이 완료됐다. 소스 검토와 관련 테스트는
집계 9개, type-LOO 4개가 통과했다. 다음 결과는 원자료에서 직접 계산한 개발 분석이다.

## 1. 전체 수지와 방향 구조

[전체 결과 JSON](../verify/MaleCNS/whole_structure_result.json)은 모든 151,856,684행을 읽고
weight 합 311,833,243, self-loop 123행·weight 542를 기록했다. 전체·범주·annotation의
incoming/outgoing 수지가 일치했다. annotation→미주석 segment는 전체 weight의 55.01%,
annotation→annotation은 40.20%다. 해당 connection-record 비율은 74.56%, 17.14%다.

범주 사이를 잇는 off-category weight는 전체의 69.84%다. 이 중 역방향 범주 합계와
짝지을 수 있는 최소 weight의 비율은 12.28%다. 이는 $\sum_{a\ne b}\min(W_{ab},W_{ba})/
\sum_{a\ne b}W_{ab}$이며 실제 뉴런 쌍의 reciprocity가 아니다.

| Source → target | Weight, 백만 접촉 | 반대 방향, 백만 접촉 |
|---|---:|---:|
| ol_intrinsic → visual_projection | 7.714 | 1.322 |
| vnc_intrinsic → vnc_motor | 2.215 | 0.019 |
| ascending_neuron → vnc_intrinsic | 1.594 | 1.636 |

이 표는 원 weight의 반올림 표현이다. 비대칭과 양방향 연결이 모두 존재한다. 서로 다른
뉴런을 하나의 범주로 모으면 거짓 경로가 만들어질 수 있어 범주 행렬의 곱으로 실제
되돌아오는 경로를 주장하지 않는다. 실제 dyad/triplet 경로와 ROI는 다음 별도 검사다.

## 2. Superclass 평균의 폐쇄 검사

27개 assigned-neuron 범주의 full-weight T는 모두 0보다 컸다. 따라서 공급한 구조적
walk에서 superclass만 남긴 exact closure의 필요조건은 실패한다. T/null 기대 비율은
1.279–599.623이다. 1보다 큰 비율 자체를 통계적 유의성으로 읽지 않는다.

| 범주 | Annotation 수 | Weight T/E0 | Record T/E0 | Assigned-target 조건부 T/E0 |
|---|---:|---:|---:|---:|
| ENS | 50 | 1.279 | 1.279 | 1.000 |
| cb_efferent | 4 | 1.656 | 1.500 | 0.781 |
| cb_intrinsic | 32,164 | 301.510 | 144.259 | 312.133 |
| ol_intrinsic | 89,403 | 60.703 | 14.652 | 95.154 |
| vnc_intrinsic | 13,161 | 163.189 | 40.997 | 252.618 |
| ascending_neuron | 1,846 | 412.751 | 84.010 | 597.559 |
| descending_neuron | 1,314 | 305.657 | 109.690 | 466.313 |
| visual_centrifugal | 563 | 599.623 | 222.196 | 887.608 |

전체 27범주는 JSON에 누락 없이 있다. 23/27에서 weight 비율이 record 비율보다 크고,
20/27에서 assigned-target 조건부 비율이 full-weight보다 크다. 조건부 입력이 보존하는
원래 out-weight의 범주별 비율 중앙값은 41.51%뿐이다. 따라서 경계를 삭제한 결과로
전체망을 대체할 수 없다. 개별 최대 차이 witness도 미주석 target의 차이가 지배할 수 있다.

## 3. 세부형과 source-neuron 보류 예측

넓은 superclass 안의 서로 다른 세부형을 섞었기 때문에 T가 커진 것인지 조사했다.
[후속 소스](../verify/MaleCNS/type_conditioned_closure.py)는 새 raw scan 없이 해시를
확인한 같은 집계 배열을 재사용한다. source만 166,700 assigned-neuron으로 해석하며
target은 교세포·미분류·미주석을 포함한 30범주 전체를 유지한다.

각 source의 **전체 outgoing row를 훈련 합계에서 제거**하고, 다른 source의 superclass
평균과 `(superclass,type)` 평균으로 그 분포를 예측한다. 같은 type의 양의 outflow peer가
없으면 superclass 보류 모형으로 돌아간다. 균등 Dirichlet 총량 alpha 1, 10, 100을 모두
계산했고 결과를 보고 특정 값을 사후 선택하지 않았다.

[결과 JSON](../verify/MaleCNS/type_conditioned_result.json)의 활성 source는 165,665개,
zero-out은 1,035개다. 평가 contact weight는 295,069,014이며 `(superclass,type)` 그룹은
11,803개다. type 결측 source는 2,194개, 그중 활성은 2,076개다.

| Alpha 총량 | Superclass loss | Type loss | Weight-weighted 감소 | Source 평균 감소 |
|---|---:|---:|---:|---:|
| 1 | 0.995924 | 0.886486 | 10.989% | 10.566% |
| 10 | 0.995921 | 0.886633 | 10.974% | 10.534% |
| 100 | 0.995925 | 0.890706 | 10.565% | 10.063% |

Loss 단위는 구조적 target 전이 한 번당 nats다. 실제 발화·행동의 확률 점수가 아니다.
type peer가 있는 활성 source 비율은 99.788%, weight coverage는 99.486%다.
type 결측 계층의 개선은 0.775–0.815%로 작았다. alpha=1에서 94.03% source의 loss가
낮아졌지만, 9개 소형·미세분 범주는 같은 그룹 또는 fallback으로 개선이 정확히 0이다.

음성 결과도 유지한다. `cb_endocrine` 개선은 alpha 1/10/100에서 각각 −4.00%, −4.99%,
−15.63%다. alpha=100에서는 `vnc_motor` −10.93%, `vnc_efferent` −3.48%,
`vnc_endocrine` −2.63%도 악화했다. 작은 peer 집단과 smoothing 의존성을 별도 한계로 둔다.

이 보류는 catalogue를 고정한 source-row 보류다. type 정의에 같은 연결 정보가 사용됐을
가능성이 있어 독립 annotation이나 독립 동물 확인이 아니다. 다음 절의 label 대조는
이 내부 관계가 단순한 그룹 크기·연결량 구간만으로도 생기는지 확인한다.

## 4. Label과 degree 조건 대조

[대조 소스](../verify/MaleCNS/type_label_control.py)로 두 가족 각각 24회, 총 48회를
완료했다. 첫 가족은 superclass 안에서 type 이름을 섞고, 두 번째는 같은 superclass의
out-weight decile 안에서만 섞는다. 실제 counts·source별 degree·block별 type 개수는
고정하며 type 결측과 zero-out source도 움직이지 않는다. alpha=1을 그대로 사용했다.

[대조 결과](../verify/MaleCNS/type_label_control_result.json)는 parent LOO loss와
type peer source 165,313개가 모든 반복에서 같음을 확인했다.

| Type 이름 조건 | Weight loss 감소 범위 | 평균 | Source 평균 감소 범위 |
|---|---:|---:|---:|
| 실제 catalogue | +10.988589% | 같은 단일 관측 | +10.566% |
| Superclass 안에서 섞기, 24회 | −7.113024% ~ −6.649042% | −6.924372% | −3.172752% ~ −3.029292% |
| Superclass + degree decile 안에서 섞기, 24회 | −7.020242% ~ −6.597463% | −6.840222% | −1.327911% ~ −1.205990% |

이 대조에서는 임의 세분화가 개선을 재현하지 못하고 오히려 악화했다. 따라서 실제
catalogue의 세부형과 target 분포의 관계는 이 두 제한된 무작위 배치로 설명되지 않는다.
그러나 type을 만들 때 연결을 사용했을 가능성은 여전히 남는다. 정확한 degree를 맞춘
pair 대조나 공간·ROI 제약, 독립 type annotation, 독립 개체를 대체하지 않는다.
두 번째 가족의 predictor peer는 여전히 `(superclass,type)` 전체에서 구하며, degree는
label 재배치의 제한이지 degree-local predictor가 아니다. 유한 24회 분포를 정밀 p값이나
독립 생물학 표본으로 해석하지 않는다.

## 산출물과 재현

- 전체 집계 배열: `data/local/malecns-analysis/whole-structure-v1.npz`, 6,629,431 bytes,
  SHA-256 `d29cb67ea2de560f5bc49314fba4c91e40e3b4e98c685075302197132ce24f98`.
- 전체 결과: `verify/MaleCNS/whole_structure_result.json`, 214,189 bytes,
  SHA-256 `38e60951fbda74a63e4ec0821e3d54df18e1dae010d26808f2b6bb76a35ebc79`.
- Type LOO 결과: `verify/MaleCNS/type_conditioned_result.json`, 48,416 bytes,
  SHA-256 `ccdf60efc2d6ebfd5766214aed4564e7a11240c34e82dcf4e72c3adee97ae9e8`.
- Label 대조 결과: `verify/MaleCNS/type_label_control_result.json`, 27,486 bytes,
  SHA-256 `bc9fb0bffe9ffd3817cc3c893c92997d0b5e79e39c733dafa21b72ba6fcc8301`.

계산 환경은 기존 승인 Arrow 실행기의 Python 3.14.4, NumPy 2.5.3, PyArrow 25.0.1이다.
실행기 절대 경로와 입력·계산 소스 해시는 각 JSON에 들어 있다. 산출물은 데이터 원장에
추가 등록하고 원본을 수정하거나 중복 다운로드하지 않았다.

```powershell
.codex/hooks/python.cmd python verify/MaleCNS/whole_structure.py `
  --source-dir data/local/malecns-v1.0 `
  --arrays data/local/malecns-analysis/whole-structure-v1.npz `
  --result verify/MaleCNS/whole_structure_result.json
.codex/hooks/python.cmd python verify/MaleCNS/type_conditioned_closure.py `
  --whole-result verify/MaleCNS/whole_structure_result.json `
  --result verify/MaleCNS/type_conditioned_result.json
.codex/hooks/python.cmd python verify/MaleCNS/type_label_control.py `
  --type-result verify/MaleCNS/type_conditioned_result.json `
  --result verify/MaleCNS/type_label_control_result.json --replicates 24
```

위 명령은 Arrow가 있는 승인 실행기를 `CE_PYTHON`으로 선택한 환경에서 실행했다.
기존 출력이 있으면 의도적으로 멈춘다. 재계산은 새 결과 경로를 명시하고 이전 결과를 보존한다.

범위고정 EM 접촉의 방향·분포 관측은 `BIO_EVIDENCE_L1`의 구조 구성요소에 한정한다.
구조적 walk의 폐쇄 반례와 정보·기억 기전의 통합 해석은 `BIO_EVIDENCE_L0`이며,
LOO라는 이름만으로 L2·기억·학습 검증으로 승격하지 않는다.

## 그림과 검증

[실행된 notebook](../verify/MaleCNS/whole_structure_companion.ipynb),
[HTML 읽기본](../verify/MaleCNS/whole_structure_companion.html),
[생성 코드](../verify/MaleCNS/build_structure_notebook.py)를 함께 남겼다.
nbformat 검증을 통과했고 코드 셀 4개가 순서대로 실행돼 오류 0개였다. 세 그림의 notebook
내장 PNG와 외부 PNG 해시가 같았으며, 그림의 분모·수치·음성 범주를 JSON에서 독립 대조했다.
외부 PNG 3개를 직접 열어 제목·축·범례·전체 범주의 표시를 시각 확인했다.

그림 실행은 기존 승인 Python 3.11.15 + Matplotlib 3.10.8 + NumPy 2.4.6 환경을 사용했다.
notebook 지원 패키지 nbformat 5.11.1, nbclient 0.11.0, ipykernel 7.3.0은 전역 설치 대신
`C:/Users/dongh/AppData/Local/Temp/ce-malecns-notebook-deps-20260914`에 설치했다.
notebook kernel도 `.codex/hooks/python.cmd`를 경유한다. 분석 실행기와 그림 실행기의
버전을 구별하며 temp 의존성이 없으면 같은 패키지를 승인된 환경에 준비해야 한다.

관련 source/fixture 검사는 9 + 4 + 1 = 14개 통과했다. 이는 코드와 대조 연산의 검증이며
생물학적 증거의 14개 복제가 아니다. 현재 다음 과제는 **전체 raw dyad 중복·상호연결 검사 →
미주석 분절을 경유하는 실제 ID 경로와 ROI 조건 → 경계를 유지한 전달·내부 이력 비교**다.

최종 문서 검사 `.codex/hooks/python.cmd python .codex/hooks/repository_harness.py`는
`REPOSITORY_HARNESS_PASS`였고, 분리 원장 세 파일의 링크 검사와 변경 범위의
`git diff --check`도 통과했다. 연구 목표는 계속 진행 중이며 전체 패턴 탐색의 완료 판정이 아니다.

## 작업 인계

저장소 `C:/dev/ce/ce-agi-runtime`, branch `main`, upstream `origin/main`.
HEAD와 이번 `git ls-remote origin refs/heads/main`은
`27c2c02e5e168732b7d24356c5b39925716cd415`다. 커밋·push는 하지 않았다.
이번 추가 파일은 `verify/MaleCNS/`의 집계·type LOO·label 대조·notebook 생성 소스와
결과·그림, 관련 테스트 세 파일, 이 원장과 논문 5장이다. 데이터 원장·논문 입구·PRD도 갱신했다.
최초 조사 단계의 변경은 보존했고, 사용자 기존 `AGENTS.md`, `.claude/` 삭제,
MICrONS radial 미추적 두 파일은 건드리지 않았다. runtime 세 결함 수정과 MICrONS 재계산도
이번 연구와 별개로 미실행 상태다.
