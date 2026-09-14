# MaleCNS 연결 효능 좌표와 관측 Fisher

문서 유형: 개발 분석 원장. 시작일: 2026-09-15. 현재 상태: 전량 계산·독립 검산·그림 검수 완료.
이전 [관측·이력 분석](malecns_observation_memory_findings.md)의 초기 혼합 좌표와 달리,
이번에는 raw ID·초기분포·관측을 고정하고 연결 효능 좌표를 바꾼다. 전체망에서 추론한
기하 패턴을 판별하는 다음 단계이며 생물학적 가소성 실험이나 사전등록이 아니다.
별도 데이터 보유·무결성 기록은 [데이터 원장](data_registry.md)에 둔다.

## 고정 입력과 좌표

`hidden-walk-v1` 전체 희소 전이와 `observation-memory-v1`의 봉인된 출력만 재사용한다.
모든 raw outgoing 접촉 311,833,243의 정규화, active source 1,834,661개, terminal category
흡수, self 접촉을 유지한다. 균등/out-weight 초기분포 54개는 기준 그래프에서 한 번 정하며
효능 변화 뒤 out-weight 초기분포를 다시 계산하지 않는다. 관측은 category 30개,
active/terminal category 60개, active ID/terminal category의 세 단계다.

공급하는 세 무차원 log-efficacy 좌표는 active target, 양 끝 assigned same superclass,
reciprocal nonself다. 첫째는 active 자기연결도 포함한다. 둘째는 같은 assigned category의
terminal 도착과 자기연결도 포함한다. 셋째는 원래 raw support에 역방향 연결이 있는
서로 다른 ID의 edge만 포함한다. 세 feature는 겹칠 수 있으며 ROI나 실제 가소성 채널이 아니다.
각 source와 terminal category를 고정하면 그 압축 셀 안의 underlying terminal ID들에서
세 feature가 일정하므로, 이번 관측과 미분에는 기존 terminal 집계가 정확하다.
세 좌표는 조건에 속한 연결들을 공유해서 바꾸는 방향이다. 151,856,684개 연결 각각을
독립 파라미터로 둔 전체 공간의 Fisher를 계산한 것은 아니다.

source $j$에서 target $i$로 가는 기준 확률을 $P_{ij}$, feature를 $f_{k,ij}$,
효능 좌표를 $\theta_k$라 하면

$$
P_{ij}(\theta)=\frac{P_{ij}\exp(\sum_k\theta_k f_{k,ij})}
{Z_j(\theta)},\qquad
Z_j(\theta)=\sum_iP_{ij}\exp(\sum_k\theta_k f_{k,ij})
$$

다. 분모는 매 $\theta$마다 active·terminal·self 전체에서 갱신한다. source의 모든
outgoing에 같은 배수를 곱하는 변화는 이 정규화에서 사라진다. 네 번째 좌표를 이 gauge의
음성 대조로 두되, 모든 생물학적 절대 효능이 관측 불가능하다는 뜻으로 확대하지 않는다.

## 미분과 검사 기준

active/terminal 전달을 $A,B$, feature를 곱한 행렬을 $F_k^A,F_k^B$라 둔다.
각 source의 feature 평균 $\mu_{k,j}$는 두 행렬의 해당 열합이다. 따라서
$\partial_k A=F_k^A-A\operatorname{diag}(\mu_k)$이며 $B$도 같다.
상태 $a_t,b_t$와 미분 $u_{k,t}=\partial_k a_t$, $v_{k,t}=\partial_k b_t$를 쓰면

$$
u_{k,t+1}=A(u_{k,t}-\mu_k\odot a_t)+F_k^A a_t,\qquad
v_{k,t+1}=v_{k,t}+B(u_{k,t}-\mu_k\odot a_t)+F_k^B a_t
$$

