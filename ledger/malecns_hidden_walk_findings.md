# MaleCNS 전체 경계의 숨은 경유량과 미래 정보

문서 유형: 개발 분석 원장. 시작일: 2026-09-14.
사용자 목표는 추론한 연구 패턴을 실제 MaleCNS에서 찾는 것이다. 이전
[실제 ID 경로 원장](malecns_dyad_return_findings.md)은 경로 존재를 확인했다.
이번 질문은 전체 outgoing 분모를 유지했을 때 숨은 경유의 양과 현재 관측에 드러나지 않은
내부 초기상태 정보가 미래 관측에서 어떻게 나타나는가이다. 새 다운로드·독립 동물 실험·
사전등록이 아니라 이미 본 단일 CNS의 개발 분석이다.

## 입력과 계산 범위

같은 `malecns-analysis/raw-dyad-return-v1`의 정렬 key·weight·source category 캐시를 재사용한다.
모든 raw source ID는 별도 상태로 유지한다. 원본 자기 연결도 전이에 포함하며 모든 outgoing
weight의 합으로 정규화한다. 추가 confidence·weight 문턱이나 top-K를 적용하지 않는다.

관측된 outgoing이 없는 target은 모형에서 흡수 상태로 둔다. 같은 관측 category를 가진
post-only ID는 하나의 흡수 상태로 계산상 합친다. 이 압축은 해당 category의 현재·미래
관측을 정확히 보존한다. 각각의 terminal ID를 구별하는 관측까지 보존한다는 뜻은 아니다.
원시 ID와 edge는 기존 캐시에 그대로 남긴다. 각 source에서 active target으로 가는 전이와
terminal category 경계로 가는 전이의 합은 1이어야 한다.

## 사전에 정한 비교

27개 assigned superclass마다 positive-outflow source 모두를 사용해 두 초기분포를 만든다.
첫째는 source 균등분포, 둘째는 전체 out-weight에 비례한 분포다. 두 경우 모두 초기
category 관측은 같은 한 superclass에 질량 1이다. 따라서 차이는 집단 관측이 숨긴 내부
구성이다. source의 out-weight가 같으면 두 분포가 같다는 음성 경우도 보존한다.
이 선택은 공급한 초기조건의 비교이지 신경활동·실제 과거 경험의 관측이 아니다.

전체 전이 후 0..16 step에서 category 확률, 총변동거리와 Fisher를 계산한다. 두 초기분포
사이의 혼합 비율을 $\alpha$라 두고 $\alpha=1/2$의 국소 정보를 쓴다. 출력 확률을
$p^U,p^W$라 하면 $G=\sum_x(p_x^W-p_x^U)^2/[(p_x^U+p_x^W)/2]$이고 두 확률이 모두
0인 항은 0으로 정의한다. 인위적인 epsilon이나 대각 regularization은 넣지 않는다.

관측은 active ID와 terminal category를 구별하는 세밀한 관측, 그리고 전체 30 category
관측의 두 층이다. 세밀한 Fisher는 step에 따라 증가하지 않아야 하고, 같은 step의 집단
Fisher는 세밀한 Fisher보다 크지 않아야 한다. 초기 집단 Fisher는 0이다. 전체 raw ID,
특히 terminal ID까지 구별하는 Fisher를 계산했다는 뜻은 아니다. 단일 혼합 좌표의 정보를
계산하며 전체 리만 계량이나 실제 뇌 좌표를 식별한 것이 아니다.

별도로 첫 step에 active 비주석/미분류/교세포 집단으로 들어간 질량이 2..64 step에
assigned 뉴런으로 **처음** 돌아오는 양을 센다. 돌아온 뒤의 재진입은 첫 경유 kernel에
중복 계산하지 않는다. assigned terminal ID에 도착한 것도 복귀로 센다. 직접 assigned에
남은 양, 처음 복귀한 누적량, hidden terminal에 흡수된 양, 아직 active hidden에 남은 양의
합은 1이어야 한다. 마지막 잔여 hidden 질량은 64 step 이후 추가 복귀량의 상한이다.
이때 복귀는 같은 시작 ID가 아니라 assigned 집합으로의 첫 도착이다.
저장 배열 `first_return_step2_by_initial_middle`은 2-step 복귀만 최초 hidden category로
분해한 값이며 2..64 step의 누적 중간 집단별 복귀량이 아니다.

