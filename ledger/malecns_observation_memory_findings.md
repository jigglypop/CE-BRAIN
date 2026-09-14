# MaleCNS 관측 경계 대조와 집단 이력 축약

문서 유형: 개발 분석 원장. 시작일: 2026-09-15.
이전 [숨은 경유와 미래 정보](malecns_hidden_walk_findings.md)는 같은 현재 범주 관측에서
미래가 갈라지는 조건부 반례를 보였다. 이번 질문은 그 차이 중 active/absorbed 구분을
버려 생긴 부분을 분리하고, 같은 관측의 기억 없는 예측과 이력 포함 예측을 비교하는 것이다.
전체 고정 뉴런·연결에서 정보와 계량을 판별한다는 사용자 목표의 다음 단계이며,
새 다운로드·독립 동물 실험·사전등록이 아니다.

## 고정 입력과 관측

`hidden-walk-v1`의 4개 NPZ와 완료 JSON을 재사용한다. 현재 크기·SHA를 다시 확인했으며
active 전이 1,834,661차원·32,751,675개 비영 성분과 30범주 terminal 경계를 바꾸지 않는다.
모든 30개 active category에 source가 있어 양의 lifting을 정의할 수 있다. 원형은
151,856,684개 연결의 전체 outgoing 정규화를 유지하고 terminal 흡수를 가정한 모형이다.
별도 데이터 등록은 [data registry](data_registry.md)에 둔다.

기존 관측은 active와 terminal을 합친 30범주다. 새 관측은 active 30범주와 terminal
30범주를 구별하는 60출력이다. 같은 27쌍 균등/out-weight 초기분포와 0..16 step에서
`G30 <= G60 <= Grefined`를 검산한다. refined는 active ID와 terminal category를
구별하며 전체 terminal ID 정보가 아니다. 60출력을 다시 30으로 합친 값이 이전 봉인
결과와 같아야 한다. 각 범주의 작은 표본 수와 흡수 모형 가정은 그대로 보고한다.

## 공급한 축약과 비교

Active 전이를 $A$, terminal 도착을 $B$, active category 합산을 $O$라 둔다.
각 category 안의 source를 균등하게 또는 전체 out-weight에 비례해 분배하는 lifting을
$R$이라 하면 $OR=I$다. active 상태 $a$를 집단 구성 $ROa$와 잔차 $z=a-ROa$로 나눈다.
집단 관측은 $y=(Oa,b)$이며 $b$는 terminal category 확률이다. 내부 잔차는 실제 ID
부분집합이 아니라 부호 있는 within-category 구성 차이다. 이전 첫 경유의 nonassigned
집합과 혼동하지 않는다.

기억 없는 전달은 $M=\left(\begin{smallmatrix}OAR&0\\BR&I\end{smallmatrix}\right)$,
잔차 전달은 $D=(I-RO)A$, 잔차 유입은 $E=DR$, 잔차의 다음 관측은
$S=\left(\begin{smallmatrix}OA\\B\end{smallmatrix}\right)$다. $S$는 $OA$ 위에 $B$를
세로로 쌓은 $60\times N$ 행렬이고 $N$은 active raw source 수다.
정확한 소거식은

$$
y_{t+1}=My_t+SD^t z_0+\sum_{r=0}^{t-1}SD^{t-1-r}E\,y_{A,r}
$$

다. $y_A$는 active category 부분이며 $t=0$의 합은 비어 있다. 16 step까지의 재현에는
kernel $K_j=SD^jE$의 $j=0..14$와 초기항 $SD^t z_0$의 $t=0..15$가 필요하다.
전체 소거식은 같은 원형의 대수적 재구성이며 독립 예측 성과가 아니다.