다. 초기 미분은 0이다. 고정 관측의 확률 $p$와 Jacobian $J=\partial_\theta p$로
$G=J^\top\operatorname{diag}(1/p)J$를 실제 양의 support에서 계산한다. $p=0$이면
미분도 0인지 검사한다. epsilon·ridge·SPD 강제·이전 signed 이력 축약은 사용하지 않는다.
같은 시점의 $G_{30}\preceq G_{60}\preceq G_{refined}$를 행렬 차이의 고유값으로 검사한다.
이번에는 전이 자체가 좌표에 의존하므로 시간에 따른 Fisher 감소를 요구하지 않는다.
각 시점의 endpoint 정보이며 joint trajectory 정보도 아니다.

수치 검사는 확률·미분 질량 오차 `5e-9`, scale-aware Loewner 최소 고유값 `-5e-9`다.
세 구조 좌표의 수치 rank는 `eigenvalue > 1e-10 * max(1, largest eigenvalue)`로 정의하며
gauge 영방향은 별도로 보존한다. 이 기준은 통계적 유의성이나 생물학적 rank가 아니다.
독립 비선형 재정규화의 central FD를 `h=1e-4, 5e-5`에서 모든 54개 초기분포·60출력·
0..16 step에 적용한다. 최대 절대오차 `1e-6` 이하와 각 성분의
`error / (1e-8 + 1e-4*abs(analytic)) <= 1`을 함께 요구한다. h 축소의 오차 변화를
그대로 보고하며 부동소수점 바닥이나 최대 위치 변경에서 4배 감소를 강요하지 않는다.