두 계산의 숨은 공간은 다르다. 첫 경유의 hidden은 nonassigned raw ID지만 초기 Fisher
비교가 숨기는 것은 같은 assigned superclass 안의 source 구성이다. 또한 30범주 관측은
active와 absorbed 구분까지 합친다. 따라서 미래 Fisher 차이를 nonassigned 경유의 인과
효과로 귀속하지 않는다. active/absorbed 상태를 보존한 60출력 대조와 같은 관측의
기억 없는 축약·기억 포함 축약은 이후 별도 비교가 필요하다.

## 구현과 현재 상태

[분석 소스](../verify/MaleCNS/hidden_walk_information.py)와
[작은 그래프 검사](../tests/test_malecns_hidden_walk.py)의 독립 리뷰와 관련 검사 5개가
통과했고 전량 계산을 완료했다. 고유 ID·terminal 경계·자기 연결·정규화 수지, 명시적 terminal ID 모형과
흡수 category 압축의 일치, 첫 복귀의 중복 방지, Fisher의 영확률·유한차분을 검사한다.
SciPy의 기존 희소 연산을 사용하며 자체 고유해법·행렬지수는 만들지 않는다.

흡수 압축의 정확성은 모형 안에서 열별로 확인할 수 있다. active source의 열은 원시
active 도착 weight를 그대로 두고 terminal 도착 weight만 category별로 합친다. terminal
열은 원형에서도 압축 모형에서도 같은 관측 category의 흡수 상태로 남는다. 따라서 원형
전이 후 압축과 압축 후 전이가 교환하며, 동일 초기분포의 미래 category 확률이 일치한다.
이 논증은 terminal이 흡수적이라는 공급한 가정을 제거하면 일반적으로 성립하지 않는다.

현재 생물학적 지위는 구조에 결박된 대리모형의 `BIO_EVIDENCE_L0` 분석이다. 기존 실제
정적 접촉 관측의 L1과 구분한다. 신경전달 부호·지연·발화·가소성·독립 기능 관측이 없어도
구조 모형 안의 비교는 수행하지만, 해당 생물학적 변수의 검증으로 승격하지 않는다.

## 전량 실행 결과

2026-09-14의 [완료 JSON](../verify/MaleCNS/hidden_walk_information_result.json)을 근거로 한다.
전체 연결을 남긴 것은 전체 초기상태와 커널의 모든 성분을 조사했다는 뜻이 아니다.
27개 범주의 두 초기분포, 총 54개 probe에 한정한 작용을 계산했다.

| 항목 | 완료 수치 | 해석 |
|---|---:|---|
| 사용한 raw dyad | 151,856,684 | 전체 v1.0 minconf-0.5 연결, 추가 문턱 없음 |
| 전체 접촉 weight | 311,833,243 | 자기 연결 123개·weight 542도 포함 |
| 별도 상태로 보존한 active raw source | 1,834,661 | 이 모두를 완전한 뉴런으로 간주하지 않음 |
| 27개 초기 probe 범주의 positive-outflow source 합 | 165,665 | 이들의 균등·out-weight 두 분포를 사용 |
| active 전이 비영 성분 | 32,751,675 | 실제 ID 사이의 희소 행렬 |
| terminal 경계 비영 성분 | 1,760,728 | 같은 terminal category로 합친 열별 도착 확률 |
| terminal 도착 raw dyad / weight | 119,105,009 / 177,619,313 | 분모에서 제거하지 않음 |
| 열별 active+terminal 확률 합의 최대 오차 | 4.44e-16 | 수치 검산, 생물학적 보존 법칙의 측정 아님 |
| 전체 전이 0..16 step의 최대 질량 오차 | 1.19e-12 | 모든 초기 probe에서 전체 확률 1과 비교 |
| 첫 경유 질량 분할의 최대 오차 | 2.49e-14 | 직접 assigned·첫 복귀·hidden terminal·잔여 hidden |
| 계산 경과 시간 | 550.662초 | 파일 검증·연산·캐시 저장 포함, 생리적 시간 아님 |

working memory 사전 추정은 4,962,089,408 bytes였으며 설정 상한 8 GiB 안이었다.
실제 프로세스 peak RSS를 측정한 값이나 엄격한 OS 메모리 제한은 아니다.