두 lifting 각각에서 memoryless, 초기항만, 기억 lag 1/2/4/8/15와 초기항,
전체 lag 15에서 초기항 생략을 비교한다. 같은 lifting과 같은 probe 안에서 lag를 비교한다.
서로 다른 lifting은 $M,D,E,K$도 바꾸므로 기억 길이 효과와 합치지 않는다.
lifting과 일치하는 초기분포는 $z_0=0$이다. 반대 분포에서 정확한 초기항을 공급하는 것은
원래 관측이 숨겼던 초기 구성을 안다는 가정이며, 현재 집단 상태만으로 추론했다는 뜻이 아니다.

예측은 초기 관측 뒤 매 step 원형 관측을 다시 주입하지 않고 자체 과거 예측을 사용한다.
오차는 출력 60개에서 절반 L1 합으로 계산하며, 유한 lag의 부호 있는 출력이 확률 조건을
어기면 TV라 부르지 않는다. 음수·질량 오차를 clip/normalize로 고치지 않는다. 모든
step×probe 분포에서 음의 성분과 질량 오차를 기록한다. $D,E,K$는 경로 확률이 아니다.

## 구현과 진행 조건

[분석 소스](../verify/MaleCNS/observation_memory.py)와
[작은 그래프 검사](../tests/test_malecns_observation_memory.py)를 작성했다. 명시적인
작은 전체 행렬과 60출력의 일치, 완전 이력·초기항의 정확성, 실제 lumpable 음성대조,
음의 축약값을 보존하는 동작 등 관련 검사 6개가 0.69초에 통과했다. 전량 캐시 실행도
229.675841초에 완료했으며 60출력의 30범주 재합산과 이전 봉인 결과의 최대 오차는 0이었다.
모든 probe·step의 Fisher 계층 부등식도 위반이 없었다. 소스와 테스트는 완료 JSON이
해시를 기록하면 변경하지 않는다. 수치 비교 허용오차는 `5e-9`이며 epsilon·통계 기준이 아니다.
생리적 시간·부호·활동·가소성·ROI·연결 파라미터 미분은 아직 이 분석에 공급하지 않는다.