[분석 소스](../verify/MaleCNS/connection_fisher.py)와
[관련 검사](../tests/test_malecns_connection_fisher.py)는 작은 raw 전체 행렬의 직접 지수화,
terminal same-category, reciprocal nonself, 겹치는 feature와 source별 공통 배수,
support 영항과 구조적 비식별을 검사한다. 전체 분석 결과가 해시를 기록하면 변경하지 않는다.
방법의 일반적 배경은 [Ay 등, Information geometry and sufficient statistics](https://arxiv.org/abs/1207.6736)이며,
현재 희소 유한 모형의 미분·관측 손실은 직접 검산한다. 실제 활동·시간·전달 부호·ROI·
독립 동물 확인 없이 이 산출은 실측 구조 L1에 조건부인 `BIO_EVIDENCE_L0`다.

## 실행 상태

관련 테스트 7개는 승인된 기본 Python 3.11.9, NumPy 2.4.6, SciPy 1.17.1,
pytest 9.1.1에서 0.43초에 통과했다. 해시 계보 변조와 reciprocal 수지 불일치의 차단도
검사에 포함한다. 분석 환경 Python 3.11.15에는 pytest가 없으므로 테스트와 전량 분석의
실행기를 구분했다. 우회 설치는 하지 않았다. 전량 분석은 기존 승인된 Python 3.11.15,
NumPy 2.4.6, SciPy 1.17.1에서 1,181.653889초에 정상 완료했다. 해석적 궤적 계산은
327.936957초였다. 보수적 working-set 추정은 6,766,427,632 bytes이며 OS peak 측정이나
강제 RAM 상한은 아니다. 이전 60출력 재현 오차는 0, 연산자 미분 열합 오차는 3.783e-16,
확률 질량 최대 오차는 1.184e-12, 미분 질량 최대 오차는 9.514e-15였다.
scale-aware Loewner 차이의 최소 고유값은 -1.593e-17로 수치 허용오차 안이다.

스키마 명명 주의: 결과의 `feature_census[].terminal.directed_dyads`는 실제로
`B.nnz`, 즉 **비영 source × terminal-category 압축 셀 수**다. raw terminal ID dyad
수가 아니다. 같은 구조의 `active.directed_dyads`는 raw active-ID dyad 수가 맞으며,
양쪽 `contact_weight`는 원자료 접촉 가중치 합을 보존한다. 실행 중인 분석 소스를 바꾸지
않고 원 결과를 보존한다. 읽기본 summary는 `active_raw_id_dyads`와
`terminal_source_category_cells`로 뜻을 분리한다. 수치 연산의 오류가 아니라 필드명의
한계지만, 해당 raw terminal dyad 개수를 계산했다는 주장에 이 필드를 사용하지 않는다.

## 완료된 전량 수지와 독립 차분

| Feature | Active raw ID dyad | Active contact weight | Terminal 압축 셀 | Terminal contact weight |
|---|---:|---:|---:|---:|
| active target | 32,751,675 | 134,213,930 | 0 | 0 |
| same assigned superclass | 18,420,974 | 84,663,333 | 14,518 | 150,107 |
| reciprocal nonself | 8,871,458 | 52,619,911 | 0 | 0 |

행들은 겹치는 feature이므로 더해 전체 수로 해석하지 않는다. reciprocal의 원 ID 개수와
접촉 가중치 합은 봉인된 raw dyad 결과에서 읽은 값과 일치한다. ancestry 검사로
observation result → hidden result → dyad result의 실제 SHA를 연결했다.

| Feature | h | 최대 절대 FD 오차 | 최대 scaled 오차 |
|---|---:|---:|---:|
| active target | 1e-4 | 2.980803e-10 | 0.00482116 |
| active target | 5e-5 | 2.182945e-10 | 0.00970034 |
| same assigned superclass | 1e-4 | 1.871334e-10 | 0.00257494 |
| same assigned superclass | 5e-5 | 2.500766e-10 | 0.00473609 |
| reciprocal nonself | 1e-4 | 1.835413e-10 | 0.00635169 |
| reciprocal nonself | 5e-5 | 3.147450e-10 | 0.01836184 |

여섯 대조는 모두 사전 구현된 수치 기준을 통과했다. h를 절반으로 줄인 최대 절대오차는
4배씩 감소하지 않았다. 이전 오차/다음 오차 비는 각각 1.3655, 0.7483, 0.5831이며
최대 위치도 변했다. 오차가 약 1e-10 수준인 이 결과를 이상적인 절단오차 수렴 구간으로
주장하지 않는다. 독립 차분은 세 구조 좌표에 실행했고, 공통 배수 영방향은 정규화 정리와
작은 raw 행렬의 독립 공통 배수 검사로 검증했다. 네 번째 좌표의 전량 차분을 실행한 것은 아니다.

## 민감도와 식별의 음성 결과

60출력 대각 Fisher의 27개 범주 중앙값은 다음과 같다. 단위는 공급한 무차원 log-efficacy
한 단위 변화에 대한 정보이며, 실제 전류·전도도 단위가 아니다.

| Step | 고정 초기분포 | Active target | Same assigned superclass | Reciprocal nonself |
|---|---|---:|---:|---:|
| 1 | uniform | 0.219375691 | 0.045308960 | 0.029477519 |
| 1 | out-weight | 0.222075137 | 0.040606697 | 0.031559520 |
| 16 | uniform | 0.000659127 | 0.000198746 | 0.000132839 |
| 16 | out-weight | 0.000585374 | 0.000171667 | 0.000133456 |

Step 1의 same-superclass 최소값은 두 초기화 모두 0이다. 해당 범주는
`descending_neuron_tbc`, `sensory_ascending_tbc`, `visual_projection_tbc`다.
이 세 범주의 30/60/refined 관측과 두 초기화 모두 구조 3×3 rank가 2였고,
나머지 24개는 rank 3이었다. 총 18개의 rank 결손은 모두 이 첫 step에만 있었다.
영방향은 same-superclass 좌표 `(0,1,0)`이며 고유벡터 부호는 임의다. 한 셀의
최소 고유값 -5.48e-19와 타 성분 약 1e-16은 반올림 수준이다.

Step 2..16의 `15 × 54 × 3 = 2,430`개 probe·관측 셀은 모두 수치 rank 3이다.
각 구조 좌표에서 16개 미래 step 내내 60출력 미분이 `1e-10` 이하인 probe는 없었다.
이는 이 초기화·기간·세 공유 좌표 안의 결과이며 모든 가능한 초기분포나 개별 연결
파라미터의 식별을 보이지 않는다. 네 번째 source-common gauge는 항상 정확히 0이므로
전체 4×4 Fisher는 여전히 특이하다. 수치 rank를 생물학적 식별이나 통계적 유의성으로 세지 않는다.

## Rank 보존과 정보량 보존의 차이

같은 rank라도 잃는 정보량은 다르다. 아래 값은 각 probe에서 세 구조 좌표의
`trace(Gobserved)/trace(Grefined)`를 먼저 계산한 뒤 27개 범주에서 요약한 것이다.
Trace 비는 현재 좌표 정의에 의존하며 최악 방향의 정보 보존 하한이 아니다.

| Step·초기분포 | 30/refined 최소·중앙값·최대 | 60/refined 최소·중앙값·최대 |
|---|---|---|
| 1·uniform | 0.657166920 / 0.772544321 / 0.936860455 | 0.749180459 / 0.853099297 / 0.963709859 |
| 1·out-weight | 0.689286067 / 0.790253128 / 0.944659280 | 0.724554877 / 0.867630271 / 0.966803743 |
| 16·uniform | 0.523221962 / 0.810232247 / 0.975553136 | 0.973041251 / 0.983464703 / 0.996733887 |
| 16·out-weight | 0.523050674 / 0.791850053 / 0.976195412 | 0.971702513 / 0.981733893 / 0.995097209 |

Step 16의 30/refined 최소 범주는 두 초기화 모두 `descending_neuron`이다.
60/refined 최소는 uniform의 `ascending_neuron`, out-weight의 `vnc_intrinsic`이다.
초기 혼합 좌표를 다룬 이전 Fisher의 수치와 합산하거나 같은 물리량으로 비교하지 않는다.
여기서도 refined는 active ID/terminal category이며 모든 raw terminal ID 관측은 아니다.

## 산출물과 해시

| 파일 | Bytes | SHA-256 |
|---|---:|---|
| [분석 소스](../verify/MaleCNS/connection_fisher.py) | 19,076 | `13ab5df66b57526b38e0b3b1852ce937902d1fe9ee4f85575190eee02650f96d` |
| [검사](../tests/test_malecns_connection_fisher.py) | 6,983 | `5e33aa6799d4900611b9b3f886b37d625a27caa8caa590b15c8c818c6a10c400` |
| [완료 JSON](../verify/MaleCNS/connection_fisher_result.json) | 10,264 | `c0a2d62f56b32d8010ffa49b7e6309a4d7f77dfe874c59db9994dc7fc0990ff7` |
| `connection-fisher-v1/connection_fisher_arrays.npz` | 3,241,836 | `0775de822b424e752b62d281996ee02ed7d2dd2edb11aa7139c3380e5ce27206` |
| [읽기본 생성기](../verify/MaleCNS/build_connection_fisher_notebook.py) | 18,263 | `d09a019010749cc6ae87f35c125824ce9a29660a67aec41c6b44ab7e70c5b68e` |
| [실행 notebook](../verify/MaleCNS/connection_fisher_companion.ipynb) | 795,509 | `78bccc98d4bc30439ce44214fc921a6fea0d950cd32b582bf78a78f2b88a3c2d` |
| [HTML 읽기본](../verify/MaleCNS/connection_fisher_companion.html) | 793,137 | `a91f650e04468535b868647cf265fbf00c34a95a1af3ba1e4aaf06fd502ccdf1` |
| [검수 요약](../verify/MaleCNS/connection_fisher_summary.json) | 28,219 | `751dfc5b4a1f38926a5e578964efd2b53468e1681414ae78bbd56a7d5af42431` |

NPZ 위치의 기준은 `data/local/malecns-analysis/`다. source·test·result·NPZ와 읽기본
소스·산출물은 이후 수정하지 않는다. 읽기본의 코드 셀 4개는 순서대로 실행됐고 오류 0개,
nbformat 4.5 형식 검사와 30/60 Fisher의 독립 재계산을 통과했다. refined Fisher의
전체 active-ID Jacobian은 저장하지 않았으므로 읽기본에서 다시 계산한 것은 아니다.

| 검수 PNG | Bytes | SHA-256 |
|---|---:|---|
| `connection_coordinate_sensitivity.png` | 173,822 | `adde195966bc3268ee19f235130f84c13518e2e8b57eb39ab08a523fa8f1a1a4` |
| `observation_numerical_rank.png` | 148,602 | `d118f08f9f08f5d0298aff82e7c37854403460bee676265e3a04a292e2a88dd0` |
| `finite_difference_convergence.png` | 255,519 | `60b73137154ac36bb951aaaecd1160e99b524a73306bc934d4f1219c4586c9f1` |

그림 위치는 `verify/MaleCNS/figures/connection-fisher/`이며 세 PNG의 notebook·HTML
내장 바이트와 외부 파일이 일치했다. 주 에이전트가 실제 그림을 열어 범주·숫자·축·범례의
겹침과 잘림이 없음을 확인했다. HTML을 여는 브라우저는 `No browser is available`이므로
브라우저 레이아웃 검증은 미실행이다. 파일·이미지 검증을 브라우저 검증으로 부르지 않는다.
결과 JSON·NPZ 2개와 읽기본 6개를 데이터 원장에 각각 `connection-fisher-v1`,
`connection-fisher-companion-v1`로 등록했다. 해시 등록은 파일 무결성이지 생물학적 확인이 아니다.

## 재현과 다음 조건

검사는 기본 승인 Python 3.11.9, 분석·읽기본은 승인 Python 3.11.15 실행기를 `CE_PYTHON`으로
선택해 wrapper를 사용한다. 후자는 기존 uv cache의 `Sp2cxzBGA63aECqn/Scripts/python.exe`다.
읽기본은 기존 `ce-malecns-notebook-deps-20260914` 임시 의존성 경로를 `PYTHONPATH`에 둔다.

```powershell
$env:CE_PYTHON = 'C:\Users\dongh\AppData\Local\Programs\Python\Python311\python.exe'
.codex/hooks/python.cmd pytest tests/test_malecns_connection_fisher.py -q
$env:CE_PYTHON = 'C:\Users\dongh\AppData\Local\uv\cache\archive-v0\Sp2cxzBGA63aECqn\Scripts\python.exe'
.codex/hooks/python.cmd python verify/MaleCNS/connection_fisher.py --parent-result verify/MaleCNS/observation_memory_result.json --dyad-result verify/MaleCNS/dyad_return_result.json --cache-dir data/local/malecns-analysis/connection-fisher-v1 --result verify/MaleCNS/connection_fisher_result.json
$env:PYTHONPATH = 'C:\Users\dongh\AppData\Local\Temp\ce-malecns-notebook-deps-20260914'
.codex/hooks/python.cmd python verify/MaleCNS/build_connection_fisher_notebook.py
$env:CE_PYTHON = 'C:\Users\dongh\AppData\Local\Programs\Python\Python311\python.exe'
.codex/hooks/python.cmd python .codex/hooks/repository_harness.py
```

분석과 생성기는 기존 결과가 있으면 실패하도록 설계했다. 위 완료 경로를 덮어쓰거나
자동 재실행하지 않는다. 재검토는 질문과 이유를 남기고 새 경로·판본을 선택해야 한다.
다음은 같은 효능 좌표에서 끝점 정보와 이력의 결합 likelihood를 구별하는 계산이다.
시점별 endpoint Fisher의 단순 합을 경로 정보로 쓰지 않는다. 확률 보존·같은 총 예산의
일반 축약·새 입력·대안 경계, 실제 ROI·활동·시간 교정은 미완료다. 전체 연구 목표는 계속 열린다.

작업트리 인계: 저장소 `C:\dev\ce\ce-agi-runtime`, branch `main`, upstream `origin/main`,
HEAD와 로컬 remote-tracking tip은 `27c2c02e5e168732b7d24356c5b39925716cd415`다.
원격 fetch·커밋·push는 하지 않았다. 이번 단계의 추가물은 이 원장, 분석·검사·읽기본
생성기와 산출물, 논문 9장이며 논문 목차·연구계획·읽기지도·PRD·데이터 원장을 연결한다.
기존 `.claude/` 삭제, `AGENTS.md` 수정, MICrONS 미완료 파일과 앞선 MaleCNS 작업은 보존했다.