27개 범주 모두 초기 30범주 Fisher가 0이고, 검사한 미래 step 중에는 허용오차
`5e-10`보다 큰 값이 있었다. 이는 통계적 유의성 판정이 아니라 모형 수치의 구별이다.
26개는 검사한 0..16 step 중 step 1에서 최대였고 `cb_intrinsic`은 step 2에서 최대였다.
세밀한 Fisher의 시간 비증가와 같은 step의 집단 Fisher 상한은 모든 probe에서 통과했다.
따라서 집단 Fisher가 0에서 증가해도 새로운 정보가 생성된 것은 아니다.
최대 집단 Fisher가 가장 작은 범주는 `ol_intrinsic`의 0.000609913418,
가장 큰 범주는 `sensory_ascending_tbc`의 0.341550738이며 둘 다 step 1의 값이다.

| 초기 범주 | 초기 세밀한 Fisher | 최대 집단 Fisher | 최대 step | step 16 집단 Fisher | 첫 복귀64 U / W |
|---|---:|---:|---:|---:|---:|
| ENS | 1.21789657 | 0.074806956 | 1 | 0.0311001338 | 0.0146810169 / 0.0114885244 |
| ascending_neuron | 0.623593544 | 0.00871582649 | 1 | 8.89160101e-6 | 0.00449677854 / 0.00441802451 |
| descending_neuron | 0.653805398 | 0.00450547344 | 1 | 1.11001802e-5 | 0.00382511105 / 0.00443854002 |
| cb_intrinsic | 0.771998074 | 0.0199184689 | 2 | 0.00019169866 | 0.00613924727 / 0.00463728367 |
| ol_intrinsic | 0.493510074 | 0.000609913418 | 1 | 0.00013612779 | 0.0061624666 / 0.00577431648 |
| vnc_intrinsic | 0.719315722 | 0.00433284999 | 1 | 4.10356917e-5 | 0.00494861477 / 0.00475757817 |

표의 U/W는 균등/out-weight 분포이고 복귀량은 퍼센트가 아닌 확률이다. 여섯 범주는
그림의 구조적 범위를 넓히기 위해 골랐으며 성공 사례를 골라 전체로 일반화한 표가 아니다.
27개 전체 결과는 JSON과 전체 범주 그림에 보존한다.

첫 step에 active hidden으로 들어간 후 64 step까지의 첫 복귀량은 초기 전체 질량 대비
균등분포에서 최대 **3.826487%**, out-weight 분포에서 최대 **3.205549%**였으며 두 최대는
모두 `ol_sensory`였다. `visual_projection_tbc`는 두 분포 모두 active hidden 진입과
첫 복귀가 0이었다. 이 범주에서도 미래 집단 Fisher는 양수이므로 두 현상을 동일한 숨은
공간의 원인·결과로 읽을 수 없다. 64 step 잔여 active hidden 질량의 전체 최대는
`cb_intrinsic` 균등분포의 **1.9444420321e-8**이다. 이는 그 probe에서 64 step 이후
추가 첫 복귀가 늘어날 수 있는 절대 확률 상한이며, 신뢰구간이나 신경 기억의 수명은 아니다.

저장 NPZ의 target별 첫 복귀를 더한 값과 JSON 누적량의 최대 오차는 3.47e-18,
최초 hidden category별 step-2 분해를 더한 값과 step-2 첫 복귀의 최대 오차는 7.98e-16이었다.
전체 raw ID의 Fisher·전체 이력 커널·초기 hidden 자극은 이번 결과에 포함되지 않는다.

## 소스와 산출물의 무결성

다음 SHA-256은 완료 실행의 파일 정체성이다. 입력은 이전
[dyad 결과 원장](malecns_dyad_return_findings.md)의 캐시를 재사용했고 새 다운로드는 없다.
원본과 과거 결과를 덮어쓰지 않았으며, 아래 분석 소스·테스트는 결과 JSON의 해시로 잠긴다.