방법의 배경은 이산 전달 연산자의 투영 소거다. [Venturi와 Li의 2023년 원문](https://link.springer.com/article/10.1007/s40687-023-00390-2)은
Mori-Zwanzig 형식으로 이산 신경망의 관측 전달과 기억 연산자를 다룬다. 여기서는 해당
논문의 생물학적 해석을 가져오지 않고 유한 희소 행렬의 위 블록 소거를 직접 검산한다.
새로운 일반 투영 항등식을 발견했다는 주장이 아니라 실제 MaleCNS의 같은 전이에서
관측·lifting·lag 선택에 따른 차이를 계산하는 것이다.

## 완료 산출물과 실행

[완료 결과 JSON](../verify/MaleCNS/observation_memory_result.json)은 1,626,955 bytes,
SHA-256 `aca8e9d2cd5f0f3c0bb34e1fb7b98c2550b2e38e4a4e9e320ffaf99827938d62`다.
파생 NPZ는 `data/local/malecns-analysis/observation-memory-v1/observation_memory_arrays.npz`,
5,198,766 bytes, SHA-256
`0c21697b4f095cc43b8dcc0dbb1aa16feddff0b5e7f03a3f7768ba5ef8225b65`다.
source SHA는 `1a5cbd65556796d6990360ea1191512352088f39283aa6b57ae2d99eb0e6fa8a`,
test SHA는 `8bd2fcead510628a81a427d97580ba81f014b44ca89c483d1a650dfbe33d7f11`이다.
이 소스·테스트·결과·NPZ는 이후 수정하지 않는다. 입력 해시와 이전 실행 계보는 JSON에 보존했다.

실제 완료 명령은 다음과 같다. 원자료 재다운로드·이전 산출물 덮어쓰기는 없었고,
재실행하려면 별도 결과와 캐시 경로를 사용해야 한다.

```powershell
$env:CE_PYTHON='C:\Users\dongh\AppData\Local\uv\cache\archive-v0\Sp2cxzBGA63aECqn\Scripts\python.exe'
.codex/hooks/python.cmd python verify/MaleCNS/observation_memory.py --parent-result verify/MaleCNS/hidden_walk_information_result.json --cache-dir data/local/malecns-analysis/observation-memory-v1 --result verify/MaleCNS/observation_memory_result.json --max-working-gib 8
```

연산은 기존 SciPy 희소 행렬 곱을 사용했다. 새로운 고유해법이나 dense 전체 전이 행렬은
만들지 않았다. `working_bytes_estimate`는 큰 임시 배열을 포함하는 사전 산식이며 실제
peak RSS나 OS 강제 상한은 아니다. 결과의 forecast 시간은 kernel·초기항을 이미
계산한 뒤의 시간이다. raw graph를 쓰는 사전 계산 비용과 합치지 않고 별도로 읽는다.

## 60출력 관측 결과

27개 범주 모두의 미래 step 1..16에서 60출력 Fisher는 양수였으며 최소는
8.9877571e-6으로 수치 허용오차 5e-9보다 컸다. 따라서 현재 active/absorbed 상태를
구별해도 같은 초기 관측 뒤 미래가 갈라지는 결과가 남는다. 이는 한 모형의 내부 초기
구성 비교이고 독립 동물·활동 표본의 유의성 판정이 아니다.

| 시점 | `G60-G30 > tol` 범주 | `Gref-G60 > tol` 범주 | `G60/Gref` 최소 / 중앙 / 최대 | `G30/G60` 최소 / 중앙 / 최대 |
|---|---:|---:|---:|---:|
| step 1 | 26/27 | 27/27 | 0.01107049 / 0.12119142 / 0.87825732 | 0.55667379 / 0.96100036 / 1 |
| step 16 | 27/27 | 27/27 | 0.90817350 / 0.99800814 / 0.99999934 | 0.97377015 / 0.99758483 / 0.99999445 |

`G60/Gref`의 step-1 최소/최대는 `ol_intrinsic`/`sensory_ascending_tbc`,
step-16 최소/최대는 `cb_intrinsic`/`ENS`다. `G30/G60`의 step-1 최소/최대는
`ENS`/`visual_projection_tbc`, step-16 최소/최대는 `cb_intrinsic`/`ENS`다.
분모 0인 경우는 없었다. 비율은 해당 시점의 refined 정보에 대한 것으로, step 16에
초기 정보의 99.8%가 보존됐다는 뜻이 아니다. 전체 refined 정보 자체는 시간에 따라 줄어든다.
각 정보 차이는 중첩된 관측 사상의 차이지 물리적 전달량이나 인과 기여가 아니다.

## 이력 길이와 실패 경계

두 lifting과 각각 일치하는 27개 초기분포에서는 초기 잔차가 0이다. 이 조건으로 비교한
memoryless의 최대 오차는 두 lifting 모두 27/27 범주에서 허용오차보다 컸다. 각 step의
원형 관측을 다시 넣지 않은 예측이며, 아래 값은 모든 범주·0..16 step의 최대 half-L1이다.

| 보존 lag | 균등 lifting 최대 오차 | out-weight lifting 최대 오차 | 균등 / out-weight 음수 분포 수 |
|---|---:|---:|---:|
| 0 | 0.08947467022 | 0.07212336206 | 0 / 0 |
| 1 | 0.02924110053 | 0.02540646369 | 128 / 10 |
| 2 | 0.01059034104 | 0.01076301607 | 89 / 17 |
| 4 | 0.003478210245 | 0.002393806416 | 25 / 15 |
| 8 | 0.0004586403034 | 0.0004180260217 | 31 / 26 |
| 15 | 6.21195e-13 | 4.89015e-13 | 0 / 0 |

음수 분포 수는 matched 27개 probe의 미래 16 step, 총 432개 분포 중 최소 성분이
`-5e-9` 미만인 경우다. 개별 음수 성분 개수나 독립 표본 수가 아니다. 더 긴 lag가
항상 더 적은 음수 분포를 만들지도 않았다. 원래 확률 전이는 양수여도 부호 있는
투영 kernel을 잘라낸 자율 예측은 확률 모형이 아닐 수 있다.

그림의 중앙값은 각 범주에서 먼저 시간 최대 오차를 구하고, 그 27개 값을 동등 가중한
중앙값이다. 432개 step×probe를 한꺼번에 모은 중앙값이나 뉴런 수 가중 평균이 아니다.

| 보존 lag | 균등 lifting의 범주별 시간 최대 오차 중앙값 | out-weight lifting의 같은 중앙값 |
|---|---:|---:|
| 0 | 0.03148198520 | 0.03116364961 |
| 1 | 0.007859295096 | 0.008427723899 |
| 2 | 0.003472393634 | 0.003166504003 |
| 4 | 0.001145666486 | 0.000723179831 |
| 8 | 8.674620964e-5 | 7.424243101e-5 |
| 15 | 4.975479968e-14 | 1.028336367e-13 |

각 범주의 각 step을 따로 비교하면 오차 감소도 단조적이지 않았다. lag를 0→1→2→4→8로
늘리는 인접 비교 중 증가가 한 번 이상 있었던 범주는 균등 14개, out-weight 16개였다.
0→1, 1→2, 2→4, 4→8에서 증가한 step×probe 수는 각각 균등 `31,59,44,22`,
out-weight `18,43,50,58`이었다. 여러 비교에 같은 경우가 반복될 수 있다. 따라서 표의
전체 최대 감소를 모든 범주·시점에서 보장되는 단조 수렴이나 안정성 정리로 읽지 않는다.

균등 lag0/1 최대는 `ol_sensory`의 step 2/3, lag2/4/8 최대는 `cb_intrinsic`의
step 5/7/11이었다. out-weight lag0/1/2/4 최대는 `cb_sensory`의 step 2/3/5/7,
lag8 최대는 `cb_intrinsic`의 step 11이었다. lag15는 16 step까지 필요한 모든 항을
포함하므로 작은 오차는 대수 항등식의 검산이다. 보류된 미래나 새 입력에서 학습한 성공이 아니다.

## 초기 내부 구성의 별도 효과

초기분포를 lifting과 반대로 놓으면 초기 잔차를 안다는 조건과 동적 이력을 분리해야 한다.
아래는 각 lifting의 mismatched 27개 probe와 미래 16 step에서의 최대 half-L1이다.

| 모형 | 균등 lifting / out-weight 초기분포 | out-weight lifting / 균등 초기분포 |
|---|---:|---:|
| 초기항만, 동적 이력 없음 | 0.08947467022 | 0.07212336206 |
| 전체 동적 이력, 초기항 생략 | 0.22010939914 | 0.22010939914 |
| 전체 동적 이력과 초기항 | 4.8251e-13 | 7.8442e-13 |

초기항을 뺀 두 최대는 `cb_endocrine`의 step 1이다. 그 step에는 동적 이력 합이 아직
비어 있어, 아무리 긴 이후 이력 kernel을 보존해도 누락된 초기 구성 정보를 복구하지 못한다.
따라서 기억항만으로 임의 초기상태를 처리한다고 주장하지 않는다.

전체 54개 probe를 함께 센 invalid step×probe 분포는 초기항만/lag1/2/4/8/full에서
균등 `251/369/248/110/76/0`, out-weight `264/137/110/69/65/0`이었다. 질량 오차는
최대 약 1.6e-12였으므로 이 invalid 사례는 음의 성분 때문이다. 원자료나 수치를 고쳐
양수로 만든 결과가 아니며, 확률을 필요로 하는 후속 Fisher에는 이 signed 근사를 쓰지 않는다.

matched probe에서 최악의 음수는 두 lifting 모두 lag1의 `ENS` 초기조건, step3의
active `visual_projection` 출력이다. 값은 균등 -0.000191992454, out-weight -0.000169649387다.
mismatched에서는 초기항만 모형의 균등/ENS/step2/active ENS가 -0.022938918471,
out-weight/`sensory_ascending_tbc`/step2/active `ascending_neuron`이 -0.006947965909였다.
수치 허용오차보다 훨씬 큰 값이므로 단순 반올림으로 무시하지 않는다.

## 계산 비용과 해석 상한

사전 working estimate는 6,513,772,920 bytes였다. Python 3.11.15, NumPy 2.4.6,
SciPy 1.17.1에서 전체 실행은 229.675841초였다. 균등 lifting의 kernel/초기항 계산은
41.350949/32.017074초, out-weight는 33.414040/28.280202초였다. 저장한 여덟 예측 모형의
forecast 시간 합은 각각 0.005347/0.004333초다. 이는 한 번의 실행 경과이며 반복 성능
벤치마크나 보장 속도가 아니다. 매우 짧은 forecast 시간만으로 전체 알고리즘이 해당 시간에
학습·실행된다고 하지 않는다.

lag $L$에서 과거 active 관측 저장량은 probe당 $30L$개 스칼라다. 현재 60출력,
kernel 계수, 알려진 초기항과 전체 graph 사전 계산은 별도다. 같은 총 예산의 일반 축약과
비교하지 않았으므로 최소 기억 차원이나 최적 계산 표현은 아직 확인하지 않았다.
이 결과의 지위는 단일 정적 구조에 결박한 `BIO_EVIDENCE_L0` 대리모형 분석이다.

## 검수한 읽기본

[검수 notebook](../verify/MaleCNS/observation_memory_checked_companion.ipynb)과
[HTML](../verify/MaleCNS/observation_memory_checked_companion.html)은 완료 NPZ·JSON만 읽고
Fisher와 예측 오차를 다시 검산한다. nbformat 4.5의 9개 셀 중 코드 4개가 순서대로 실행돼
오류 0이었다. 내장 PNG 3개는 외부 파일과 bytes·SHA가 같고 HTML에도 같은 바이트가 있다.
세 그림의 범위·라벨·겹침을 직접 열어 검사했다. HTML 자체의 브라우저 시각 검사는
사용 가능한 브라우저가 없어 수행하지 못했다.

| 파일 (`verify/MaleCNS/` 기준) | bytes | SHA-256 |
|---|---:|---|
| `observation_memory_checked_companion.ipynb` | 838,096 | `87b223776045aad0c012fafb850bd1073db22270f33f7cbc8be444e485c17467` |
| `observation_memory_checked_companion.html` | 834,321 | `bb3b93b56bfc6ea731d9c4c21a3fde261c45b382378e187a40e20fc352aed080` |
| `figures/observation-memory-checked/boundary_information_partition.png` | 124,144 | `23dd9b2d1fb8c5e5ec766ba81461ee8f9e842fe49e163a8e5a63c0287e3e071c` |
| `figures/observation-memory-checked/memory_length_error.png` | 341,579 | `cea78772b5f26dc69f6fd02cf17ffb615c02e649d103849914d771b125cefdb2` |
| `figures/observation-memory-checked/initial_residual_comparison.png` | 147,836 | `a735be825e55d001821a8f7b25cff790d20e88e68bc603fc2aeb497ec62c8c32` |

[Builder](../verify/MaleCNS/build_observation_memory_notebook.py) 14,572 bytes의 SHA는
`144a9abbc74d2a04fc8cabdf590c370a88533078b392a4dfdb3455341d66a196`다.
Matplotlib 3.10.8, nbformat 5.11.1, nbclient 0.11.0, ipykernel 7.3.0을 사용했다.
최초 실행본 `observation_memory_companion.ipynb`의 SHA는
`1ecfd150fec953fd50a2465e3e6a9d2c40ccff854bec6c79373900d9f1c3876e`, HTML의 SHA는
`a42c81d9a7015c6b116d18084344e5972322273c95cf6b726bcf1e1a014de37a`다.
최초 그림의 symlog y축에서 0과 1e-9 눈금 글자가 겹쳐 현재 읽기본으로 쓰지 않는다.
이를 새 경로에서 명시적 눈금으로 교정했고 분석 수치·원본 읽기본은 보존했다. 다른 두 PNG는
처음과 해시가 같다. 교정본의 첫 kernel 시작은 `kernel_info` 전에 종료됐으나 출력 부재를
확인한 뒤 동일 승인 환경으로 한 번 재시도해 정상 완료했다. 정책 우회는 없었다.

## 다음 판별

60출력 대조와 정확한 이력 항등식, 유한 lag의 오차·음수 실패를 확인했다. 다음은 고정된
raw ID에서 연결 효능 파라미터를 별도로 바꿔 같은 확률 관측의 Jacobian·Fisher와 관측에
드러나지 않는 변화 방향을 검사하는 것이다. 현재 초기 구성 좌표를 연결 변화로 대신하지
않는다. signed 유한 이력식은 후속 likelihood로 채택하지 않고 검증된 전체 확률 전이를
사용한다. 확률을 보존하는 축약, 같은 총 예산의 일반 축약, 보류된 초기 입력과 대안 경계는
이력 압축을 채택하기 전의 별도 비교로 남는다. 생물학적 계량의 전체 목표는 미완료다.

## 작업 인계와 최종 검증

저장소는 `C:\dev\ce\ce-agi-runtime`, 브랜치 `main`, upstream `origin/main`이다.
확인한 HEAD와 로컬 remote-tracking tip은 모두
`27c2c02e5e168732b7d24356c5b39925716cd415`였다. 이번 단계에서 fetch·커밋·push는
하지 않았으므로 서버 원격의 최신 tip을 다시 확인한 것은 아니다.

추가한 파일은 `verify/MaleCNS/observation_memory.py`,
`tests/test_malecns_observation_memory.py`, 완료 JSON·NPZ·companion builder와 읽기본,
이 원장과 논문 8장이다. 데이터 원장·논문 목차·4장·7장·상위 읽기지도·PRD도 갱신했다.
원장 본체에는 새 분석 2개·검수 읽기본 5개·보존용 초기 읽기본 5개를 구별해 등록했다.
기존 `.claude/` 삭제·`AGENTS.md` 수정과 MICrONS radial 미완료 파일은 손대지 않았다.

검증 명령 `.codex/hooks/python.cmd pytest tests/test_malecns_observation_memory.py -q`는
6개 통과했다. 문서 반영 뒤 `.codex/hooks/python.cmd python .codex/hooks/repository_harness.py`는
`REPOSITORY_HARNESS_PASS`였다. 같은 harness의 `check_links`를 MaleCNS 원장 5개와
`data_registry.md`에 적용해 위반 0을 확인했고, 변경한 tracked 문서의 `git diff --check`도
통과했다. LF/CRLF 경고 때문에 파일을 일괄 변환하지는 않았다.
읽기 전용 독립 리뷰에서 수식·수치·분모·음수 위치·중앙값 정의의 중요 이슈는 없었고,
분석 소스·테스트·결과·NPZ·검수 읽기본·builder의 현재 해시도 원장과 일치했다.

전체 계산과 notebook 프로세스는 정상 종료했다. 브라우저 접근 도구의 현재 응답은
`No browser is available`이었으므로 HTML 브라우저 렌더링은 미검증이고, 실행 셀·내장
이미지·직접 연 PNG의 검수까지만 완료로 보고한다. 전체 pytest·생물학적 endpoint·배포
검사는 실행하지 않았다. 이번 분석을 완료했어도 전체 연구 목표를 완료로 판정하지 않는다.