| 파일 | bytes | SHA-256 |
|---|---:|---|
| `verify/MaleCNS/hidden_walk_information_result.json` | 1,290,078 | `098241d5051fb133cbb1fbf08ef505180850bd4da34d596d2fecf6f6bce0fb9d` |
| `data/local/malecns-analysis/hidden-walk-v1/active_transition.npz` | 131,402,054 | `7d9a412563fe11e4390c94cd705f728ab93a1c05ff5db9c462eaaafd8afea350` |
| `data/local/malecns-analysis/hidden-walk-v1/terminal_boundary.npz` | 6,079,459 | `d18bc531debd8fd3e84c8804bb5a848addb3d8bacc321cb51e8ec7aa2b5d5130` |
| `data/local/malecns-analysis/hidden-walk-v1/source_scope.npz` | 7,344,249 | `f5106515fd1c00e32c4f988da07c7a8a5e08b0662f15d5427cc1ade0d9796273` |
| `data/local/malecns-analysis/hidden-walk-v1/probe_traces.npz` | 520,093 | `122178b18ca034be8e15752a58a32505894b46e9d3da4ffac7a7ebdfbf37ec58` |

분석 소스 SHA는 `cf625be0d0621e20308f4d2edffe00c08d96b6c72308eb9e80a81736b67ec585`,
테스트 SHA는 `1d5a05e04553931a8dda240669423109aedd1e5078c21360daad651cce758200`이다.
부모 dyad 결과 SHA는 `42b0414279cd6e12ae0fd541ac8ced607fff47cde3b3cdd81b057b80e35b9239`다.
배열의 축과 각 관측의 범위는 결과 JSON·소스·실행 notebook에 함께 둔다.

## 실행 그림과 검수 이력

읽기 경로는 [검수한 notebook](../verify/MaleCNS/hidden_walk_checked_companion.ipynb)과
[정적 HTML](../verify/MaleCNS/hidden_walk_checked_companion.html)이다. 완료 JSON·NPZ만
읽고 무결성과 수치 수지를 재확인하며 전량 전이를 다시 실행하지 않는다. nbformat 4.5의
9개 셀 중 코드 4개가 실행 순서 1..4, 오류 0으로 끝났다. 내장 PNG 3개는 외부 PNG와
bytes·SHA가 모두 일치하고 HTML에도 같은 이미지 3개가 내장돼 있다.

| 검수 산출물 (`verify/MaleCNS/` 기준) | bytes | SHA-256 |
|---|---:|---|
| `hidden_walk_checked_companion.ipynb` | 482,111 | `358a0ccb002ab2f099e00dce9a1e93c8d2b43c452a9863af7ce2954269e36c2d` |
| `hidden_walk_checked_companion.html` | 478,574 | `dd84a60a301442ad5ab7936949f30dcf8f8eb19085f94ad964cb3802aacdc355` |
| `figures/hidden-walk-checked/first_hidden_return.png` | 125,921 | `632ceed234b3f9ca51867f46ba19d4a5bd288e36eaf9ff6b392ec6f3ec13fd10` |
| `figures/hidden-walk-checked/future_category_fisher.png` | 124,677 | `92e5415bc7f0f11b5618f40e63b19f9b2e309af8d42b17dea383d4683e3c0e90` |
| `figures/hidden-walk-checked/refined_and_category_information.png` | 97,839 | `c0e6bd70ebdb934b6658dba5a8914c577864a7227e03ee4b1b4ae169e96cb8f6` |

[Builder](../verify/MaleCNS/build_hidden_walk_notebook.py)의 SHA는
`b191885865e0aa68843be9fa96672d678a1b0dbf78ba1a1cdeb92e59fae4bdef`다.
Matplotlib 3.10.8, nbformat 5.11.1, nbclient 0.11.0, ipykernel 7.3.0을 사용했다.
초기 실행본 `hidden_walk_companion.ipynb`(SHA
`83fb9629684b7cb0d349e19ad54571b55d8b943217b086198e57b5692e6db22e`)와 HTML(SHA
`138127df13bfc6648b01c3abcebc1dfabac98e59c14a6b92c5d2cd3c319f48c7`),
`figures/hidden-walk/`는 보존하지만 현재 읽기본으로 채택하지 않는다. 수치 오류는 없었으나
공유 y축이 첫 패널에서 고정돼 세 번째 그림의 ENS 초기 1.21789657을 잘랐기 때문이다.
검수본은 여섯 패널의 전체 값으로 공통 상한을 정하고 모든 선이 축 안에 있는지 검사한다.
처음 두 PNG는 원본과 해시가 같고, 교정한 세 번째 PNG도 직접 열어 잘림·겹침 없음을 확인했다.
브라우저가 제공되지 않아 HTML 자체의 브라우저 시각 검사는 수행하지 못했다.

검수본의 첫 실행은 셀 실행 전 `kernel_info` 대기에서 kernel이 종료됐다. 출력이 전혀
생성되지 않았음을 확인한 뒤 같은 승인 실행기·환경으로 한 번 재시도해 성공했다.
정책 우회·원자료 수정·이전 산출물 덮어쓰기는 없었다.

## 재현과 다음 조건

작은 그래프 관련 검사 5개는 기본 승인 Python 3.11.9에서 통과했다. 전량 실행에는
Python 3.11.15, NumPy 2.4.6, SciPy 1.17.1을 사용했다. 저장된 결과를 덮어쓰는 호출은
실행기가 거부한다. 아래는 실제 완료 명령이며 재실행하려면 별도 결과·캐시 경로를 지정한다.

```powershell
$env:CE_PYTHON='C:\Users\dongh\AppData\Local\uv\cache\archive-v0\Sp2cxzBGA63aECqn\Scripts\python.exe'
.codex/hooks/python.cmd python verify/MaleCNS/hidden_walk_information.py --dyad-result verify/MaleCNS/dyad_return_result.json --cache-dir data/local/malecns-analysis/hidden-walk-v1 --result verify/MaleCNS/hidden_walk_information_result.json --steps 16 --return-steps 64 --max-working-gib 8
```

다음은 30범주를 active/absorbed 60출력으로 나눈 대조, 같은 관측에서 기억 없는 예측과
이력 포함 예측의 비교, 그리고 초기 구성과 구별되는 연결 변화의 미분이다. 이 조건을
만족하기 전에는 비주석 경유가 관측 정보 변화의 원인이라고 판정하지 않는다. 해부학 ROI와
신경전달 부호·지연·가소성·활동 관측은 별도 결합이 필요하다. 이번 단계를 마쳤어도
고정 뉴런의 연결·부가 기능에서 실제 뇌 메트릭을 식별한다는 전체 목표는 미완료다.

## 작업 인계와 검증 (2026-09-15)

저장소는 `C:\dev\ce\ce-agi-runtime`, 브랜치는 `main`, upstream은 `origin/main`이다.
확인한 HEAD와 로컬 remote-tracking tip은 모두
`27c2c02e5e168732b7d24356c5b39925716cd415`다. 이번 작업에서 fetch·커밋·push는 하지
않았으므로 서버 원격의 최신 tip을 새로 확인한 것은 아니다.

이번 단계의 새 분석 파일은 `verify/MaleCNS/hidden_walk_information.py`,
`tests/test_malecns_hidden_walk.py`, 결과 JSON·희소 캐시·companion builder와 실행 읽기본이다.
원장 본문과 `data_registry.md/jsonl`, 논문 7장 및 목차·4장·6장·상위 읽기지도·PRD를
갱신했다. 원장 본체에 새 분석/검수본 10개와 보존용 초기 읽기본 5개의 해시를 등록했다.
대용량 원자료와 기존 분석은 재사용했으며 파일 보유·과학적 적격성 판정을 구별한다.

관련 테스트 명령 `.codex/hooks/python.cmd pytest tests/test_malecns_hidden_walk.py -q`는
5개 통과했다. 문서 변경 후 `.codex/hooks/python.cmd python .codex/hooks/repository_harness.py`는
`REPOSITORY_HARNESS_PASS`였다. 같은 harness의 `check_links`를 MaleCNS 원장 4개와
`data_registry.md`에 적용한 결과 위반 0이었다. 변경한 tracked 문서의 `git diff --check`도
통과했다. Git의 LF/CRLF 경고는 있었지만 줄바꿈을 일괄 변경하지 않았다.
Sol의 읽기 전용 독립 리뷰에서 수치·분모·전이·Fisher·첫 복귀 식의 차단 이슈는 없었고,
현재 소스·테스트·결과·검수 notebook의 해시 일치도 확인했다.

기존 `.claude/` 삭제, `AGENTS.md` 변경과 MICrONS radial의 미완료 JSONL·render 소스는
다른 작업으로 보존했다. 전체 pytest·생물학적 endpoint·배포 검사는 수행하지 않았다.
이 인계는 이번 개발 분석의 완료 기록이지 전체 연구의 폐쇄나 정식 감사 증거가 아니다.
